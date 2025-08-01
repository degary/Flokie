# Multi-stage Dockerfile for Flask API Template
# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pip configuration for Aliyun mirror
COPY docker/pip.conf /etc/pip.conf

# Copy requirements and install Python dependencies
COPY requirements/ /tmp/requirements/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements/production.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_CONFIG=production \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with specific UID/GID for security
RUN groupadd -r -g 1000 flask && useradd -r -u 1000 -g flask flask

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Copy application code (exclude unnecessary files)
COPY --chown=flask:flask app/ ./app/
COPY --chown=flask:flask migrations/ ./migrations/
COPY --chown=flask:flask docker/healthcheck.sh ./docker/
COPY --chown=flask:flask wsgi.py run.py ./
COPY --chown=flask:flask .env.example ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/instance && \
    chown -R flask:flask /app && \
    chmod -R 755 /app

# Switch to non-root user
USER flask

# Expose port
EXPOSE 5001

# Health check with comprehensive script
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD /app/docker/healthcheck.sh

# Default command with optimized gunicorn settings
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5001", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--timeout", "120", \
     "--keepalive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:application"]
