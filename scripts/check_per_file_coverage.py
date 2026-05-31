#!/usr/bin/env python3
"""Fail if any source file falls below a per-file coverage floor.

``coverage.py`` enforces only a single project-wide ``--cov-fail-under``. This
script reads the coverage XML report and additionally requires every measured
file to meet a minimum line-coverage percentage, so a well-covered overall
number can't hide an untested module.

Usage::

    # after a coverage run that wrote coverage.xml
    uv run python scripts/check_per_file_coverage.py --min 80

Exits 0 if every file meets the floor, 1 otherwise (printing the offenders).
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_DEFAULT_MIN = 80.0
_DEFAULT_XML = Path("coverage.xml")


def _file_rates(xml_path: Path) -> dict[str, float]:
    """Return per-file line-coverage percentages from a coverage XML report.

    Args:
        xml_path: Path to the Cobertura-style ``coverage.xml``.

    Returns:
        A mapping of filename to its line-rate as a percentage.
    """
    tree = ET.parse(xml_path)  # noqa: S314 - trusted local coverage output
    root = tree.getroot()
    rates: dict[str, float] = {}
    for cls in root.iter("class"):
        filename = cls.get("filename")
        line_rate = cls.get("line-rate")
        if filename is None or line_rate is None:
            continue
        rates[filename] = float(line_rate) * 100.0
    return rates


def main(argv: list[str] | None = None) -> int:
    """Check per-file coverage against the floor.

    Args:
        argv: Optional argument list (defaults to ``sys.argv``).

    Returns:
        Process exit code: 0 on success, 1 when any file is below the floor.
    """
    parser = argparse.ArgumentParser(description="Per-file coverage floor check.")
    parser.add_argument("--min", type=float, default=_DEFAULT_MIN)
    parser.add_argument("--xml", type=Path, default=_DEFAULT_XML)
    args = parser.parse_args(argv)

    if not args.xml.exists():
        print(f"coverage XML not found: {args.xml}", file=sys.stderr)
        return 1

    rates = _file_rates(args.xml)
    offenders = sorted(
        (name, rate) for name, rate in rates.items() if rate < args.min
    )
    if offenders:
        print(f"Files below {args.min:.0f}% line coverage:", file=sys.stderr)
        for name, rate in offenders:
            print(f"  {rate:6.2f}%  {name}", file=sys.stderr)
        return 1

    print(f"All {len(rates)} files meet the {args.min:.0f}% coverage floor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
