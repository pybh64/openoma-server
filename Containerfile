FROM docker.io/library/python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* ./

# Copy the openoma library (needed as local dependency)
COPY ../openoma /openoma

# Install dependencies
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy application code
COPY src/ src/
COPY main.py .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "openoma_server.app:app", "--host", "0.0.0.0", "--port", "8000"]
