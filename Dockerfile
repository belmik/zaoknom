FROM python:3.7.5-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN pip install --upgrade pip
RUN pip install pipenv

COPY ./Pipfile /usr/src/app/
COPY ./Pipfile.lock /usr/src/app/
COPY ./manage.py /usr/src/app/
RUN pipenv install --deploy --system 

COPY ./docbox/ /usr/src/app/docbox/
