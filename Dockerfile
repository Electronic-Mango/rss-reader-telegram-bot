# Dockerfile which can be used for deploying the bot as a Docker container.

FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/main ./src/main

COPY *.toml ./
COPY *.yaml ./

CMD ["python", "src/main/main.py"]
