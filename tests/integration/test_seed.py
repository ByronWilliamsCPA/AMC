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
    DiagnosticInstrument,
    DiagnosticItem,
    Exam,
    Problem,
)
from amc.seed import seed_amc, seed_diag

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
