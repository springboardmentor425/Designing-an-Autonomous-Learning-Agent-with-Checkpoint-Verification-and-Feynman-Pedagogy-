# ============================================
# Deep Research From Scratch - Dockerfile
# Python 3.11 + Node.js + uv package manager
# ============================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8000 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies including Node.js (required for MCP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version \
    && npm --version \
    && npx --version

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock langgraph.json ./
COPY src/ ./src/
COPY notebooks/ ./notebooks/

# Install dependencies using uv
RUN uv sync

# Create files directory for report storage
RUN mkdir -p /app/src/deep_research_from_scratch/files

# Expose port for LangGraph server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Default command - run LangGraph dev server using uvx
CMD ["uvx", "--refresh", "--from", "langgraph-cli[inmem]", "--with-editable", ".", "--python", "3.11", "langgraph", "dev", "--host", "0.0.0.0", "--port", "8000", "--allow-blocking"]
