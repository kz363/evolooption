import subprocess

from evolooption.policy.verification import VerificationCommand, VerificationRunner
from evolooption.policy.worktree import WorktreeRunner


class Completed:
    def __init__(self, returncode=0, stdout="", stderr="") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_verification_runner_stops_after_failure(monkeypatch) -> None:
    calls = []

    def fake_run(command, cwd, check, capture_output, text, timeout):
        calls.append(command)
        return Completed(returncode=1, stderr="failed")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = VerificationRunner([
        VerificationCommand(("python", "-m", "pytest")),
        VerificationCommand(("python", "-m", "ruff")),
    ])

    results = runner.run()

    assert len(results) == 1
    assert results[0].stderr == "failed"
    assert calls == [("python", "-m", "pytest")]


def test_worktree_runner_returns_changed_paths(monkeypatch, tmp_path) -> None:
    def fake_run(command, cwd, check, capture_output, text, timeout):
        assert command == ["git", "diff", "--name-only"]
        assert cwd == tmp_path
        return Completed(stdout="metrics/evaluator.py\n\npolicy/autonomy.py\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert WorktreeRunner(tmp_path).changed_paths() == [
        "metrics/evaluator.py",
        "policy/autonomy.py",
    ]


def test_worktree_runner_fail_closed_to_empty_list(monkeypatch, tmp_path) -> None:
    def fake_run(command, cwd, check, capture_output, text, timeout):
        return Completed(returncode=1, stderr="not a repo")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert WorktreeRunner(tmp_path).changed_paths() == []
