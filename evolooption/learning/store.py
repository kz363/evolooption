from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Lesson:
    text: str
    source: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_iso(cls, text: str, source: str, created_at: str) -> "Lesson":
        return cls(text=text, source=source, created_at=datetime.fromisoformat(created_at))


class InMemoryLessonStore:
    def __init__(self) -> None:
        self._lessons: list[Lesson] = []

    def add(self, lesson: Lesson) -> None:
        self._lessons.append(lesson)

    def list(self) -> list[Lesson]:
        return list(self._lessons)
