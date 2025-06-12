# Base Python image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash greenlightpa
USER greenlightpa
WORKDIR /app

# Install Python dependencies
COPY --chown=greenlightpa:greenlightpa requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
COPY --chown=greenlightpa:greenlightpa requirements-dev.txt ./requirements-dev.txt
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir --user -r requirements-dev.txt; fi

# Create directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Command for development (with hot reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy application code
COPY --chown=greenlightpa:greenlightpa app/ ./app/
COPY --chown=greenlightpa:greenlightpa alembic/ ./alembic/
COPY --chown=greenlightpa:greenlightpa alembic.ini .

# Create directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 