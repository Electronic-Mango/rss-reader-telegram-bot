FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY settings.py ./

COPY bot/bot.py ./bot/
COPY bot/error_handler.py ./bot/
COPY bot/update_checker.py ./bot/
COPY bot/sender.py ./bot/

COPY bot/command/add.py ./bot/command/
COPY bot/command/hello.py ./bot/command/
COPY bot/command/list.py ./bot/command/
COPY bot/command/remove_all.py ./bot/command/
COPY bot/command/remove.py ./bot/command/
COPY bot/command/start_help.py ./bot/command/

COPY db/client.py ./db/
COPY db/wrapper.py ./db/

COPY feed/parser.py ./feed/
COPY feed/reader.py ./feed/

COPY *.toml ./
COPY *.yaml ./

CMD ["python3.10", "main.py"]
