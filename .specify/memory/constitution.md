<!--
Sync Impact Report:
- Version change: [initial] → 1.0.0
- Initial constitution ratification
- Principles derived from README.md Key Design Principles section
- Templates: No updates required (initial baseline)
- Follow-up TODOs: None
-->

# AI Medicare Evaluation Harness Constitution

## Core Principles

### I. Primary goals

The goal of this project is to assess how well different AI tools answer questions about Medicare. The whole exercise is an extension of and grounded in the study "Accuracy of Medicare Information Provided by State Health Insurance Assistance Programs" located at https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/. 

The goal is to understand how well the AI tools will respond to Medicare questions in real world usage of AI tools. We will strive to reproduce real world usage of AI and will call out any cases where this is different. For example by calling AI tools by API we may get different responses than more typical approaches (e.g. OpenAI API vs ChatGPT.com) which might have different system prompts, tool usage and context.

Always align with the methodology used in that study. 
Always reference and link to the study when describing this project and when sharing values from the study.

### I. Strict Role Separation (NON-NEGOTIABLE)

Questioner ≠ Responder ≠ Judge. The system MUST maintain complete separation between:
- **Questioner agent**: Generates beneficiary questions from scenarios
- **Target model**: The AI system being evaluated (responder)
- **Judge agents**: Extractor, Verifier (multiple independent instances), Scorer, and Adjudicator

**Rationale**: Prevents bias and contamination. A model cannot evaluate its own outputs. Independent judges ensure objective assessment. This mirrors the SHIP mystery-shopper methodology where counselors don't evaluate themselves.

**Rules**:
- No agent may access another agent's internal state or reasoning
- Target model receives only user questions, never judge feedback
- Judge agents receive only answer keys and target responses
- Cross-contamination between roles invalidates the evaluation

### II. Answer-Key Grounded Evaluation

ALL evaluations MUST be grounded in explicit, pre-defined answer keys. Judges rely ONLY on provided canonical facts.

**Rationale**: Ensures reproducible, objective evaluation. Prevents subjective judgment or hallucinated standards. Answer keys are derived from authoritative Medicare sources and SHIP study methodology.

**Rules**:
- Every scenario MUST have a complete answer key with canonical facts
- Each canonical fact MUST include: fact_id, statement, rationale, source, severity_if_wrong
- Judges may NOT use external knowledge or internet searches
- Judges may NOT invent or infer facts not in the answer key
- Claims not covered by answer key are marked "NOT_IN_KEY", not evaluated as correct/incorrect

### III. Deterministic by Default

The system MUST produce reproducible results. All randomness MUST be controlled.

**Rationale**: Scientific reproducibility requires controlled experiments. Model drift detection requires identical conditions. Enables audit and replication of findings.

**Rules**:
- Fixed random seeds for all models (default: 0)
- Fixed temperature for target models (default: 0.0)
- Prompt templates are versioned and immutable during evaluation runs
- Agent model versions are locked and recorded
- Scenario files are versioned with effective dates
- Any parameter changes MUST be documented and version-bumped

### IV. Full Auditability

ALL evaluation artifacts MUST be stored verbatim in immutable, timestamped records.

**Rationale**: Research credibility requires complete paper trail. Debugging requires full context. Regulatory scrutiny demands evidence.

**Rules**:
- Store complete conversation transcripts with target model
- Store all judge outputs (claims, verdicts, scores) without summarization
- Record all model metadata: version, parameters, token usage, latency
- Save raw JSON artifacts to `runs/` directory (one per evaluation)
- Never modify past run artifacts - regenerate with new timestamp instead
- Include scenario_id, target model, agent models, timestamp in every artifact

### V. Snapshot-Based Evaluation

Results are time-, model-, and prompt-specific. Comparisons MUST account for temporal and configurational context.

**Rationale**: Models change over time (drift). Prompts affect outcomes. Fair comparison requires identical conditions or explicit acknowledgment of differences.

**Rules**:
- Every result includes timestamp and model version
- Comparison reports MUST note any differences in: model versions, prompt versions, scenario versions, evaluation dates
- Longitudinal studies MUST use frozen model versions or document version changes
- Scenario files include `effective_date` field to mark temporal validity
- Reports clearly distinguish: same-model-over-time vs. cross-model comparisons

## Research Ethics

This system is for research purposes ONLY. It evaluates AI-generated information quality but does NOT:
- Provide medical, legal, or insurance advice
- Replace professional Medicare counseling
- Recommend specific health coverage decisions
- Serve as a decision-support tool for beneficiaries

**Rules**:
- All documentation MUST include ethics disclaimer
- Results MUST NOT be framed as endorsements or recommendations
- System purpose is comparative evaluation, not beneficiary guidance
- Any publication or derivative work MUST cite SHIP study methodology and acknowledge limitations

## Development Workflow

### Test Coverage

- Unit tests required for: adapters, agents, utilities, schemas
- Integration tests required for: full evaluation pipeline, multi-agent coordination
- Scenario validation tests required for: answer key completeness, fact consistency
- Use fake adapters (`fake:perfect`, `fake:incorrect`) for testing without API costs

### Documentation Standards

- Every new scenario MUST include: SCENARIOS.md entry, answer key documentation, expected rubric distribution
- Every new adapter MUST include: ADAPTERS_COMPLETE.md entry, usage example, error handling docs
- Breaking changes MUST include: migration guide, deprecation timeline, backward compatibility notes
- Configuration changes MUST update: USER_GUIDE.md, QUICK_REFERENCE.md, relevant examples

### Code Review Requirements

- Verify role separation is maintained
- Confirm deterministic seeds/parameters used
- Check answer key completeness for new scenarios
- Validate audit artifacts are complete
- Ensure ethical disclaimers present in user-facing docs

## Governance

This constitution supersedes all other development practices. When conflicts arise between this document and other guidance, this constitution takes precedence.

**Amendment Process**:
- Amendments MUST increment constitution version (semantic versioning)
- Breaking changes (MAJOR): Principle removals, redefinitions incompatible with prior version
- New principles (MINOR): Additions that don't invalidate prior work
- Clarifications (PATCH): Wording improvements, examples, non-semantic fixes
- Amendments MUST update Sync Impact Report at top of this file
- Amendments MUST propagate to affected templates and docs

**Compliance**:
- All PRs MUST verify constitution compliance in review
- Violations MUST be justified and documented as technical debt
- Repeat violations indicate constitution needs amendment or enforcement improvement

**Version**: 1.0.0 | **Ratified**: 2026-01-29 | **Last Amended**: 2026-01-29
