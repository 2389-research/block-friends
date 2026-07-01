# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install build tools and Cairo graphics library
# Build tools needed for compiling httptools and other C extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using Python 3.13 explicitly
ENV UV_PYTHON=python3.13
RUN uv sync --frozen --no-dev

# Copy application code and assets
COPY app.py door_agents.py avatar.py ./
COPY assets ./assets
COPY static ./static

# Create output directories for cache
RUN mkdir -p out/avatar out/avatar_png

# Set environment to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run uvicorn directly from venv
CMD ["/app/.venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
