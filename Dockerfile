# --- Build Stage ---
FROM python:3.10-slim

# --- Environment Configuration ---
# PYTHONUNBUFFERED: Ensure logs reach console immediately
# PYTHONDONTWRITEBYTECODE: Don't write .pyc files (keep image clean)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set production-ready working directory
WORKDIR /app

# --- System Dependencies ---
# Install build-essential for packages with C extensions and curl for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Python Dependencies ---
# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies (fastapi, uvicorn, openenv-core, pydantic, numpy, pandas)
RUN pip install --no-cache-dir -r requirements.txt

# --- Project Files ---
# Copy the entire project into the container
COPY . .

# --- Port Management ---
# Default port for Hugging Face Spaces and internal OpenEnv discovery
EXPOSE 7860

# --- Start Command ---
# Preferred: Start as a production-grade FastAPI web server
ENV ENABLE_WEB_INTERFACE=true
CMD ["python", "-m", "uvicorn", "env.server:app", "--host", "0.0.0.0", "--port", "7860"]

# --- Build & Run Instructions ---
# 1. Build:
#    docker build -t gatekeeper-env .
# 2. Run:
#    docker run -p 7860:7860 gatekeeper-env
