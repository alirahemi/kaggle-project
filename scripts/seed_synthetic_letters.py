#!/usr/bin/env python3
"""Copy synthetic sample letters into data/uploads for demos and tests."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FIXTURES = Path("tests/fixtures/sample_letters")
DEFAULT_DEST = Path("data/uploads/synthetic")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic German letters")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    if not FIXTURES.exists():
        raise SystemExit(f"Fixtures directory missing: {FIXTURES}")

    letters = sorted(p for p in FIXTURES.glob("*.txt"))
    if args.list_only:
        for letter in letters:
            print(letter.name)
        return

    args.dest.mkdir(parents=True, exist_ok=True)
    for letter in letters:
        target = args.dest / letter.name
        shutil.copy2(letter, target)
        print(f"Copied {letter.name} -> {target}")

    print(f"Seeded {len(letters)} letters to {args.dest}")


if __name__ == "__main__":
    main()
