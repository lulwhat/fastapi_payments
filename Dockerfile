###########
# BUILDER #
###########

FROM python:3.12.2-alpine AS builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

COPY ./app ./app
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r ./app/requirements.txt

#######
# APP #
#######

FROM python:3.12.2-alpine AS app_payments

WORKDIR /home/app/web

# reqs
COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY ./app ./app
COPY ./alembic.ini .
COPY ./alembic ./alembic

COPY ./setup.py .
RUN pip install -e .

RUN addgroup -S app \
    && adduser -S app -G app \
    && apk update \
    && apk add libpq
RUN chown -R app:app .
USER app

RUN chmod +x ./app/entrypoint.sh
ENTRYPOINT ["./app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "./app"]