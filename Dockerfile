# ---- build ----
FROM python:3.11-slim AS build
WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir . && pip install --no-cache-dir .[prod]

# ---- runtime ----
FROM python:3.11-slim
WORKDIR /srv
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY app ./app
# Alembic нужен в runtime: миграции применяются при старте приложения.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
RUN useradd -m botuser && mkdir -p /srv/data && chown -R botuser /srv
USER botuser
CMD ["python", "-m", "app.main"]