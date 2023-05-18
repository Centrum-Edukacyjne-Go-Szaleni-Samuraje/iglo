FROM python:3.10.5-buster

RUN apt-get update && apt-get install -y gettext

RUN pip install poetry==1.4.2

ADD poetry.lock pyproject.toml /app/

WORKDIR /app

RUN poetry config virtualenvs.create false

RUN poetry install

ADD . /app/

WORKDIR /app/iglo
