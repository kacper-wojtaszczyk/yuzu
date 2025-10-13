# Yuzu Dockerfile
# Ubuntu-based image for geospatial Python applications
# This is a placeholder for when you're ready to Dockerize the Python app

FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-venv \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Install Poetry
RUN pip3 install --no-cache-dir poetry==2.2.1

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Create data directories
RUN mkdir -p data/raw data/processed

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Default command (can be overridden)
CMD ["python3", "-m", "yuzu"]

