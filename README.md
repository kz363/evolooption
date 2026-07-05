# evolooption

`evolooption` is a domain-agnostic, self-learning multi-agent framework with a clonable starter template.
Given a goal and a metric, it synthesizes a team of agents, iterates toward the target, learns from failures through postmortems and proposals, and can evolve its own configuration under an explicit autonomy policy.
It ships no real-world action tools by design; consuming projects supply their own domain actions.

Phases 0 through 4 are currently implemented: the package scaffold, a provider-agnostic LLM abstraction, evolution primitives, loop orchestration and policy enforcement, and a steward template for downstream repositories.

## Core concepts

The framework is built around a small set of composable primitives.

| Concept | Responsibility | Type |
| --- | --- | --- |
| Goal | Declares what the loop is optimizing and how it is measured | `Goal(prompt, target_metric, metadata)` |
| MetricEvaluator | Scores the current state against the goal | Protocol in `evolooption.metrics` |
| AgentSpec | Static definition of an agent, including activation rule | `evolooption.agents.AgentSpec` |
| ActivationRule | Declarative gate over a `QueryContext` field | `evolooption.agents.ActivationRule` |
| Signal | Recorded observation used as input to evolution | `evolooption.evolution.Signal` |
| Proposal | Declared change with a stable taxonomy | `new-agent`, `new-skill`, `config-change`, `code-change` |
| Postmortem | Analysis record produced after a failure or regression | `evolooption.evolution.Postmortem` |
| Lesson | Reusable insight derived from postmortems | `evolooption.learning.Lesson` |
| AutonomyTier | Policy level chosen by the operator | `conservative`, `assisted`, `full-auto` |
| ProtectedSurface | Set of paths, modules, and baseline tests the loop must not modify | `evolooption.policy.ProtectedSurface` |
| ActionPolicy | Permission, spend, and rate gate applied to tool execution | `evolooption.execution.ActionPolicy` |

## Design principles and trust boundary

The framework enforces a strict ownership boundary between deterministic Python code and LLM output:

- Python computes, validates, routes, persists state, enforces policy, and executes real-world actions.
- LLMs interpret context and propose agents, lessons, plans, and explanations.
- Proposals are never executed directly; they must pass through `ActionPolicy`, `ProtectedSurface`, and any configured verification runner.
- `MetricEvaluator` and protected-surface declarations are never writable by the loop. This is the primary control against reward hacking.
- Dynamic agent registration is declarative only; there is no use of `eval` for gating rules or registry dispatch.

Projects remain domain-owners of their tools, metrics, and protected paths. The framework never ships built-in real-world actions.

## Package map

| Subpackage | Responsibility |
| --- | --- |
| `evolooption.llm` | Provider-agnostic LLM abstraction and JSON-backed role configuration |
| `evolooption.agents` | Declarative agent specs, activation rules, and selection |
| `evolooption.evolution` | Signals, proposals, postmortems, scaffolding, and the dynamic registry |
| `evolooption.loop` | Goal-driven evolution loop with metric feedback and team synthesis |
| `evolooption.execution` | Tool definitions, executor protocol, and action policy enforcement |
| `evolooption.metrics` | `MetricEvaluator` protocol and metric contracts |
| `evolooption.policy` | Autonomy tiers, protected surface, and verification runners |
| `evolooption.learning` | Lesson store and JSON lesson persistence |
| `evolooption.cli` | Setup CLI for LLM provider configuration |

Deeper architecture guidance lives in `docs/ARCHITECTURE.md` and `docs/TECHNICAL_DESIGN.md`.

## Installation

Python 3.10 or newer is required.
The package has **no runtime dependencies**; adapters use only the Python standard library.

```bash
pip install -e .
```

For local development and testing:

```bash
pip install -e ".[dev]"
```

Dev extras currently provide `pytest` and `ruff`.

## Quickstart: run the loop offline

The evolution loop can run fully offline without any LLM configuration.
The example below uses fakes modelled on `tests/test_loop_phase3.py`, which is the canonical reference implementation.

```python
from evolooption.evolution.postmortem import StaticRootCauseAnalyzer
from evolooption.execution.interfaces import Tool
from evolooption.execution.policy import ActionPolicy
from evolooption.loop import EvolutionLoop, Goal
from evolooption.policy import ProtectedSurface


class MetricEvaluator:
    def evaluate(self, goal, state):
        return float(state.get("score", 0.0))


class ActionExecutor:
    def __init__(self):
        self.calls = []

    def tools(self):
        return [Tool(name="improve", description="improve fake score")]

    def execute(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return {"ok": True}


executor = ActionExecutor()

loop = EvolutionLoop(
    metric_evaluator=MetricEvaluator(),
    action_executor=executor,
    action_policy=ActionPolicy(
        allowed_tools={"improve"},
        require_human_approval=False,
    ),
    protected_surface=ProtectedSurface(globs=("metrics/**",)),
    root_cause_analyzer=StaticRootCauseAnalyzer(["low_score"]),
)

ledger = loop.run(
    Goal(prompt="raise score", target_metric="score"),
    {"score": 1.0, "target": 1.0, "action": {"tool": "improve", "arguments": {}}},
)

print(ledger.latest().success)
```

