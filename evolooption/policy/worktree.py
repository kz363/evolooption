import subprocess
from dataclasses import dataclass
from pathlib import Path


def _git_paths(root: Path, command: list[str]) -> list[str]:
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git command failed"
        raise RuntimeError(f"could not enumerate changed paths: {detail}")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


@dataclass(frozen=True)
class WorktreeRunner:
    root: Path

    def changed_paths(self) -> list[str]:
        tracked = _git_paths(self.root, ["git", "diff", "--name-only", "HEAD"])
        untracked = _git_paths(
            self.root,
            ["git", "ls-files", "--others", "--exclude-standard"],
        )
        return list(dict.fromkeys(tracked + untracked))
