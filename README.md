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

Running python with iglo and its libraries:

```
$ poetry run python3 iglo/manage.py shell
```
