FROM python:3.9.7-buster

RUN pip install poetry==1.1.9

ADD poetry.lock pyproject.toml /app/

WORKDIR /app

RUN poetry config virtualenvs.create false

RUN poetry install

ADD . /app/

WORKDIR /app/iglo

EXPOSE 9999

CMD /app/deploy/run.sh
