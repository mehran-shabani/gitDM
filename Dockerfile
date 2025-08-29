FROM python:3.11-slim

WORKDIR /app

# Create a non-root user and group
RUN addgroup --system app && adduser --system --group app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Change ownership to the new user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

RUN python manage.py migrate && python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
