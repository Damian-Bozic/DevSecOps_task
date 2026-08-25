FROM python:3.12-slim

ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

RUN groupadd --gid ${APP_GID} appgroup \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --create-home appuser

COPY pyproject.toml .

RUN pip install --no-cache-dir .

COPY app ./app

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]