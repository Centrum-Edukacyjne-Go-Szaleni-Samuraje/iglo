# IGLO

You need Python 3.9 to run this project. 

Local development (inside Python venv):

```
$ pip install poetry
$ poetry install
$ python iglo/manage.py migrate
$ python iglo/manage.py runserver
```

Docker build & run:

```
$ ./deploy/build.sh
$ ./deploy/start.sh
```
