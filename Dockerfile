# 2-Stage Dockerfile - makes the image size significantly smaller

########################################################
# Stage 1: Builder stage
########################################################
FROM python:3.11-slim-bookworm AS builder

# # Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project into `/app`
WORKDIR /app

# Copy pyproject.toml, uv.lock that define the dependencies
COPY pyproject.toml uv.lock

# Copy code over
COPY src /app/src

# Install the dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

########################################################
# Stage 2: Final stage
########################################################
FROM python:3.11-slim-bookworm

# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.
WORKDIR /app

# Install curl in the final image as well
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the /usr/local from the builder
COPY --from=builder /usr/local /usr/local

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

EXPOSE 80

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "80"]

# If one wants to not use the API endpoint
# CMD ["python", "/app/run.py"]

# Debug container (keep running with)
# CMD ['sleep', '1000']