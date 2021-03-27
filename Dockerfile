FROM python:3.9-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt

RUN set -ex \
    && apk add su-exec dumb-init libpq \
    && apk add --virtual .temp-dependencies \
    gcc g++ libffi-dev make musl-dev postgresql-dev python3-dev openssl-dev cargo rustup\
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .temp-dependencies \
    && rm -rf /root/.cargo \
    && adduser -s /bin/sh -D -u 1111 app

WORKDIR /home/app

COPY --chown=app:app manage.py .
COPY --chown=app:app docbox docbox

ENTRYPOINT [ "/usr/bin/dumb-init", "su-exec", "app" ]
CMD [ "python" ]