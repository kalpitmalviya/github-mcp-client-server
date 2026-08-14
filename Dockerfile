# MCP Chat CLI - Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install -e .

# Stage 2: Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    USE_UV=0 \
    PYTHONPATH=/app

# Create .env file (will be overridden at runtime with actual values)
RUN echo "# MCP Chat Configuration\n\
ANTHROPIC_API_KEY=\n\
CLAUDE_MODEL=claude-3-5-sonnet-20241022\n\
USE_UV=0" > .env

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (if needed for future web interface)
EXPOSE 8000

# Default entry point
ENTRYPOINT ["python", "main.py"]
CMD []