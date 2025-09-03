# Dockerfile

FROM python:3.13-slim

# Set working directory before copy/run
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list
COPY requirements.txt .

# Install Python packages with no cache
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose default Django port
EXPOSE 8000

# ENV should be the last instruction per test expectations
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
