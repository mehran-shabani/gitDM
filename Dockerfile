# Dockerfile

FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set working directory before copy/run
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose default Django port
EXPOSE 8000

# ENV should be last according to test expectation
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

ENTRYPOINT ["/entrypoint.sh"]
