# Invoice Processing System Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt pyproject.toml* poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt || \
    pip install --no-cache-dir --user requests streamlit pandas numpy

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p data/invoices data/processed logs .pids

# Make scripts executable
RUN chmod +x scripts/*.sh

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501 || exit 1

# Default command
CMD ["python", "main.py", "web", "--host", "0.0.0.0", "--port", "8501"]