This example is covered by the offline test suite and does not make any network calls.

## Configuring LLM providers

LLM configuration is optional; the loop itself does not require any external model.
When you do want LLM-backed agents, configure providers with the setup CLI.
There is no installed console script, so the CLI is invoked as a module.

```bash
python -m evolooption.cli.setup \
  --provider ollama \
  --role analysis=qwen3:8b \
  --config state/evolooption_llm.json
```

OpenAI-compatible providers use a base URL and an environment variable name for the API key.

```bash
python -m evolooption.cli.setup \
  --provider openai-compatible \
  --role planner=gpt-4o-mini \
  --base-url https://api.example.com/v1 \
  --api-key-env OPENAI_API_KEY
```

Configuration is written to JSON under `state/`, which is excluded from version control and search tooling via `.ignore`.
At runtime, load the configuration and build a client per role.

```python
from pathlib import Path

from evolooption.llm import LLMConfig, RoleRegistry
from evolooption.llm.ollama import OllamaClient
from evolooption.llm.openai_compatible import OpenAICompatibleClient

config = LLMConfig.load(Path("state/evolooption_llm.json"))
registry = RoleRegistry(config.roles)

analysis_client = OllamaClient(roles=registry)
planner_client = OpenAICompatibleClient(
    roles=registry,
    base_url=config.base_url or "https://api.example.com/v1",
    api_key_env=config.api_key_env or "OPENAI_API_KEY",
)
```

`OllamaClient` targets the default local Ollama endpoint; `OpenAICompatibleClient` requires `base_url` and reads the API key from the environment variable specified by `api_key_env`, defaulting to `OPENAI_API_KEY`.

## Extending evolooption for your domain

### Implement a `MetricEvaluator`

```python
from evolooption.metrics import MetricEvaluator

class MyEvaluator:
    def evaluate(self, goal, state):
        return state["objective_score"]
```

### Implement an `ActionExecutor`

Declare `Tool` objects and gate them with `ActionPolicy`:

```python
from evolooption.execution.interfaces import Tool
from evolooption.execution.policy import ActionPolicy

class MyExecutor:
    def tools(self):
        return [Tool(name="deploy", description="deploy the artifact")]

    def execute(self, tool_name, arguments):
        return {"ok": True}

policy = ActionPolicy(
    allowed_tools={"deploy"},
    require_human_approval=True,
    spend_limit=10.0,
    rate_limit_per_minute=5,
)
```

`ActionPolicy.allows()` combines three independent gates: the tool allowlist, the cumulative spend limit, and a 60-second sliding window rate limiter keyed to `time.monotonic()`.
`require_human_approval` defaults to `True`.

### Define agent specs and activation rules

```python
from evolooption.agents import ActivationRule, AgentSelector, AgentSpec, QueryContext

core_agent = AgentSpec(
    name="core",
    prompt="Handle the default case.",
    schema={"type": "object"},
)

specialist = AgentSpec(
    name="risk-specialist",
    prompt="Evaluate risk assumptions.",
    schema={"type": "object"},
    activation=ActivationRule(field="task", operator="contains", value="risk"),
)

selector = AgentSelector(
    always_active=["core"],
    optional_agents={"risk-specialist": specialist},
    specs={"core": core_agent},
)

active = selector.select(QueryContext({"task": "risk", "source": "loop"}))
```

Operators supported by `ActivationRule` are `equals`, `contains`, `exists`, and `in`.

### Emit signals and generate proposals

```python
from evolooption.evolution import Signal
from evolooption.evolution.analyzer import ProposalEngine, ThresholdProposalRule
from evolooption.evolution.tracker import InMemorySignalStore

store = InMemorySignalStore()
store.add(Signal(kind="low-score", source="metric", strength=0.8))

rule = ThresholdProposalRule(
    signal_kind="low-score",
    threshold=0.7,
    proposal_kind="new-agent",
    proposal_name="risk-specialist",
    rationale="Repeated low-score signals need a specialist.",
)
engine = ProposalEngine(rules=[rule])
proposals = engine.propose(store.list())
```

### Scaffold accepted proposals and persist lessons

```python
from pathlib import Path

from evolooption.evolution import Proposal
from evolooption.evolution.scaffolder import ScaffoldRequest, Scaffolder
from evolooption.learning import JSONLessonStore

accepted_proposal = Proposal(
    kind="new-agent",
    name="risk-specialist",
    rationale="Repeated low-score signals need a specialist.",
    artifacts={"agents/risk-specialist.py": "..."},
)

scaffolder = Scaffolder()
scaffolder.scaffold(
    ScaffoldRequest(
        proposal=accepted_proposal,
        root=Path("workspace"),
    )
)

lesson_store = JSONLessonStore(Path("state/lessons.json"))
lesson_store.add_postmortem(postmortem)
```

