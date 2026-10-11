from __future__ import annotations

import argparse
import json
from pathlib import Path

from product_research.config import load_config
from product_research.engine import ResearchEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="Run automated product research")
    parser.add_argument("--csv", type=Path, default=None, help="Optional Amazon data CSV import")
    args = parser.parse_args()
    result = ResearchEngine(load_config()).run(args.csv)
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

