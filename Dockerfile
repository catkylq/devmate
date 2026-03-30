FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md uv.lock ./
COPY src /app/src
COPY docs /app/docs
COPY examples /app/examples
COPY .skills /app/.skills

RUN uv sync --frozen

ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 3000

CMD ["devmate-api"]
