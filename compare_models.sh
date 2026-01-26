#!/bin/bash

###############################################################################
# Multi-Model Comparison Script
#
# This script runs the same scenario across multiple AI models and
# generates a comparison table.
#
# Usage:
#   chmod +x compare_models.sh
#   ./compare_models.sh
#
# Results will be saved in runs/ directory
###############################################################################

echo "=========================================="
echo "AI Medicare Evaluation - Model Comparison"
echo "=========================================="
echo ""

# Configuration
SCENARIO="scenarios/v1/scenario_002.json"
AGENT_MODEL="openrouter:anthropic/claude-3-haiku"  # Cheap and accurate
JUDGES=2

# Models to test (customize this list)
MODELS=(
  "openrouter:openai/gpt-4-turbo"
  "openrouter:openai/gpt-4o"
  "openrouter:anthropic/claude-3-5-sonnet"
  "openrouter:google/gemini-pro-1.5"
  "openrouter:meta-llama/llama-3.1-70b-instruct"
)

echo "Configuration:"
echo "  Scenario: $SCENARIO"
echo "  Agent Model: $AGENT_MODEL"
echo "  Judges: $JUDGES"
echo "  Models to test: ${#MODELS[@]}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
  echo "ERROR: .env file not found!"
  echo "Please create .env and add your OPENROUTER_API_KEY"
  echo "  cp .env.example .env"
  echo "  echo 'OPENROUTER_API_KEY=sk-or-your_key' >> .env"
  exit 1
fi

# Check if OPENROUTER_API_KEY is set
if ! grep -q "OPENROUTER_API_KEY" .env; then
  echo "ERROR: OPENROUTER_API_KEY not found in .env"
  echo "Please add your OpenRouter API key to .env"
  exit 1
fi

echo "Starting evaluations..."
echo "This will take approximately $((${#MODELS[@]} * 2)) minutes"
echo ""

# Run evaluation for each model
for MODEL in "${MODELS[@]}"; do
  echo "========================================="
  echo "Evaluating: $MODEL"
  echo "========================================="

  python -m src run \
    --scenario "$SCENARIO" \
    --target "$MODEL" \
    --agent-model "$AGENT_MODEL" \
    --judges "$JUDGES"

  if [ $? -eq 0 ]; then
    echo "✓ Completed: $MODEL"
  else
    echo "✗ Failed: $MODEL"
  fi

  echo ""

  # Small delay to avoid rate limits
  sleep 3
done

echo ""
echo "=========================================="
echo "All evaluations complete!"
echo "=========================================="
echo ""
echo "Generating comparison table..."
echo ""

# Generate comparison table
echo "MODEL COMPARISON - SHIP Question #3"
echo "===================================================================================================="
printf "%-45s %-10s %-28s %-12s %-12s\n" "Model" "Score" "Classification" "Completeness" "Accuracy"
echo "----------------------------------------------------------------------------------------------------"

for run in runs/*/results.jsonl; do
  # Extract data from JSON
  MODEL=$(cat "$run" | python -m json.tool 2>/dev/null | grep '"model_version"' | head -1 | cut -d'"' -f4)
  SCORE=$(cat "$run" | python -m json.tool 2>/dev/null | grep '"rubric_score"' | head -1 | awk '{print $2}' | tr -d ',')
  LABEL=$(cat "$run" | python -m json.tool 2>/dev/null | grep '"rubric_label"' | head -1 | cut -d'"' -f4)
  COMPLETE=$(cat "$run" | python -m json.tool 2>/dev/null | grep '"completeness_percentage"' | head -1 | awk '{print $2}' | tr -d ',')
  ACCURACY=$(cat "$run" | python -m json.tool 2>/dev/null | grep '"accuracy_percentage"' | head -1 | awk '{print $2}' | tr -d ',')

  # Skip if parsing failed
  if [ -z "$MODEL" ] || [ -z "$SCORE" ]; then
    continue
  fi

  # Convert to percentages
  if command -v bc &> /dev/null; then
    COMPLETE_PCT=$(echo "$COMPLETE * 100" | bc -l 2>/dev/null | xargs printf "%.1f%%" 2>/dev/null || echo "$COMPLETE")
    ACCURACY_PCT=$(echo "$ACCURACY * 100" | bc -l 2>/dev/null | xargs printf "%.1f%%" 2>/dev/null || echo "$ACCURACY")
  else
    COMPLETE_PCT="$COMPLETE"
    ACCURACY_PCT="$ACCURACY"
  fi

  printf "%-45s %-10s %-28s %-12s %-12s\n" "$MODEL" "$SCORE" "$LABEL" "$COMPLETE_PCT" "$ACCURACY_PCT"
done

echo "===================================================================================================="
echo ""
echo "SHIP Rubric:"
echo "  Score 1 = Accurate and Complete (100% facts covered)"
echo "  Score 2 = Substantive but Incomplete (partial coverage)"
echo "  Score 3 = Not Substantive (insufficient coverage)"
echo "  Score 4 = Incorrect (materially wrong information)"
echo ""
echo "Results saved in: runs/"
echo ""
echo "To view detailed results for a specific run:"
echo "  cat runs/TIMESTAMP/results.jsonl | python -m json.tool | less"
echo ""
echo "To view OpenRouter costs:"
echo "  open https://openrouter.ai/activity"
echo ""
