import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorktreeRunner:
    root: Path

    def changed_paths(self) -> list[str]:
        completed = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode != 0:
            return []
        return [line.strip() for line in completed.stdout.splitlines() if line.strip()]
