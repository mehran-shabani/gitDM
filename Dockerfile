FROM python:3.11-slim

# Create a non-root user and group
RUN addgroup --system app && adduser --system --group app

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Change ownership to the new user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1