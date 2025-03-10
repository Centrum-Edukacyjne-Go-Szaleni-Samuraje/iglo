# IGLO

You need Python 3.10 to run this project.

## Dev workflow and useful commands:

```

# One time setup/install:

systeminstall() {
  # sudo apt -y install $@
  sudo dnf install -y $@
}


systeminstall virtualenv
systeminstall docker
# systeminstall gcc-c++ python3-devel gcc-gfortran openblas-devel lapack-devel cmake pkg-config libopenblas-dev

sudo systemctl start docker
sudo usermod -aG docker $USER
# needs logout+login


# Virtual env

# rm -fr ${HOME}/venv/iglo/
virtualenv ${HOME}/venv/iglo
source ${HOME}/venv/iglo/bin/activate
pip install poetry
poetry install

# Setup

export IGLO_DB_PORT=15432  # envvar needed for manage and other commands
export CELERY_TASK_ALWAYS_EAGER=True
export ENABLE_PROFILING=False  # Uncomment to enable performance profiling
alias manage="poetry run python3 iglo/manage.py"

# Start Postgres

# docker stop iglo-db; docker rm iglo-db
docker ps -a
docker run -e POSTGRES_PASSWORD=postgres --name iglo-db -p ${IGLO_DB_PORT}:5432 -d postgres
manage migrate

# Populate Postgres v1

## Method 1

# We can't commit fixtures/iglo_db.dump to github, due to GPDR law.
ssh apps@iglo.szalenisamuraje.org 'docker exec iglo-production_db_1 pg_dump -Fc -U postgres' > fixtures/iglo_db.dump
cat fixtures/iglo_db.dump | docker exec -i iglo-db pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers

## Method 2

manage load_seasons fixtures/seasons.json

# Run IGLO web server

echo "from accounts.models import User; User.objects.create_superuser(email='test@test.com', password='test')" | poetry run python3 iglo/manage.py shell
# manage createsuperuser # more manual method.

manage runserver

```

Now you can go to `http://127.0.0.1:8000/`

### update translation file, then one can add translations

`manage makemessages --all`

### update lib versions

```
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
poetry update --lock
```

Method for accurating only:
```
poetry cache clear PyPI --all  # sometimes
poetry add accurating@latest
```

### Performance Profiling

IGLO includes a performance profiling system that helps identify and fix bottlenecks like N+1 query issues.
To enable the profiling system:

```bash
export ENABLE_PROFILING=True
```

After enabling profiling and running some pages, you can view a performance summary in the Django shell:

```bash
manage shell
```

```python
from logging import getLogger
logger = getLogger('misc.middleware')
print(logger.dump_profile_stats())  # Shows performance stats summary
```

**Note**: Only enable profiling during development as it adds overhead to request processing.

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
(staging = devel)

Get into dev web docker:
`docker exec -it iglo-staging_web_1 bash`


We get: `bash-5.1#`
`psql -U postgres`

Postgres nice commands:

- `\dt`
- `select * from league_player limit 1;`
- `copy (select nick, rank, igor from league_player) to stdout with csv header;`

### Postgres dumps and restores

Dumps:
```
apps@iglo:~$ docker exec iglo-staging_db_1 pg_dump -Fc -U postgres > iglo_dumps/iglo-staging_db_1.$(date +%Y%m%d).pg_dump
apps@iglo:~$ docker exec iglo-production_db_1 pg_dump -Fc -U postgres > iglo_dumps/iglo-production_db_1.$(date +%Y%m%d).pg_dump
```

Copy prod to dev:
```
apps@iglo:~$ cat iglo_dumps/iglo-production_db_1.(date +%Y%m%d).pg_dump | docker exec -i iglo-staging_db_1 pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers--no-acl
```
NOTE: Double check that `docker exec -i iglo-staging_db_1 ...`, don't run on prod db!


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
