import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationCommand:
    command: tuple[str, ...]
    workdir: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class VerificationRunner:
    def __init__(self, commands: list[VerificationCommand]) -> None:
        self.commands = commands

    def run(self) -> list[VerificationResult]:
        results: list[VerificationResult] = []
        for command in self.commands:
            completed = subprocess.run(
                command.command,
                cwd=command.workdir,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
            )
            results.append(
                VerificationResult(
                    command=command.command,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            )
            if completed.returncode != 0:
                break
        return results
