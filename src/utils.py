"""Utility functions for the AI Medicare Evaluation Harness"""

import json
import re


def extract_json_from_text(text: str) -> dict:
    """
    Extract JSON object or array from text that may contain preamble or postamble.

    This is needed because LLMs often add explanatory text before/after JSON:
    "Here are the results:\n{...}\n\nLet me know if you need anything else."

    Args:
        text: Raw text that may contain JSON

    Returns:
        Parsed JSON object or array

    Raises:
        ValueError: If no valid JSON found
    """
    # First, try direct parsing (fastest path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON object or array using regex
    # Look for outermost { } or [ ]
    patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # Match nested objects
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]',  # Match nested arrays
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)

        # Try each match, starting with the longest (most likely to be complete)
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    # If regex fails, try to find JSON between common delimiters
    json_start = text.find('{')
    json_array_start = text.find('[')

    # Use whichever comes first
    if json_start == -1 and json_array_start == -1:
        raise ValueError(f"No JSON object or array found in text: {text[:200]}...")

    if json_start != -1 and (json_array_start == -1 or json_start < json_array_start):
        # Try to find matching closing brace
        brace_count = 0
        json_end = -1
        for i, char in enumerate(text[json_start:], start=json_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break

        if json_end != -1:
            try:
                return json.loads(text[json_start:json_end])
            except json.JSONDecodeError:
                pass

    if json_array_start != -1:
        # Try to find matching closing bracket
        bracket_count = 0
        json_end = -1
        for i, char in enumerate(text[json_array_start:], start=json_array_start):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    json_end = i + 1
                    break

        if json_end != -1:
            try:
                return json.loads(text[json_array_start:json_end])
            except json.JSONDecodeError:
                pass

    # Last resort: show what we found
    raise ValueError(
        f"Failed to parse JSON from text. "
        f"Text starts with: {text[:200]}... "
        f"Text ends with: ...{text[-200:]}"
    )
