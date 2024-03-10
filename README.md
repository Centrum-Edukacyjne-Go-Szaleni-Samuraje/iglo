# IGLO

You need Python 3.10 to run this project.

## Dev workflow and useful commands:

```
# Virtual env

sudo apt install virtualenv

virtualenv /tmp/iglo
source /tmp/iglo/bin/activate
pip install poetry
poetry install

# Setup

export IGLO_DB_PORT=15432  # envvar needed for manage and other commands
export CELERY_TASK_ALWAYS_EAGER=True
alias manage="poetry run python3 iglo/manage.py"

# docker stop iglo-db; docker rm iglo-db
docker ps -a
docker run -e POSTGRES_PASSWORD=postgres --name iglo-db -p ${IGLO_DB_PORT}:5432 -d postgres
manage migrate
manage load_seasons fixtures/seasons.json
manage createsuperuser

# Run server

manage runserver
```

### update translation file, then one can add translations

`manage makemessages --all`

### update accurating lib version

```
poetry cache clear PyPI --all  # sometimes
poetry add accurating@latest
```

### Celery dev run.
Should not be needed because we run iglo with CELERY_TASK_ALWAYS_EAGER=True

```
export IGOR_MAX_STEPS=120
cd iglo
celery -A iglo worker -l INFO --concurrency 2 --max-tasks-per-child 50 --max-memory-per-child 200000
```

### Shell development

This will run python with iglo:
`manage shell`

And then inside you can run

```python
from importlib import reload
import league.igor as igor

igor.recalculate_igor()

# edit some code and reload to take new code into account:
reload(igor)
igor.recalculate_igor()

```

### Postgres access

```
docker exec -it <container id> bash
psql -U postgres
```


## Important links

- http://localhost:8000/admin/
- http://localhost:8000/league/admin

## ssh debugging

`ssh apps@iglo.szalenisamuraje.org`

Global logs:
`less -R logs.txt`

Iglo dockers on the server:
`docker ps -a | grep iglo`

Get into dev web docker:
`ISW=$(docker ps | grep iglo-production_db_1 | sed 's/ .*//')`
`docker exec -it ${ISW} bash`

We get: `bash-5.1#`
`psql -U postgres`

Postgres nice commands:
`\dt`
`select * from league_player limit 1;`
`copy (select nick, rank, igor from league_player) to stdout with csv header;`

## Old instructions:

Local development (inside Python venv):

```
$ pip install poetry
$ poetry install
$ docker run --name iglo-db -p 5432:5432 -d postgres
$ python iglo/manage.py migrate
$ python iglo/manage.py runserver
```

Docker build & run:

```
$ ./deploy/build.sh
$ ./deploy/start.sh
```

Lukasz Lew's workflow and useful commands:

```
# Startup.
$ docker run -e POSTGRES_PASSWORD=postgres --name iglo-db -p 15432:5432 -d postgres
$ python3 manage.py migrate  # maybe prefix with 'potery run'
$ python3 manage.py load_seasons ../fixtures/seasons.json
$ CELERY_TASK_ALWAYS_EAGER=True IGLO_DB_PORT=15432 poetry run python3 manage.py runserver
$ python3 manage.py createsuperuser

# update translation file, then one can add translations
$ python3 iglo/manage.py makemessages --all

# update lib version
$ poetry cache clear PyPI --all  # sometimes
$ poetry add accurating@latest

# Running python with iglo and its libraries
$ poetry run python3 manage.py shell

# Celery dev run.
$ IGOR_MAX_STEPS=120 IGLO_DB_PORT=15432 celery -A iglo worker -l INFO --concurrency 2 --max-tasks-per-child 50 --max-memory-per-child 200000
```
