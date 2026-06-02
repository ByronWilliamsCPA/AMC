"""Tests for the content seed loader.

Seeds the real ``content/diag_data.json`` and a synthetic AMC payload into an
in-memory database, verifying counts, idempotency, and that the seeded content
is gradeable end to end.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from amc.models import (
    DiagnosticCatalogEntry,
    DiagnosticInstrument,
    DiagnosticItem,
    Exam,
    Problem,
)
from amc.repositories.catalog import DiagnosticRepository
from amc.seed import seed_amc, seed_catalog, seed_diag

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

_DIAG_PATH = Path(__file__).resolve().parents[2] / "content" / "diag_data.json"

_AMC_FIXTURE = {
    "tests": {
        "AMC8-2019": {
            "id": "AMC8-2019",
            "contest": "AMC 8",
            "year": 2019,
            "exam": "",
            "durationSec": 2400,
            "scoreMode": "count",
            "mode": "latex",
            "voided": [],
            "answers": ["A", "B", "C"],
            "problems": [
                {
                    "n": 1,
                    "q": "1+1?",
                    "choices": [{"L": L, "html": L} for L in "ABCDE"],
                    "sol": "https://example.com/1",
                },
                {
                    "n": 2,
                    "q": "2+2?",
                    "choices": [{"L": L, "html": L} for L in "ABCDE"],
                    "sol": "https://example.com/2",
                },
                {
                    "n": 3,
                    "q": "3+3?",
                    "choices": [{"L": L, "html": L} for L in "ABCDE"],
                    "sol": "https://example.com/3",
                },
            ],
        }
    },
    "byContest": {"AMC 8": ["AMC8-2019"], "AMC 10": [], "AMC 12": []},
    "keyedTests": [],
}


class TestSeedAmc:
    """Seeding AMC content."""

    async def test_seeds_exam_and_problems(self, db_session: AsyncSession) -> None:
        exams, problems = await seed_amc(db_session, _AMC_FIXTURE)
        assert exams == 1
        assert problems == 3

        exam = (await db_session.execute(select(Exam))).scalar_one()
        assert exam.contest == "AMC 8"
        assert exam.num_problems == 3

        rows = (
            (await db_session.execute(select(Problem).order_by(Problem.number)))
            .scalars()
            .all()
        )
        # Answer key is taken from the test-level answers array.
        assert [p.correct_answer for p in rows] == ["A", "B", "C"]

    async def test_idempotent_reseed(self, db_session: AsyncSession) -> None:
        await seed_amc(db_session, _AMC_FIXTURE)
        await seed_amc(db_session, _AMC_FIXTURE)
        exams = (await db_session.execute(select(Exam))).scalars().all()
        problems = (await db_session.execute(select(Problem))).scalars().all()
        # Re-running does not duplicate the exam or its problems.
        assert len(exams) == 1
        assert len(problems) == 3


class TestSeedDiag:
    """Seeding the real diagnostic content bundle."""

    async def test_seeds_all_instruments_and_items(
        self, db_session: AsyncSession
    ) -> None:
        with _DIAG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)

        instruments, items = await seed_diag(db_session, data)
        # The bundle documents 10 instruments and 218 items.
        assert instruments == 10
        assert items == 218

        rows = (await db_session.execute(select(DiagnosticInstrument))).scalars().all()
        assert {r.id for r in rows} >= {"pa1-pre", "algA-pre", "count-post"}

    async def test_item_fields_seeded(self, db_session: AsyncSession) -> None:
        with _DIAG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        await seed_diag(db_session, data)

        # The pa1-pre first item carries a numeric value and accept list.
        stmt = select(DiagnosticItem).where(DiagnosticItem.label == "1(a)")
        item = (await db_session.execute(stmt)).scalars().first()
        assert item is not None
        assert item.numeric_value == 3660.0
        assert "3,660" in item.accept
        assert item.manual is False


class TestSeedCatalog:
    """Seeding the diagnostic course catalog and reading its AMC gates."""

    async def test_seeds_catalog_with_amc_gates(self, db_session: AsyncSession) -> None:
        with _DIAG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)

        count = await seed_catalog(db_session, data)
        # The bundle documents 10 catalog rows.
        assert count == 10

        rows = (
            (await db_session.execute(select(DiagnosticCatalogEntry))).scalars().all()
        )
        amc = {r.course: r for r in rows if r.gate == "amc"}
        # Only the two AMC-gated courses carry a score threshold (CONSTANTS §3).
        assert amc["AMC 10 Problem Series"].min_score == pytest.approx(60.0)
        assert amc["AMC 10 Final Fives"].min_score == pytest.approx(80.0)

    async def test_idempotent_reseed(self, db_session: AsyncSession) -> None:
        with _DIAG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        await seed_catalog(db_session, data)
        await seed_catalog(db_session, data)
        rows = (
            (await db_session.execute(select(DiagnosticCatalogEntry))).scalars().all()
        )
        # Re-running upserts by course rather than duplicating rows.
        assert len(rows) == 10

    async def test_list_amc_gates_sorted_by_min_score(
        self, db_session: AsyncSession
    ) -> None:
        with _DIAG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        await seed_catalog(db_session, data)

        gates = await DiagnosticRepository(db_session).list_amc_gates()
        # Only amc rows, lowest bar first; prereq/diagnostic rows are excluded.
        assert [g.course for g in gates] == [
            "AMC 10 Problem Series",
            "AMC 10 Final Fives",
        ]
        assert [g.min_score for g in gates] == pytest.approx([60.0, 80.0])


class TestSeedCli:
    """The ``python -m amc.seed`` entry point against a temp SQLite file."""

    def test_main_seeds_from_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from sqlalchemy import create_engine, text

        import amc.core.database as db_module
        from amc import seed as seed_module

        # Point the app at a throwaway file-based SQLite database.
        db_path = tmp_path / "seed.db"
        url = f"sqlite+aiosqlite:///{db_path}"
        monkeypatch.setattr(db_module.settings, "database_url", url)
        # Reset the cached engine so the new URL takes effect.
        db_module._engine = None
        db_module._sessionmaker = None

        # Create the schema synchronously for the CLI run.
        sync_engine = create_engine(f"sqlite:///{db_path}")
        from amc.models import Base

        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()

        # Write a tiny AMC file and reuse the real diagnostics file.
        amc_path = tmp_path / "amc.json"
        with amc_path.open("w", encoding="utf-8") as handle:
            json.dump(_MINIMAL_AMC, handle)

        seed_module.main(["--amc", str(amc_path), "--diag", str(_DIAG_PATH)])

        # Verify rows landed.
        check = create_engine(f"sqlite:///{db_path}")
        with check.connect() as conn:
            exams = conn.execute(text("SELECT count(*) FROM exams")).scalar_one()
            items = conn.execute(
                text("SELECT count(*) FROM diagnostic_items")
            ).scalar_one()
        check.dispose()
        assert exams == 1
        assert items == 218


_MINIMAL_AMC = {
    "tests": {
        "AMC8-2016": {
            "id": "AMC8-2016",
            "contest": "AMC 8",
            "year": 2016,
            "exam": "",
            "durationSec": 2400,
            "scoreMode": "count",
            "mode": "latex",
            "voided": [],
            "answers": ["A"],
            "problems": [
                {
                    "n": 1,
                    "q": "1?",
                    "choices": [{"L": x, "html": x} for x in "ABCDE"],
                    "sol": "s",
                }
            ],
        }
    },
    "byContest": {"AMC 8": ["AMC8-2016"], "AMC 10": [], "AMC 12": []},
    "keyedTests": [],
}
