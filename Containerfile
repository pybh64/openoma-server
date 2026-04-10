FROM docker.io/library/python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the openoma local dependency (referenced as ../openoma in pyproject.toml)
# With WORKDIR=/app, ../openoma resolves to /openoma inside the container
COPY openoma/ /openoma/

# Copy server dependency files for layer caching
COPY openoma-server/pyproject.toml openoma-server/uv.lock* openoma-server/README.md ./

# Copy application source before sync so the project installs correctly
COPY openoma-server/src/ src/
COPY openoma-server/main.py .

# Install all dependencies including the project itself
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "openoma_server.app:app", "--host", "0.0.0.0", "--port", "8000"]