`Scaffolder.scaffold()` validates that all artifact paths are contained under the configured `root`, and raises `ValueError` if any relative path would escape it.

## Autonomy and safety controls

`AutonomyTier` selects the default operating posture for a deployment:

| Tier | Behavior |
| --- | --- |
| `conservative` | Human approval required for all executions |
| `assisted` | Allowlisted low-risk actions run automatically; others require approval |
| `full-auto` | All policy-allowed actions run automatically within spend and rate limits |

`ProtectedSurface` declares what the loop may never modify.

```python
from evolooption.policy import ProtectedSurface

surface = ProtectedSurface(
    globs=("metrics/**", "policy/**", "tests/baseline/**"),
)

surface.validate_changed_paths(
    ["metrics/evaluator.py"]
)  # raises PermissionError listing blocked paths
```

`VerificationRunner` executes configured verification commands before accepting changes.
`WorktreeRunner` executes proposals in isolated git worktrees.

The loop may never:

- Modify `MetricEvaluator` implementations used by the loop.
- Modify protected-surface declarations.
- Bypass `ActionPolicy` gates, including spend, rate, and human-approval requirements.
- Execute any action whose tool is not in the allowlist.

## Steward template

`template/` contains a starter steward agent configuration that downstream repositories can copy into their own projects.

It provides:

- A canonical `AGENTS.md` steward registry.
- Five base stewards: Repo Janitor, AI Workflow Architect, Code Standards Reviewer, Context/Token-Efficiency, and PR Review Orchestrator.
- Canonical `.github/agents/*.agent.md` bodies.
- Thin `.kilo/agent/*.md` and `.codex/agents/*.toml` adapters for cross-tool parity.
- `.agents/skills/*` entries for Kilo and Codex.

Copy `template/` into your repository, then adapt the registry rows to describe domain-specific stewards.

## Consuming evolooption as a dependency

A typical consumer is a sibling repository that editable-installs this framework.

```toml
# example pyproject in the consuming repo
[tool.uv.sources]
evolooption = { path = "../evolooption", editable = true }
```

The recommended bridge pattern is:

- Wrap your existing LLM client as an `LLMClient` adapter, or use the provided `OllamaClient` and `OpenAICompatibleClient`.
- Map your operational roles onto a `RoleRegistry` backed by `state/evolooption_llm.json`.
- Declare a conservative `ProtectedSurface` that pins down metrics, policy, and baseline tests before enabling higher autonomy tiers.
- Supply only your domain-specific `Tool` implementations; the framework provides no built-in real-world actions.

The `agents` trading repository is one example of a consumer that follows this pattern.

## Testing and verification

All tests are fully offline; adapters and HTTP calls are monkeypatched.
No network access is required to run the suite.

Verification is tiered so agents can iterate cheaply and still run a full
gate before committing. Reuse a passing, still-valid result instead of
rerunning it when nothing relevant changed.

**Per-step (run frequently, cheap):**
```bash
ruff check <changed files>
pytest tests/test_llm_phase1.py -q   # targeted tests for the touched module
```

**Fast full loop (run when a unit of work is done):**
```bash
pytest -q -n auto
```

**Finalization gate (run once before commit / PR):**
```bash
python -m ruff check .
python -m pytest -q -n auto
python -m compileall -q -x "(\.venv|\.venv-win)" .
git diff --check
```

On Windows PowerShell, the finalization gate is also provided via `scripts/verify.ps1`.

The suite is small enough today that `-n auto` and `-m "not slow"` make little
difference, but the `slow` marker (declared in `pyproject.toml`) and
`pytest-xdist` are wired in now so growing test suites — in this repo or in
consumers built on top of it — can adopt `-m "not slow"` for the fast loop
without further setup. Mark a test `@pytest.mark.slow` once it meaningfully
slows down the fast loop (as a rough guide, more than ~1s).

`.ignore` and the repository’s default configuration exclude runtime directories such as `state/` and `outputs/`, along with virtual environments and caches, from search and editor tooling.

## Repository layout

```
evolooption/        # framework package
template/           # starter steward template for downstream repositories
docs/               # design docs and architecture notes
tests/              # offline pytest suite
scripts/            # verification and utility scripts
```

Additional documentation:

- `docs/ARCHITECTURE.md`
- `docs/TECHNICAL_DESIGN.md`
- `AGENTS.md`

## Status

Evolooption currently ships implemented support for:

- Provider-agnostic LLM abstraction with reference adapters.
- Declarative agents, activation rules, and selection.
- Evolution signals, proposals, postmortems, lessons, and scaffolding.
- Goal-driven evolution loop with protected surfaces and action policy enforcement.
- Steward agent template for downstream repositories.

Provider adapters are reference implementations; additional LLM providers can be added by implementing the `LLMClient` protocol.
