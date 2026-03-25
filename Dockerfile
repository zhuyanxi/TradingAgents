# syntax=docker/dockerfile:1
FROM 3.12-alpine3.23

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy the rest of the application
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
# COPY pyproject.toml ./
# COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -e ".[dev]" 2>/dev/null || pip install -e .

# Create directories for results and data cache
RUN mkdir -p /app/results /app/tradingagents/dataflows/data_cache

# Default command runs the CLI
CMD ["tradingagents"]
