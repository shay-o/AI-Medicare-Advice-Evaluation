# Documentation Index

**Complete guide to available documentation for the AI Medicare Evaluation Harness**

---

## For First-Time Users

**Start here if you're new to the project:**

1. **[README.md](README.md)** - Project overview and quick start (5 min read)
2. **[USER_GUIDE.md](USER_GUIDE.md)** - Step-by-step usage guide (15 min read)
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command reference card (2 min read)
4. **[SCENARIOS.md](SCENARIOS.md)** - Test scenarios explained (10 min read)

**Recommended path:**
1. Read README.md to understand the project
2. Follow USER_GUIDE.md Quick Start section
3. Run first evaluation with fake adapter
4. Read SCENARIOS.md to choose appropriate test
5. Keep QUICK_REFERENCE.md open while working

---

## For Researchers & Evaluators

### Running Evaluations

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete instructions for:
  - Running single evaluations
  - Comparing multiple models
  - Interpreting SHIP rubric scores
  - Managing costs
  - Troubleshooting

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast command lookup:
  - Common commands
  - Model names
  - Score interpretation
  - Viewing results

- **[REPORTING_GUIDE.md](REPORTING_GUIDE.md)** - Generate accuracy reports:
  - SHIP-style accuracy tables
  - Group by scenario or model
  - Compare to SHIP study results
  - Export options

### Understanding Tests

- **[SCENARIOS.md](SCENARIOS.md)** - Detailed scenario documentation:
  - What each scenario tests
  - All 14 canonical facts explained
  - SHIP rubric interpretation
  - Which scenario to use when
  - How to create new scenarios

- **[SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md)** - SHIP scoring methodology:
  - How the 4-tier rubric works
  - Score 1-4 definitions
  - Example results with explanations
  - Technical implementation details

### Model Access

- **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)** - Using OpenRouter (recommended):
  - Why use OpenRouter
  - How to set up API key
  - Available models (100+)
  - Cost comparison
  - When to use direct vs OpenRouter

### Methodology

- **[METHODOLOGY_COMPARISON.md](METHODOLOGY_COMPARISON.md)** - System vs SHIP study:
  - What matches the original study
  - What's different
  - Implementation gaps
  - Future enhancements

---

## For Developers

### Architecture & Implementation

- **[AGENTS_COMPLETE.md](AGENTS_COMPLETE.md)** - Agent system design:
  - 5 specialized agents explained
  - Role separation
  - Data flow between agents
  - Prompt design

- **[ORCHESTRATOR_COMPLETE.md](ORCHESTRATOR_COMPLETE.md)** - Pipeline architecture:
  - 6-stage evaluation pipeline
  - CLI interface
  - Storage system
  - Configuration options

- **[ADAPTERS_COMPLETE.md](ADAPTERS_COMPLETE.md)** - LLM adapter system:
  - Adapter interface
  - 7 implemented adapters
  - How to add new providers
  - Rate limiting and retries

### Project Status

- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Development roadmap:
  - Completed features
  - Remaining work
  - Future enhancements
  - Known limitations

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete implementation summary:
  - What was built (3,586 lines)
  - Architecture overview
  - Key achievements
  - Usage examples

### Technical Details

- **[JSON_PARSING_FIX.md](JSON_PARSING_FIX.md)** - LLM JSON parsing solution:
  - Problem description
  - Implementation fix
  - Before/after comparison
  - How it works

---

## Quick Start by Role

### Researcher: "I want to evaluate AI models on Medicare questions"

1. Read: [USER_GUIDE.md](USER_GUIDE.md) Quick Start section
2. Read: [SCENARIOS.md](SCENARIOS.md) - Choose scenario_002
3. Set up: [OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md) - Get API key
4. Run: Follow examples in [USER_GUIDE.md](USER_GUIDE.md)
5. Analyze: [REPORTING_GUIDE.md](REPORTING_GUIDE.md) - Generate accuracy tables
6. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands

### Developer: "I want to understand how this works"

1. Read: [README.md](README.md) - Architecture overview
2. Read: [AGENTS_COMPLETE.md](AGENTS_COMPLETE.md) - Agent design
3. Read: [ORCHESTRATOR_COMPLETE.md](ORCHESTRATOR_COMPLETE.md) - Pipeline
4. Read: [ADAPTERS_COMPLETE.md](ADAPTERS_COMPLETE.md) - LLM integration
5. Reference: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for gaps

