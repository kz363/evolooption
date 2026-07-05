import json
from pathlib import Path

from evolooption.evolution.models import Postmortem
from evolooption.learning.store import Lesson


class JSONLessonStore:
    def __init__(self, path: Path, *, max_lessons: int | None = None) -> None:
        self.path = path
        self.max_lessons = max_lessons

    def add(self, lesson: Lesson) -> None:
        lessons = [*self.list(), lesson]
        if self.max_lessons is not None:
            lessons = lessons[-self.max_lessons :]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(
                [
                    {
                        "text": item.text,
                        "source": item.source,
                        "created_at": item.created_at.isoformat(),
                    }
                    for item in lessons
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    def add_postmortem(self, postmortem: Postmortem) -> None:
        for lesson in postmortem.lessons:
            self.add(Lesson(text=lesson, source="postmortem"))

    def list(self) -> list[Lesson]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Lesson.from_iso(item["text"], item["source"], item["created_at"]) for item in data]
