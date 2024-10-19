# Dockerfile which can be used for deploying the bot as a Docker container.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/main ./src/main

COPY *.yml ./

CMD ["python", "src/main/main.py"]
