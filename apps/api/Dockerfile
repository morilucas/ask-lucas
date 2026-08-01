FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.11.3

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY apps/api/src ./src
RUN uv sync --frozen --no-dev
RUN mkdir /data && chown 65532:65532 /data

USER 65532:65532
EXPOSE 8000

CMD ["uvicorn", "ask_lucas.main:app", "--host", "0.0.0.0", "--port", "8000"]
