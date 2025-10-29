FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:/root/.local/bin:/usr/local/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Install uv (fast Python package manager) and system deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv --version

# Copy dependency manifests first to leverage Docker cache
COPY pyproject.toml uv.lock /app/

# Create virtual env and install dependencies from lockfile
RUN uv sync --frozen --no-dev

# Copy application code
COPY pubsub /app/pubsub

# Default Temporal env (override in compose as needed)
ENV TEMPORAL_ADDRESS=temporal:7233 \
    TEMPORAL_NAMESPACE=default \
    TEMPORAL_TASK_QUEUE=pubsub-task-queue

CMD ["python", "-m", "pubsub.worker"]


