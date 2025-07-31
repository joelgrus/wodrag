"""Simple, reliable workout text parser."""

import re


def parse_workout_simple(raw_text: str) -> dict[str, str | None]:
    """
    Simple parser that extracts workout and scaling sections.

    Returns:
        dict with 'workout' (always str) and 'scaling' (str or None) keys
    """
    lines = raw_text.split("\n")

    # Skip first two lines (date headers)
    if len(lines) < 3:
        return {"workout": raw_text.strip(), "scaling": None}

    content_lines = lines[2:]  # Skip date lines
    content = "\n".join(content_lines)

    # Find where scaling section starts
    scaling_patterns = [
        r"\bscaling:",
        r"\bbeginner option:",
        r"\bintermediate option:",
        r"\badvanced option:",
    ]

    scaling_start = None
    for pattern in scaling_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and (scaling_start is None or match.start() < scaling_start):
            scaling_start = match.start()

    # If scaling section exists, workout ends there, otherwise use full content
    workout_end = scaling_start if scaling_start is not None else len(content)

    # Extract sections
    workout = content[:workout_end].strip()

    scaling = None
    if scaling_start is not None:
        scaling = content[scaling_start:].strip()
        if not scaling:
            scaling = None

    return {"workout": workout or content.strip(), "scaling": scaling}


def clean_workout_text(workout_text: str) -> str:
    """Clean up workout text by removing common noise."""
    # Remove extra whitespace
    workout_text = re.sub(r"\n\s*\n", "\n", workout_text)
    workout_text = re.sub(r"[ \t]+", " ", workout_text)

    # Remove trailing periods that are just formatting
    workout_text = re.sub(r"\n\.\s*$", "", workout_text)

    return workout_text.strip()
