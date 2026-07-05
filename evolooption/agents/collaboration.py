from dataclasses import dataclass
from typing import Protocol


class Collaborator(Protocol):
    name: str

    def respond(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class DebateRound:
    advocate: str
    counter_advocate: str
    arbitrator: str
    red_team: str | None = None