### Methodology Expert: "I want to compare this to [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)"

1. Read: [SCENARIOS.md](SCENARIOS.md) - scenario_002 section
2. Read: [SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md) - Scoring details
3. Read: [METHODOLOGY_COMPARISON.md](METHODOLOGY_COMPARISON.md) - Full comparison
4. Review: `reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`
5. Full study: [PMC11962663](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)

---

## Documentation Size Guide

| Document | Length | Read Time | Audience |
|----------|--------|-----------|----------|
| README.md | 2 pages | 5 min | Everyone |
| QUICK_REFERENCE.md | 3 pages | 2 min | Users |
| USER_GUIDE.md | 15 pages | 15 min | Users |
| SCENARIOS.md | 12 pages | 10 min | Users/Researchers |
| OPENROUTER_GUIDE.md | 10 pages | 8 min | Users |
| SHIP_RUBRIC_UPDATE.md | 8 pages | 7 min | Researchers |
| METHODOLOGY_COMPARISON.md | 20 pages | 20 min | Researchers |
| AGENTS_COMPLETE.md | 25 pages | 25 min | Developers |
| ORCHESTRATOR_COMPLETE.md | 20 pages | 20 min | Developers |
| ADAPTERS_COMPLETE.md | 25 pages | 25 min | Developers |

---

## Practical Tools

### Scripts

- **`compare_models.sh`** - Automated multi-model comparison
  - Edit the `MODELS` array to choose which models to test
  - Generates comparison table automatically
  - Usage: `./compare_models.sh`

### Example Files

- **`scenarios/v1/scenario_001.json`** - Synthetic scenario example
- **`scenarios/v1/scenario_002.json`** - SHIP-aligned scenario example
- **`.env.example`** - Template for API keys

### Reference Material

- **`reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`**
  - Original SHIP study appendices
  - Mystery-shopper scripts
  - Scoring guides

---

## Frequently Asked Questions

### "Where do I start?"
Read [USER_GUIDE.md](USER_GUIDE.md) Quick Start section (5 minutes).

### "Which scenario should I use?"
Use **scenario_002.json** - it's SHIP study aligned. See [SCENARIOS.md](SCENARIOS.md).

### "How do I test multiple models?"
Run `./compare_models.sh` or follow examples in [USER_GUIDE.md](USER_GUIDE.md) Multi-Model Comparisons section.

### "How do I interpret the scores?"
See [SCENARIOS.md](SCENARIOS.md) "Interpreting Results" section or [SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md).

### "What is OpenRouter?"
See [OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md) - it's a unified API for 100+ models.

### "How much does this cost?"
See [USER_GUIDE.md](USER_GUIDE.md) Cost Management section (~$0.09 per evaluation).

### "How does this compare to the SHIP study?"
See [METHODOLOGY_COMPARISON.md](METHODOLOGY_COMPARISON.md) for detailed comparison, or read the [original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/).

### "Can I add new scenarios?"
Yes! See [SCENARIOS.md](SCENARIOS.md) "Creating New Scenarios" section.

---

## Getting Help

1. **Check documentation** - Most questions answered in guides above
2. **Review examples** - All guides include working examples
3. **Check existing runs** - Look at `runs/` directory for sample outputs
4. **Test with fake adapter** - Verify system works before using real APIs

---

## Updates & Changelog

### January 26, 2026
- ✅ Added USER_GUIDE.md - comprehensive usage guide
- ✅ Added SCENARIOS.md - detailed scenario documentation
- ✅ Added QUICK_REFERENCE.md - command reference card
- ✅ Added compare_models.sh - automated comparison script
- ✅ Updated README.md - better first-time user experience
- ✅ Added DOCUMENTATION_INDEX.md - this file

### January 25, 2026
- ✅ Implemented SHIP study rubric (Score 1-4)
- ✅ Fixed JSON parsing for real LLM agents
- ✅ Added scenario_002.json (SHIP Question #3)
- ✅ Created SHIP_RUBRIC_UPDATE.md

---

**Tip:** Bookmark [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for fast command lookup while working!
