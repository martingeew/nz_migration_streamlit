"""
Observable Framework data loader — emits the migration payload to stdout.

Framework runs this at build time and caches the result as
src/.observablehq/cache/data/migration.json, which the page then reads via
FileAttachment. Reuses build_payload() from the shared export so all three
prototypes are guaranteed identical numbers.

Note: nothing may be printed to stdout except the JSON, hence quiet=True.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROTOTYPES_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROTOTYPES_DIR))

from export_prototype_data import build_payload  # noqa: E402


def main() -> None:
    json.dump(build_payload(quiet=True), sys.stdout)


if __name__ == "__main__":
    main()
