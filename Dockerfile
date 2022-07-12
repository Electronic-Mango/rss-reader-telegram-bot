FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY .env .
COPY feeds.yaml .
COPY bot.py .
COPY db.py .
COPY error_handler.py .
COPY feed_parser.py .
COPY feed_reader.py .
COPY sender.py .
COPY settings.py .
COPY update_checker.py .
RUN mkdir commands
COPY commands/add.py commands/
COPY commands/hello.py commands/
COPY commands/list.py commands/
COPY commands/remove_all.py commands/
COPY commands/remove.py commands/
COPY commands/start_help.py commands/

CMD ["python3.10", "bot.py"]
