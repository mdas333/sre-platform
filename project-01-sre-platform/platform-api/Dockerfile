# syntax=docker/dockerfile:1.7
#
# Multi-stage build for the Platform API.
# - Stage 1 installs dependencies with uv into a clean venv.
# - Stage 2 is a minimal runtime image with only what's needed to run.
# The final image is small, does not contain uv or build tools, and runs
# as a non-root user. PYTHONPATH points at /app/src so existing imports
# (`from config import ...`) work without restructuring the package.

FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copy uv from its official image; faster than curl-install in a layer.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install into /opt/venv via uv's project-environment mechanism. uv sync
# populates the venv with the locked dependency set and the project itself.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
RUN uv venv /opt/venv && \
    uv sync --frozen --no-dev


FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH=/opt/venv/bin:$PATH

# Non-root user — avoids running as uid 0 inside the cluster.
RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid 10001 --shell /sbin/nologin app && \
    mkdir -p /app && chown -R app:app /app

COPY --from=builder --chown=app:app /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app:app src ./src

USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
