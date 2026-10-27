from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import uuid4

from core.language.facts import USER_KEY, Fact
from core.storage import db as _db

MAX_RESULTS = 25

# Upsert outcomes.
NEW = "new"
DUPLICATE = "duplicate"
FLIPPED = "flipped"  # same subject/relation/object, opposite polarity
REPLACED = "replaced"  # single-valued relation got a new value


@dataclass(frozen=True)
class UpsertResult:
    status: str
    fact: Fact
    previous: Fact | None = None


def _row_to_fact(row: sqlite3.Row) -> Fact:
    return Fact(
        id=row["id"],
        subject_key=row["subject_key"],
        subject_text=row["subject_text"],
        relation=row["relation"],
        object_key=row["object_key"],
        object_text=row["object_text"],
        polarity=int(row["polarity"]),
        copula=row["copula"] or "is",
    )


class FactStore:
    """SQLite-backed fact store. All lookups are exact matches on normalized keys."""

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = _db.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()  # always close: open handles lock files on Windows

    def upsert(self, fact: Fact) -> UpsertResult:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT * FROM facts WHERE subject_key = ? AND relation = ? AND object_key = ?",
                fact.identity,
            ).fetchone()
            if existing is not None:
                old = _row_to_fact(existing)
                if old.polarity == fact.polarity:
                    return UpsertResult(DUPLICATE, old)
                conn.execute(
                    "UPDATE facts SET polarity = ?, object_text = ?, copula = ?, updated_at = ? WHERE id = ?",
                    (fact.polarity, fact.object_text, fact.copula, now, old.id),
                )
                return UpsertResult(FLIPPED, replace(fact, id=old.id), previous=old)

            previous: Fact | None = None
            if fact.is_functional:
                rows = conn.execute(
                    "SELECT * FROM facts WHERE subject_key = ? AND relation = ? ORDER BY created_at",
                    (fact.subject_key, fact.relation),
                ).fetchall()
                if rows:
                    previous = _row_to_fact(rows[0])
                    conn.execute(
                        "DELETE FROM facts WHERE subject_key = ? AND relation = ?",
                        (fact.subject_key, fact.relation),
                    )

            fact_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO facts (id, subject_key, subject_text, relation, object_key, object_text,
                                   polarity, copula, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact_id,
                    fact.subject_key,
                    fact.subject_text,
                    fact.relation,
                    fact.object_key,
                    fact.object_text,
                    fact.polarity,
                    fact.copula,
                    now,
                    now,
                ),
            )
            stored = replace(fact, id=fact_id)
            return UpsertResult(
                REPLACED if previous is not None else NEW, stored, previous=previous
            )

    def get(self, subject_key: str, relation: str | None = None) -> list[Fact]:
        sql = "SELECT * FROM facts WHERE subject_key = ?"
        params: list[object] = [subject_key]
        if relation is not None:
            sql += " AND relation = ?"
            params.append(relation)
        sql += " ORDER BY created_at LIMIT ?"
        params.append(MAX_RESULTS)
        return self._fetch(sql, params)

    def find(self, subject_key: str, relation: str, object_key: str) -> Fact | None:
        rows = self._fetch(
            "SELECT * FROM facts WHERE subject_key = ? AND relation = ? AND object_key = ?",
            [subject_key, relation, object_key],
        )
        return rows[0] if rows else None

    def list_by(self, subject_key: str, relation: str, polarity: int) -> list[Fact]:
        return self._fetch(
            "SELECT * FROM facts WHERE subject_key = ? AND relation = ? AND polarity = ? "
            "ORDER BY created_at LIMIT ?",
            [subject_key, relation, polarity, MAX_RESULTS],
        )

    def about(self, term_key: str) -> list[Fact]:
        """Facts whose subject or object is exactly ``term_key`` (or an attribute of it)."""
        if term_key == USER_KEY:
            return self._fetch(
                "SELECT * FROM facts WHERE subject_key = ? OR subject_key LIKE ? ESCAPE '\\' "
                "ORDER BY created_at LIMIT ?",
                [USER_KEY, f"{_escape_like(USER_KEY)}:%", MAX_RESULTS],
            )
        return self._fetch(
            "SELECT * FROM facts WHERE subject_key = ? OR object_key = ? "
            "OR subject_key LIKE ? ESCAPE '\\' OR subject_key LIKE ? ESCAPE '\\' "
            "ORDER BY created_at LIMIT ?",
            [
                term_key,
                term_key,
                f"{_escape_like(term_key)}:%",
                f"%:{_escape_like(term_key)}",
                MAX_RESULTS,
            ],
        )

    def delete(self, fact: Fact) -> bool:
        """Delete the exact stored fact (subject, relation, object), whatever its polarity."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM facts WHERE subject_key = ? AND relation = ? AND object_key = ?",
                fact.identity,
            )
            return cursor.rowcount > 0

    def count(self) -> int:
        with self._conn() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0])

    def _fetch(self, sql: str, params: list[object]) -> list[Fact]:
        with self._conn() as conn:
            return [_row_to_fact(row) for row in conn.execute(sql, params).fetchall()]


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


DEFAULT_STORE = FactStore()
