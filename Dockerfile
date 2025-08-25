# Multi-stage build for optimal image size and caching
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./

ENV UV_TORCH_BACKEND=cu121 \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy

RUN uv sync --frozen --no-install-project --no-dev

COPY . ./

RUN uv sync --no-build-isolation-package flash-attn

# Runtime stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update && apt-get install -y \
    libgomp1 \
    build-essential \
    git \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_TORCH_BACKEND=auto

USER appuser

EXPOSE 8080

ENTRYPOINT ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD []