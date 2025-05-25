FROM python:3.12-bullseye
RUN apt update && apt-get install vim -y && apt-get install lsof -y

ENV POETRY_VERSION=2.1.1
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock log.ini /app/
RUN poetry install --no-root --no-interaction --no-ansi

COPY metrics/ /app/metrics/
COPY cyberpartner_create/ /app/cyberpartner_create/
COPY main.py /app/
