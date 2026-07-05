import json
from pathlib import Path

from evolooption.evolution.models import Postmortem
from evolooption.learning.store import Lesson


class JSONLessonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def add(self, lesson: Lesson) -> None:
        lessons = self.list()
        lessons.append(lesson)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
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

    def add_postmortem(self, postmortem: Postmortem) -> None:
        for lesson in postmortem.lessons:
            self.add(Lesson(text=lesson, source="postmortem"))

    def list(self) -> list[Lesson]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Lesson.from_iso(item["text"], item["source"], item["created_at"]) for item in data]
