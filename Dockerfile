# Autonomous Dockerfile for Alert-Service
FROM python:3.10-slim

ENV PYTHONPATH=/app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

COPY . .

CMD ["python", "main.py"]
