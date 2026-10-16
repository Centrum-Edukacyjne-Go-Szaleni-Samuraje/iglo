FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y gettext

RUN pip install poetry>=2.0.0

ADD poetry.lock pyproject.toml /app/

WORKDIR /app

RUN poetry config virtualenvs.create false
RUN poetry config installer.parallel false

RUN poetry install --no-cache --no-root

ADD . /app/

WORKDIR /app/iglo
