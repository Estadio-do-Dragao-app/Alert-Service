# Autonomous Dockerfile for Alert-Service
FROM python:3.10-slim

ENV PYTHONPATH=/app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

COPY main.py mqtt_configs.py mqtt_handler.py schemas.py ./
# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
