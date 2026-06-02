#!/usr/bin/env python3
"""Validate content files against the contract (see CONTENT_CONTRACT.md).

Usage:
    python validate_content.py [amc_data.json] [diag_data.json]

Defaults to the two files in the same directory. Exits 0 if both pass,
1 otherwise, printing every problem found. This is the gate the seed
script should run before assembly; if it passes, the data drops into
the prototype without app changes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CONTESTS = {"AMC 8", "AMC 10", "AMC 12"}
DATA_URI = re.compile(r"^data:")
EXT_IMG = re.compile(r'<img[^>]+src="(?!data:)', re.IGNORECASE)


class Report:
    """Accumulates validation errors and warnings."""

    def __init__(self) -> None:
        """Initialise with empty error and warning lists."""
        self.errs: list[str] = []
        self.warns: list[str] = []

    def err(self, m: str) -> None:
        """Append an error message."""
        self.errs.append(m)

    def warn(self, m: str) -> None:
        """Append a warning message."""
        self.warns.append(m)


def validate_amc(d: dict[str, Any], r: Report) -> None:  # noqa: C901
    """Validate the top-level AMC data structure."""
    tests = d.get("tests")
    by = d.get("byContest")
    if not isinstance(tests, dict):
        r.err("amc: 'tests' missing or not an object")
        return
    if not isinstance(by, dict):
        r.err("amc: 'byContest' missing or not an object")
        return
    if set(by) != CONTESTS:
        r.err(f"amc: byContest keys {sorted(by)} != {sorted(CONTESTS)}")
    # every listed id resolves, no dupes, grouping covers tests
    listed: list[str] = []
    for c, ids in by.items():
        for tid in ids:
            listed.append(tid)
            if tid not in tests:
                r.err(f"amc: byContest[{c}] lists unknown id {tid}")
            elif tests[tid].get("contest") != c:
                r.err(
                    f"amc: {tid} contest={tests[tid].get('contest')!r} but grouped under {c!r}"
                )
    if len(listed) != len(set(listed)):
        r.err("amc: a test id appears in byContest more than once")
    for tid in tests:
        if tid not in listed:
            r.warn(f"amc: {tid} not shown in byContest (won't appear in UI)")
    for tid, t in tests.items():
        validate_test(tid, t, r)


def validate_test(tid: str, t: dict[str, Any], r: Report) -> None:  # noqa: C901, PLR0912
    """Validate a single AMC test entry."""
    if t.get("id") != tid:
        r.err(f"amc:{tid} id field {t.get('id')!r} != key")
    if t.get("contest") not in CONTESTS:
        r.err(f"amc:{tid} bad contest {t.get('contest')!r}")
    sm = t.get("scoreMode")
    if sm not in {"count", "sixpoint"}:
        r.err(f"amc:{tid} bad scoreMode {sm!r}")
    mode = t.get("mode")
    if mode not in {"img", "latex"}:
        r.err(f"amc:{tid} bad mode {mode!r}")
    if not isinstance(t.get("durationSec"), (int, float)):
        r.err(f"amc:{tid} durationSec not numeric")
    probs = t.get("problems")
    ans = t.get("answers")
    if not isinstance(probs, list):
        r.err(f"amc:{tid} problems not a list")
        return
    if not isinstance(ans, list):
        r.err(f"amc:{tid} answers not a list")
        return
    if len(probs) != 25:
        r.warn(f"amc:{tid} has {len(probs)} problems (expected 25)")
    if len(ans) != len(probs):
        r.err(f"amc:{tid} answers={len(ans)} != problems={len(probs)}")
    voided = set(t.get("voided") or [])
    for i, a in enumerate(ans):
        if a is None:
            if (i + 1) not in voided:
                r.err(f"amc:{tid} answer {i + 1} is null but not in voided")
        elif a not in "ABCDE":
            r.err(f"amc:{tid} answer {i + 1} = {a!r} not A-E")
    for idx, p in enumerate(probs, 1):
        if p.get("n") != idx:
            r.warn(f"amc:{tid} problem at position {idx} has n={p.get('n')}")
        if not p.get("sol"):
            r.warn(f"amc:{tid} problem {idx} missing sol link")
        if mode == "img":
            img = p.get("img", "")
            if not DATA_URI.match(img):
                r.err(f"amc:{tid} problem {idx} img is not a data: URI")
            if "q" in p or "choices" in p:
                r.err(f"amc:{tid} problem {idx} has latex fields in an img test")
        else:
            q = p.get("q", "")
            if not q:
                r.err(f"amc:{tid} problem {idx} empty q")
            if EXT_IMG.search(q):
                r.err(
                    f"amc:{tid} problem {idx} q has an external <img> (must be data:)"
                )
            ch = p.get("choices")
            if not isinstance(ch, list) or len(ch) != 5:
                r.err(
                    f"amc:{tid} problem {idx} has {len(ch) if isinstance(ch, list) else 'no'} choices (need 5)"
                )
            else:
                for j, (letter, c) in enumerate(zip("ABCDE", ch, strict=True)):
                    if c.get("L") != letter:
                        r.err(
                            f"amc:{tid} problem {idx} choice {j} L={c.get('L')!r} != {letter}"
                        )
                    if not (c.get("html") or "").strip():
                        r.err(f"amc:{tid} problem {idx} choice {letter} empty html")


def validate_diag(d: dict[str, Any], r: Report) -> None:  # noqa: C901, PLR0912
    """Validate the top-level diagnostic data structure."""
    inst = d.get("instruments")
    order = d.get("order")
    ladder = d.get("ladder")
    catalog = d.get("catalog")
    if not isinstance(inst, dict):
        r.err("diag: 'instruments' missing")
        return
    if not isinstance(order, list):
        r.err("diag: 'order' missing or not a list")
    else:
        for iid in order:
            if iid not in inst:
                r.err(f"diag: order lists unknown instrument {iid}")
        for iid in inst:
            if iid not in order:
                r.warn(f"diag: {iid} not in order (won't appear in UI)")
    courses = {v.get("course") for v in inst.values()}
    if isinstance(ladder, list):
        for c in ladder:
            if c not in courses:
                r.err(f"diag: ladder course {c!r} has no matching instrument course")
    else:
        r.err("diag: 'ladder' missing or not a list")
    if isinstance(catalog, list):
        cat_courses = {row.get("course") for row in catalog}
        for c in ladder or []:
            if c not in cat_courses:
                r.err(f"diag: ladder course {c!r} absent from catalog")
        for row in catalog:
            g = row.get("gate")
            if g not in {"diagnostic", "prereq", "amc"}:
                r.err(f"diag: catalog {row.get('course')!r} bad gate {g!r}")
            if g == "amc" and not isinstance(row.get("min"), (int, float)):
                r.err(
                    f"diag: catalog {row.get('course')!r} gate=amc but no numeric min"
                )
    else:
        r.err("diag: 'catalog' missing or not a list")
    for iid, v in inst.items():
        validate_instrument(iid, v, r)


def validate_instrument(iid: str, v: dict[str, Any], r: Report) -> None:  # noqa: C901, PLR0912
    """Validate a single diagnostic instrument entry."""
    if v.get("id") != iid:
        r.err(f"diag:{iid} id field {v.get('id')!r} != key")
    if v.get("role") not in {"AYR", "DYK"}:
        r.err(f"diag:{iid} bad role {v.get('role')!r}")
    secs = v.get("sections")
    if not isinstance(secs, list) or not secs:
        r.err(f"diag:{iid} no sections")
        return
    items = [it for s in secs for it in s.get("items", [])]
    ids = [it.get("id") for it in items]
    if len(ids) != len(set(ids)):
        r.err(f"diag:{iid} duplicate item id")
    g = v.get("grading") or {}
    mode = g.get("mode")
    if mode == "single":
        if not all(k in g for k in ("total", "need")):
            r.err(f"diag:{iid} single grading missing total/need")
        else:
            if g["need"] > g["total"]:
                r.err(f"diag:{iid} need>{'total'} ({g['need']}>{g['total']})")
            if g["total"] != len(items):
                r.warn(f"diag:{iid} grading.total={g['total']} but {len(items)} items")
    elif mode == "fundps":
        need = ("fundTotal", "fundNeeded", "psTotal", "psNeeded")
        if not all(k in g for k in need):
            r.err(f"diag:{iid} fundps grading missing a field")
        else:
            if g["fundNeeded"] > g["fundTotal"]:
                r.err(f"diag:{iid} fundNeeded>fundTotal")
            if g["psNeeded"] > g["psTotal"]:
                r.err(f"diag:{iid} psNeeded>psTotal")
            fund = sum(1 for it in items if it.get("group") == "fund")
            ps = sum(1 for it in items if it.get("group") == "ps")
            if fund != g["fundTotal"]:
                r.warn(f"diag:{iid} {fund} fund items but fundTotal={g['fundTotal']}")
            if ps != g["psTotal"]:
                r.warn(f"diag:{iid} {ps} ps items but psTotal={g['psTotal']}")
            for it in items:
                if it.get("group") not in {"fund", "ps"}:
                    r.err(f"diag:{iid} item {it.get('id')} missing fund/ps group")
    else:
        r.err(f"diag:{iid} bad grading mode {mode!r}")
    for it in items:
        if (
            not it.get("manual")
            and it.get("v") is None
            and not (it.get("accept") or [])
        ):
            r.err(
                f"diag:{iid} item {it.get('id')} auto-graded but has neither v nor accept"
            )
        if not (it.get("ans") or "").strip():
            r.warn(f"diag:{iid} item {it.get('id')} blank ans")


def main() -> None:
    """Run validation of AMC and diagnostic content files."""
    here = Path(__file__).resolve().parent
    amc_path = sys.argv[1] if len(sys.argv) > 1 else str(here / "amc_data.json")
    diag_path = sys.argv[2] if len(sys.argv) > 2 else str(here / "diag_data.json")
    r = Report()
    try:
        with Path(amc_path).open(encoding="utf-8") as fh:
            validate_amc(json.load(fh), r)
    except (OSError, ValueError) as e:
        r.err(f"amc: could not load {amc_path}: {e}")
    try:
        with Path(diag_path).open(encoding="utf-8") as fh:
            validate_diag(json.load(fh), r)
    except (OSError, ValueError) as e:
        r.err(f"diag: could not load {diag_path}: {e}")
    for w in r.warns:
        print("WARN:", w)  # noqa: T201
    for e in r.errs:
        print("FAIL:", e)  # noqa: T201
    if r.errs:
        print(f"\n{len(r.errs)} error(s), {len(r.warns)} warning(s). NOT READY.")  # noqa: T201
        sys.exit(1)
    print(  # noqa: T201
        f"\nOK. 0 errors, {len(r.warns)} warning(s). Content conforms to the contract."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
