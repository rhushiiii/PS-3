FROM python:3.13-slim-bookworm

WORKDIR /app

COPY requirements.txt requirements.lock ./

RUN pip install --no-cache-dir \
    -r requirements.txt \
    -c requirements.lock

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
