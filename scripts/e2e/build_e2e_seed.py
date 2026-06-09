#!/usr/bin/env python3
"""Generate the synthetic e2e seed used by the Playwright harness.

The output contains no real AMC problem text or images: it is 25 trivial
LaTeX problems (one deliberately wide, to exercise KaTeX horizontal overflow)
plus one minimal diagnostic instrument and catalog row. It passes
``content/validate_content.py`` and seeds via ``python -m amc.seed``.

Run from the repo root:

    uv run python scripts/e2e/build_e2e_seed.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Problem 13 is intentionally wide to exercise KaTeX overflow at 320-375px.
_WIDE_LATEX = (
    r"\sum_{k=1}^{40} \left( a_k + b_k + c_k + d_k + e_k + f_k + g_k "
    r"+ h_k + i_k + j_k \right)^2 = \prod_{m=1}^{40} (x_m - y_m)(p_m - q_m)"
)


def _problem(n: int) -> dict[str, object]:
    q = _WIDE_LATEX if n == 13 else f"Synthetic problem {n}: compute {n} + {n}."
    return {
        "n": n,
        "q": q,
        "choices": [
            {"L": letter, "html": f"{letter}. choice {n}"} for letter in "ABCDE"
        ],
        "sol": f"https://example.test/solution/{n}",
    }


def build() -> dict[str, object]:
    answers = [["A", "B", "C", "D", "E"][n % 5] for n in range(25)]
    return {
        "tests": {
            "AMC10-2099": {
                "id": "AMC10-2099",
                "contest": "AMC 10",
                "year": 2099,
                "exam": "",
                "durationSec": 4500,
                "scoreMode": "count",
                "mode": "latex",
                "voided": [],
                "answers": answers,
                "problems": [_problem(n) for n in range(1, 26)],
            }
        },
        "byContest": {"AMC 8": [], "AMC 10": ["AMC10-2099"], "AMC 12": []},
        "keyedTests": [],
        "instruments": {
            "e2e-diag": {
                "id": "e2e-diag",
                "course": "E2E Synthetic Course",
                "role": "AYR",
                "kind": "",
                "grading": {"mode": "single", "total": 2, "need": 1},
                "instructions": "Synthetic diagnostic for e2e.",
                "sections": [
                    {
                        "title": "Section 1",
                        "items": [
                            {
                                "id": "e2e-1",
                                "label": "1",
                                "prompt": "What is 2 + 2?",
                                "ans": "4",
                                "v": 4,
                                "accept": ["4"],
                                "manual": False,
                            },
                            {
                                "id": "e2e-2",
                                "label": "2",
                                "prompt": "Explain your reasoning.",
                                "ans": "free response",
                                "manual": True,
                            },
                        ],
                    }
                ],
            }
        },
        "order": ["e2e-diag"],
        "ladder": [],
        "catalog": [
            {"course": "E2E Synthetic Course", "gate": "diagnostic", "note": "e2e"}
        ],
    }


def main() -> None:
    out = Path(__file__).resolve().parents[2] / "content" / "e2e_seed.json"
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
