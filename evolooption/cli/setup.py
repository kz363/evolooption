import argparse
from pathlib import Path

from evolooption.llm.config import LLMConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure evolooption LLM providers.")
    parser.add_argument("--config", default="state/evolooption_llm.json")
    parser.add_argument("--provider", choices=["ollama", "openai-compatible"], required=True)
    parser.add_argument("--role", action="append", default=[], help="ROLE=MODEL mapping")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roles = _parse_roles(args.role)
    LLMConfig(
        provider=args.provider,
        roles=roles,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    ).save(Path(args.config))
    return 0


def _parse_roles(values: list[str]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"role mapping must be ROLE=MODEL: {value}")
        role, model = value.split("=", 1)
        role = role.strip()
        model = model.strip()
        if not role or not model:
            raise ValueError(f"role mapping must be ROLE=MODEL: {value}")
        roles[role] = model
    return roles


if __name__ == "__main__":
    raise SystemExit(main())
