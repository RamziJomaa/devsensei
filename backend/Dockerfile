# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install build tools and python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runner (Production Slim Image)
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime postgres libraries
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . /app

# Create a non-root user and switch to it for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
