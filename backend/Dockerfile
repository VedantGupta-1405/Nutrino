FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies needed for compiling psycopg2 and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root system user for container security
RUN useradd -m -u 1000 appuser

# Copy application files, Alembic configuration, and entrypoint
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY entrypoint.sh .

# Ensure entrypoint is executable and owned by non-root user
RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app

USER appuser

# Expose FastAPI application port
EXPOSE 8000

# Set entrypoint to run migrations and start server
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
