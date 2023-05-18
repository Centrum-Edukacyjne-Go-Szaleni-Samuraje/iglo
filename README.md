# IGLO

You need Python 3.10 to run this project.

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

Lukasz Lew workflow and useful commands:

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
