# syntax=docker/dockerfile:1

# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip tools with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir wheel setuptools

# Copy only docker-requirements.txt
COPY docker-requirements.txt ./

# Create wheels with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /app/wheels -r docker-requirements.txt

# Final stage
FROM python:3.9-slim

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install packages from wheels and additional dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir /wheels/* python-multipart pymongo

# Copy application files
COPY ./main.py ./auth_email.py ./auth_phone.py ./
COPY ./cybershieldai-firebase-adminsdk-fbsvc-36a8d0d55c.json ./

# Create necessary directories
RUN mkdir -p /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV FIREBASE_CREDENTIALS=cybershieldai-firebase-adminsdk-fbsvc-36a8d0d55c.json

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]