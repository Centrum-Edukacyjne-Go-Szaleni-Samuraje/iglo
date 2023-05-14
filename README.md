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
$ docker run -e POSTGRES_PASSWORD=postgres --name iglo-db -p 15432:5432 -d postgres
$ python3 manage.py migrate
$ python3 manage.py load_seasons ../fixtures/seasons.json
$ CELERY_TASK_ALWAYS_EAGER=True IGLO_DB_PORT=15432 poetry run python3 manage.py runserver
$ python3 manage.py createsuperuser

$ python3 iglo/manage.py makemessages --all  # update translation file, then one can add translations
$ poetry add accurating@latest  # update lib version
$ poetry run python3 iglo/manage.py shell  # Running python with iglo and its libraries
```
