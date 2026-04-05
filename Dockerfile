# Use Python 3.10 slim for lightweight footprint
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy Requirements
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Complete Project
COPY . .

# Set Environment Variables (Optional)
ENV PYTHONUNBUFFERED=1
ENV API_BASE_URL="https://router.huggingface.co/v1"

# Expose Default OpenEnv Port (if needed for FastAPI)
EXPOSE 7860

# Default Command: Start Inference Loop
CMD ["python", "inference.py"]
