"""Check an Assignment's instructions before filing it.

Usage: python check_assignment.py [--lead-minutes N] "<instructions>"

Prints OK, or one line per problem, and exits 1 when there is a problem.
Standard library only, no network, no file writes.
"""

from __future__ import annotations

import argparse
import re
import sys

MAX_CHARS = 8000
LEAD_MIN, LEAD_MAX = 5, 1440

# Words Kutana never uses in product copy. An Assignment's instructions are shown
# to the person on the meeting card, so they count as product copy.
NEVER_SAY = re.compile(
    r"(?<![a-z])(previews?|sandbox(?:es)?|demos?|feeds?|free|meeting prep)(?![a-z])",
    re.IGNORECASE,
)


def problems(text: str, lead_minutes: int | None) -> list[str]:
    found: list[str] = []
    if not text.strip():
        found.append("instructions are empty")
    if len(text) > MAX_CHARS:
        found.append(f"instructions are {len(text)} characters; the limit is {MAX_CHARS}")
    if lead_minutes is not None and not LEAD_MIN <= lead_minutes <= LEAD_MAX:
        found.append(f"lead time {lead_minutes} is outside {LEAD_MIN} to {LEAD_MAX} minutes")
    for match in NEVER_SAY.finditer(text):
        found.append(f"'{match.group(0)}' is a word Kutana does not use; rephrase it")
    if "\u2014" in text:
        found.append("replace the em dash with a colon or a new sentence")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("instructions")
    parser.add_argument("--lead-minutes", type=int, default=None)
    args = parser.parse_args()
    found = problems(args.instructions, args.lead_minutes)
    print("OK" if not found else "\n".join(found))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
