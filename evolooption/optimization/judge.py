"""LLM-as-a-Judge grading.

Grades a provider's output against a declarative numeric rubric using a separate
``LLMClient`` (the "judge" model). Returns a single numeric score.

The rubric is declared up-front — every criterion is a ``(name, points)`` pair. The
judge is prompted to evaluate each criterion and return a per-criterion score; the
final score is the deterministic sum. This is the "mathematical evaluation criteria"
rule: the rubric exists *before* any shadow test, and is part of the proposal.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from evolooption.llm.client import LLMClient, LLMMessage


@dataclass(frozen=True)
class RubricCriterion:
    """One evaluation criterion.

    ``points`` is the maximum score for satisfying this criterion. The judge returns
    an integer in ``[0, points]`` per criterion, and the final score is the sum.
    """

    name: str
    description: str
    points: int


@dataclass(frozen=True)
class JudgeVerdict:
    """The result of grading one output against a rubric."""

    score: int
    per_criterion: dict[str, int] = field(default_factory=dict)
    rationale: str | None = None


@dataclass
class LLMJudge:
    """Grades outputs against a rubric using a judge LLM.

    The judge model is intentionally separate from the provider being graded. A
    deployment may pass a local model as the judge; the graded provider may be
    remote and more expensive. The judge never sees raw secrets or credentials.
    """

    judge_client: LLMClient
    role: str = "judge"

    def grade(
        self,
        *,
        output: str,
        rubric: Sequence[RubricCriterion],
        context: str | None = None,
    ) -> JudgeVerdict:
        """Grade ``output`` against ``rubric`` using the configured judge client."""
        if not rubric:
            raise ValueError("rubric must contain at least one criterion")
        prompt = _build_prompt(output=output, rubric=rubric, context=context)
        schema = {
            "type": "object",
            "required": ["per_criterion", "score", "rationale"],
            "properties": {
                "per_criterion": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "score": {"type": "integer"},
                "rationale": {"type": "string"},
            },
        }
        response = self.judge_client.structured(
            [LLMMessage(role="user", content=prompt)],
            role=self.role,
            schema=schema,
        )
        per_criterion = _coerce_per_criterion(response.get("per_criterion"), rubric)
        expected = sum(c.points for c in rubric)
        score = _coerce_int(response.get("score"))
        if score is None:
            score = sum(per_criterion.values())
        score = max(0, min(expected, score))
        return JudgeVerdict(
            score=score,
            per_criterion=per_criterion,
            rationale=str(response.get("rationale", "")).strip() or None,
        )


def _build_prompt(*, output: str, rubric: Iterable[RubricCriterion], context: str | None) -> str:
    criteria_lines = []
    for criterion in rubric:
        criteria_lines.append(
            f"- name={criterion.name!r} max={criterion.points}: {criterion.description}"
        )
    criteria_block = "\n".join(criteria_lines)
    context_block = f"\nContext:\n{context}\n" if context else ""
    return (
        "You are an evaluation judge. Grade the OUTPUT against the RUBRIC. "
        "Return JSON with keys: per_criterion (object mapping criterion name -> int "
        "in [0, max]), score (sum of per_criterion, capped to rubric max), and "
        "rationale (one short sentence).\n"
        f"RUBRIC:\n{criteria_block}\n"
        f"OUTPUT:\n{output}{context_block}"
    )


def _coerce_per_criterion(
    raw: object, rubric: Sequence[RubricCriterion]
) -> dict[str, int]:
    if not isinstance(raw, dict):
        raw = {}
    out: dict[str, int] = {}
    for criterion in rubric:
        value = raw.get(criterion.name)
        coerced = _coerce_int(value)
        if coerced is None:
            out[criterion.name] = 0
        else:
            out[criterion.name] = max(0, min(criterion.points, coerced))
    return out


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


__all__ = ["JudgeVerdict", "LLMJudge", "RubricCriterion"]
