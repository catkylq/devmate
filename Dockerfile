FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md config.toml /app/
COPY src /app/src
COPY docs /app/docs
COPY .skills /app/.skills

RUN uv sync

ENV PYTHONPATH=/app/src

CMD ["uv", "run", "devmate-api"]

