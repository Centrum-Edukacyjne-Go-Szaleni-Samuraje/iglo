# IGLO

You need Python 3.10 to run this project.

## Development Setup

The easiest way to set up the development environment is by using the provided setup script:

```bash
# Install system dependencies if you haven't already
sudo apt install -y python3-venv docker   # For Ubuntu/Debian
# OR
sudo dnf install -y python3-venv docker   # For Fedora/RHEL

# You might need these additional packages for certain dependencies:
# sudo apt/dnf install -y gcc gcc-c++ python3-devel gcc-gfortran openblas-devel lapack-devel cmake pkg-config libopenblas-dev

# Ensure Docker is running
sudo systemctl start docker
sudo usermod -aG docker $USER  # May require logout+login to take effect

# Run the setup script (must be sourced, not executed)
source setup_dev.sh
```

The setup script will:
1. Create a virtual environment in `.venv/`
2. Install all dependencies
3. Set environment variables
4. Start PostgreSQL in Docker
5. Apply migrations (for new databases)
6. Create a test superuser (for new databases)

After setup, you can run the development server:
```bash
manage.sh runserver
```

The setup script will print a comprehensive list of available commands after completion.

## Advanced Topics

### Celery Development
Celery is configured to run tasks eagerly by default (set with `CELERY_TASK_ALWAYS_EAGER=True`). If you need to run Celery as a separate worker:

```bash
cd iglo
celery -A iglo worker -l INFO --concurrency 2 --max-tasks-per-child 50 --max-memory-per-child 200000
```

### Interactive Shell Development
You can use Django's shell for interactive development:

```bash
manage.sh shell
```

Example of working with the IGOR system:
```python
from importlib import reload
import league.igor as igor

igor.recalculate_igor()

# After editing code, reload the module:
reload(igor)
igor.recalculate_igor()
```

### Package Management
To update dependencies:
```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
poetry update --lock
```

For specific packages:
```bash
poetry cache clear PyPI --all  # If needed
poetry add <package-name>@latest
```


## Server Administration

### Important URLs
- http://localhost:8000/ - Main application
- http://localhost:8000/admin/ - Django admin interface
- http://localhost:8000/league/admin - League admin interface

### PostgreSQL Commands
Useful PostgreSQL commands when connected to the database:
```sql
\dt                                           -- List tables
SELECT * FROM league_player LIMIT 1;          -- View first player
\copy (SELECT nick, rank, igor FROM league_player) TO stdout WITH CSV HEADER;  -- Export data
```

### Remote Server Access
For debugging on the production server:

```bash
# Connect to the server
ssh apps@iglo.szalenisamuraje.org

# View logs
less -R logs.txt

# Check Docker containers
docker ps -a | grep iglo  # Note: staging = devel

# View worker logs
docker logs iglo-staging_worker_1

# Access development web container
docker exec -it iglo-staging_web_1 bash
```

### Database Dumps and Restores

#### IMPORTANT: GDPR Compliance
We can't commit database dumps to GitHub due to GDPR regulations. Always handle data exports carefully.

#### Copy from Production
To copy production data to development:

```bash
# On the server:
ssh apps@iglo.szalenisamuraje.org 'docker exec iglo-production_db_1 pg_dump -Fc -U postgres' > fixtures/iglo_db.dump

# Then locally:
cat fixtures/iglo_db.dump | docker exec -i iglo-db pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers
```

#### Creating and Managing Dumps
```bash
# Create dumps with date stamps
docker exec iglo-staging_db_1 pg_dump -Fc -U postgres > iglo_dumps/iglo-staging_db_1.$(date +%Y%m%d).pg_dump
docker exec iglo-production_db_1 pg_dump -Fc -U postgres > iglo_dumps/iglo-production_db_1.$(date +%Y%m%d).pg_dump

# Copy between environments
cat iglo_dumps/iglo-production_db_1.$(date +%Y%m%d).pg_dump | docker exec -i iglo-staging_db_1 pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers --no-acl
```

⚠️ **WARNING**: Always double-check container names to avoid accidentally overwriting production data. Verify that you're running commands on the intended environment.

### Docker Deployment
To build and deploy using Docker:

```bash
./deploy/build.sh
./deploy/start.sh
```
