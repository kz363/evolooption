$ErrorActionPreference = "Stop"
python -m ruff check .
python -m pytest -q -n auto
python -m compileall -q -x "(\.venv|\.venv-win)" .
git diff --check
