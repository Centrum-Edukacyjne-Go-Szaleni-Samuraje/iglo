# IGLO

You need Python 3.9 to run this project. 

Local development (inside Python venv):

```
$ pip install poetry
$ poetry install
$ python iglo/manage.py migrate
$ python iglo/manage.py runserver
```

Docker image/container:

```
$ docker build -f deploy/Dockerfile -t iglo .
$ docker run --name iglo -p 8000:8000 iglo
```