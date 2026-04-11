 - Openoma should be written as Openoma, not OpenOMA, unless it's in paths or code where case sensitivity is required, it can be written as openoma.
 - if .venv does not exist, create: uv venv .venv. 
 - Activate the venv with source .venv/bin/activate.
 - Use uv exclusively for package/project management (e.g., uv 
add, uv remove, uv sync, uv pip install -e .). Commit 
pyproject.toml and uv.lock.
 - Run tools/tests via uv run (example: uv run pytest tests/ -x 
-q).
 - Place all tests under tests/ named test_*.py.
 - Never use system Python or other package managers 
(pip/poetry/conda)