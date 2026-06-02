r"""Seed the database from the content bundle (``amc_data.json`` / ``diag_data.json``).

This is the repeatable import path the content handoff is built around: it reads
the two JSON files documented in ``content/CONTENT_CONTRACT.md``, optionally
validates them against the contract, and upserts exams, problems, diagnostic
instruments, and items into the database.

The loader is idempotent on natural keys (exam ``contest/year/variant`` and
instrument slug): re-running replaces a paper's problems rather than duplicating
them, so adding a new paper is "drop the JSON in and re-run."

Usage::

    uv run python -m amc.seed --amc content/amc_data.json \
        --diag content/diag_data.json

With no paths, it looks for the two files under ``content/``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from amc.core.database import dispose_engine, get_session
from amc.models import (
    DiagnosticCatalogEntry,
    DiagnosticInstrument,
    DiagnosticItem,
    Exam,
    Problem,
)
from amc.utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

_DEFAULT_AMC = Path("content/amc_data.json")
_DEFAULT_DIAG = Path("content/diag_data.json")


@dataclass(frozen=True)
class SeedCounts:
    """Tallies returned by a seed run.

    Attributes:
        exams: Number of exams upserted.
        problems: Number of problems written.
        instruments: Number of diagnostic instruments upserted.
        items: Number of diagnostic items written.
        catalog: Number of catalog entries upserted.
    """

    exams: int
    problems: int
    instruments: int
    items: int
    catalog: int


def _load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        path: The file to read.

    Returns:
        The parsed JSON object.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


async def seed_amc(session: AsyncSession, data: dict[str, Any]) -> tuple[int, int]:
    """Upsert AMC exams and their problems.

    For each exam, an existing row with the same contest/year/variant is replaced
    (its problems deleted and re-created) so re-runs are idempotent.

    Args:
        session: The active database session.
        data: The parsed ``amc_data.json`` object.

    Returns:
        A tuple of (exam count, problem count) written.
    """
    tests: dict[str, Any] = data.get("tests", {})
    exam_count = 0
    problem_count = 0

    for test in tests.values():
        exam = await _upsert_exam(session, test)
        # Replace problems wholesale for idempotency.
        await session.execute(delete(Problem).where(Problem.exam_id == exam.id))
        for problem in test.get("problems", []):
            session.add(_build_problem(exam.id, test, problem))
            problem_count += 1
        exam_count += 1

    await session.flush()
    return exam_count, problem_count


async def _upsert_exam(session: AsyncSession, test: dict[str, Any]) -> Exam:
    """Insert or update an exam from a contract test object.

    Args:
        session: The active database session.
        test: A single test object from ``amc_data.json``.

    Returns:
        The persisted exam.
    """
    contest = test["contest"]
    year = int(test["year"])
    variant = test.get("exam", "") or ""
    stmt = select(Exam).where(
        Exam.contest == contest, Exam.year == year, Exam.variant == variant
    )
    exam = (await session.execute(stmt)).scalar_one_or_none()
    if exam is None:
        exam = Exam(contest=contest, year=year, variant=variant)
        session.add(exam)

    exam.duration_sec = int(test["durationSec"])
    exam.score_mode = test["scoreMode"]
    exam.num_problems = len(test.get("problems", []))
    exam.voided = list(test.get("voided") or [])
    exam.source_url = test.get("sourceUrl")
    # Stash the answer key on the exam's problems below; the key lives per-problem.
    await session.flush()
    return exam


def _build_problem(
    exam_id: Any, test: dict[str, Any], problem: dict[str, Any]
) -> Problem:
    """Build a Problem ORM object from a contract problem object.

    The answer key for problem ``n`` comes from the test-level ``answers`` array
    (index ``n - 1``).

    Args:
        exam_id: The owning exam's id.
        test: The parent test object (for the answers array and mode).
        problem: A single problem object.

    Returns:
        An unsaved :class:`~amc.models.exam.Problem`.
    """
    number = int(problem["n"])
    answers: list[str | None] = test.get("answers", [])
    correct = answers[number - 1] if number - 1 < len(answers) else None
    mode = test.get("mode", "latex")
    render_mode = "image" if mode == "img" else "latex"
    return Problem(
        exam_id=exam_id,
        number=number,
        render_mode=render_mode,
        body_latex=problem.get("q"),
        image_path=problem.get("img"),
        choices=problem.get("choices"),
        # A null answer (voided problem) is stored as an empty string sentinel.
        correct_answer=(correct or ""),
        solution_url=problem.get("sol"),
    )


async def seed_diag(session: AsyncSession, data: dict[str, Any]) -> tuple[int, int]:
    """Upsert diagnostic instruments and their items.

    Args:
        session: The active database session.
        data: The parsed ``diag_data.json`` object.

    Returns:
        A tuple of (instrument count, item count) written.
    """
    instruments: dict[str, Any] = data.get("instruments", {})
    instrument_count = 0
    item_count = 0

    for slug, instrument in instruments.items():
        await _upsert_instrument(session, slug, instrument)
        await session.execute(
            delete(DiagnosticItem).where(DiagnosticItem.instrument_id == slug)
        )
        for section in instrument.get("sections", []):
            for item in section.get("items", []):
                session.add(_build_item(slug, section, item))
                item_count += 1
        instrument_count += 1

    await session.flush()
    return instrument_count, item_count


async def seed_catalog(session: AsyncSession, data: dict[str, Any]) -> int:
    """Upsert the diagnostic course catalog.

    The catalog is the placement engine's reference table (CONSTANTS.md §3): each
    row maps a course to how it is reached (``diagnostic`` / ``prereq`` / ``amc``).
    ``amc`` rows carry the ``min`` score the recommendation engine uses for its
    advisory unlock list. Upserts by ``course`` so re-runs are idempotent.

    Args:
        session: The active database session.
        data: The parsed ``diag_data.json`` object.

    Returns:
        The number of catalog entries upserted.
    """
    catalog: list[dict[str, Any]] = data.get("catalog", [])
    for row in catalog:
        course = row["course"]
        record = await session.get(DiagnosticCatalogEntry, course)
        if record is None:
            record = DiagnosticCatalogEntry(course=course)
            session.add(record)
        record.gate = row.get("gate", "")
        record.min_score = row.get("min")
        record.note = row.get("note", "")
    await session.flush()
    return len(catalog)


async def _upsert_instrument(
    session: AsyncSession, slug: str, instrument: dict[str, Any]
) -> DiagnosticInstrument:
    """Insert or update a diagnostic instrument.

    Args:
        session: The active database session.
        slug: The instrument id.
        instrument: The instrument object from ``diag_data.json``.

    Returns:
        The persisted instrument.
    """
    record = await session.get(DiagnosticInstrument, slug)
    if record is None:
        record = DiagnosticInstrument(id=slug)
        session.add(record)

    record.course = instrument["course"]
    record.kind = instrument.get("kind", "")
    record.role = instrument["role"]
    record.ladder = instrument.get("ladder", {})
    record.grading = instrument.get("grading", {})
    record.instructions = instrument.get("instructions", "")
    await session.flush()
    return record


def _build_item(
    slug: str, section: dict[str, Any], item: dict[str, Any]
) -> DiagnosticItem:
    """Build a DiagnosticItem ORM object from a contract item object.

    Args:
        slug: The owning instrument slug.
        section: The parent section (for its title).
        item: A single item object.

    Returns:
        An unsaved :class:`~amc.models.diagnostic.DiagnosticItem`.
    """
    return DiagnosticItem(
        instrument_id=slug,
        section_title=section.get("title", ""),
        label=item.get("label", ""),
        prompt=item.get("prompt", ""),
        answer=item.get("ans", ""),
        numeric_value=item.get("v"),
        accept=list(item.get("accept") or []),
        group=item.get("group"),
        manual=bool(item.get("manual", False)),
    )


async def run_seed(amc_path: Path, diag_path: Path) -> SeedCounts:
    """Seed the database from both content files within one transaction.

    Args:
        amc_path: Path to ``amc_data.json``.
        diag_path: Path to ``diag_data.json``.

    Returns:
        The counts of rows written.
    """
    # Read files synchronously up front so the async block is purely DB work.
    amc_data = _load_json(amc_path) if amc_path.exists() else None
    if amc_data is None:
        logger.warning("amc_data_missing", path=str(amc_path))
    diag_data = _load_json(diag_path)

    async with get_session() as session:
        exams, problems = (
            await seed_amc(session, amc_data) if amc_data is not None else (0, 0)
        )
        instruments, items = await seed_diag(session, diag_data)
        catalog = await seed_catalog(session, diag_data)
    return SeedCounts(
        exams=exams,
        problems=problems,
        instruments=instruments,
        items=items,
        catalog=catalog,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv``).

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Seed the AMC database.")
    parser.add_argument("--amc", type=Path, default=_DEFAULT_AMC)
    parser.add_argument("--diag", type=Path, default=_DEFAULT_DIAG)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: seed the database and log the counts.

    Args:
        argv: Optional argument list.
    """
    args = _parse_args(argv)

    async def _run() -> SeedCounts:
        try:
            return await run_seed(args.amc, args.diag)
        finally:
            await dispose_engine()

    counts = asyncio.run(_run())
    logger.info(
        "seed_complete",
        exams=counts.exams,
        problems=counts.problems,
        instruments=counts.instruments,
        items=counts.items,
        catalog=counts.catalog,
    )


if __name__ == "__main__":
    main()
