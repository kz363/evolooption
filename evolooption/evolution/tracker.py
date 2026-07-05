import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol

from evolooption.evolution.models import Signal


class SignalStore(Protocol):
    def add(self, signal: Signal) -> None: ...

    def list(self) -> list[Signal]: ...


class InMemorySignalStore:
    def __init__(self) -> None:
        self._signals: list[Signal] = []

    def add(self, signal: Signal) -> None:
        self._signals.append(signal)

    def list(self) -> list[Signal]:
        return list(self._signals)


class SQLiteSignalStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def add(self, signal: Signal) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO signals(kind, source, strength, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    signal.kind,
                    signal.source,
                    signal.strength,
                    json.dumps(signal.metadata, sort_keys=True),
                    signal.created_at.isoformat(),
                ),
            )

    def list(self) -> list[Signal]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                SELECT kind, source, strength, metadata_json, created_at
                FROM signals
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [
            Signal(
                kind=str(row[0]),
                source=str(row[1]),
                strength=float(row[2]),
                metadata=json.loads(row[3]),
                created_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    strength REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
