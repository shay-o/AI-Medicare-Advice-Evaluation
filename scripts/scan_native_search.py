"""Which models actually support provider-hosted (native) web search on OpenRouter?

Docs list which providers offer native search; this establishes it per model
empirically, because the roster has to be built from what works today.

For each model, three probes on a question that cannot be answered from
training data alone (a specific MA plan's drug coverage):

  1. plain        - no search. Baseline cost.
  2. native       - plugins engine="native". Does the provider host it?
  3. searched?    - did it actually search, judged by cost delta and citations.

Reports availability, whether citations are traceable URLs or opaque redirects,
and cost. A model can accept the native plugin and still decline to search,
which is a behaviour worth seeing rather than a failure.
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

ROOT = "/Users/jamesoreilly/Documents/Projects/AI-Medicare-Advice-Evaluator"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
load_dotenv(".env")

import httpx  # noqa: E402

KEY = os.environ["OPENROUTER_API_KEY"]
Q = "Does the Aetna Medicare Eagle PPO plan include prescription drug coverage?"

# the 9 originally evaluated, plus current candidates
CANDIDATES = [
    "openai/gpt-5.2",
    "openai/gpt-5.2-chat",
    "openai/gpt-5.2-pro",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-opus-4.1",
    "google/gemini-3-flash-preview",
    "google/gemini-3-pro-preview",
    "x-ai/grok-4",
    "x-ai/grok-4.1-fast",
    "perplexity/sonar-pro",
]


async def call(client, model, plugins):
    body = {"model": model, "messages": [{"role": "user", "content": Q}],
            "max_tokens": 300, "temperature": 0}
    if plugins:
        body["plugins"] = plugins
    try:
        r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                              headers={"Authorization": f"Bearer {KEY}"},
                              json=body, timeout=240)
    except Exception as e:
        return {"err": f"request failed: {type(e).__name__}"}
    if r.status_code != 200:
        try:
            msg = r.json().get("error", {}).get("message", r.text[:120])
        except Exception:
            msg = r.text[:120]
        return {"err": f"HTTP {r.status_code}: {msg[:110]}"}
    d = r.json()
    msg = d["choices"][0]["message"]
    ann = msg.get("annotations") or []
    cites = [a.get("url_citation", {}).get("url") for a in ann
             if isinstance(a, dict) and a.get("type") == "url_citation"]
    return {"cost": (d.get("usage") or {}).get("cost"),
            "cites": [c for c in cites if c],
            "text": (msg.get("content") or "")[:60]}


async def probe(client, model, sem):
    async with sem:
        plain = await call(client, model, None)
        native = await call(client, model, [{"id": "web", "engine": "native", "max_results": 5}])
        return model, plain, native


async def main():
    sem = asyncio.Semaphore(3)
    async with httpx.AsyncClient() as c:
        results = await asyncio.gather(*(probe(c, m, sem) for m in CANDIDATES))

    print(f"{'model':34}{'plain':>10}{'native':>26}{'cites':>7}  notes")
    print("-" * 108)
    summary = {}
    for model, plain, native in results:
        if "err" in plain and "err" in native:
            print(f"{model:34}{'--':>10}{'--':>26}{'--':>7}  UNAVAILABLE: {plain['err'][:44]}")
            summary[model] = {"available": False, "native_search": False, "note": plain["err"]}
            continue
        pc = plain.get("cost")
        pcs = f"${pc:.5f}" if isinstance(pc, (int, float)) else "err"
        if "err" in native:
            note = "no native search: " + native["err"][:52]
            print(f"{model:34}{pcs:>10}{'unsupported':>26}{'0':>7}  {note}")
            summary[model] = {"available": True, "native_search": False, "note": native["err"][:120]}
            continue
        nc = native.get("cost")
        ncs = f"${nc:.5f}" if isinstance(nc, (int, float)) else "err"
        n_cites = len(native.get("cites", []))
        searched = isinstance(nc, (int, float)) and isinstance(pc, (int, float)) and nc > pc * 3
        opaque = any("grounding-api-redirect" in u or "vertexaisearch" in u
                     for u in native.get("cites", []))
        notes = []
        notes.append("searched" if searched or n_cites else "accepted but did not search")
        if n_cites and opaque:
            notes.append("citations are opaque redirects")
        elif n_cites:
            notes.append("citations are real URLs")
        print(f"{model:34}{pcs:>10}{ncs:>26}{n_cites:>7}  {', '.join(notes)}")
        summary[model] = {"available": True, "native_search": True, "searched": bool(searched or n_cites),
                          "citations": n_cites, "opaque_citations": opaque,
                          "cost_plain": pc, "cost_native": nc}

    out = "reference_material/native_search_capability.json"
    json.dump({"probed_question": Q, "results": summary}, open(out, "w"), indent=1)
    print(f"\nwritten to {out}")

    usable = [m for m, v in summary.items() if v.get("native_search") and v.get("searched")]
    print(f"\nusable for the search tier ({len(usable)}): {usable}")


asyncio.run(main())
