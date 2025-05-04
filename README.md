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
idev runserver
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
idev shell
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

#### Copy from Production for Local Development
Use the provided script to copy production data to your local environment:

```bash
# Run from your local machine:
./bin/copy-prod-data.sh
```

This script:
1. Creates a backup of your current local database
2. Fetches the production database dump
3. Restores it to your local development environment

#### Copy from Production to Staging Server
On the server environment, use the original script:

```bash
# Run on the server only:
./copy_iglo_db_prod_to_dev.sh
```

This server script:
1. Creates backup dumps of both staging and production databases 
2. Copies production data to the staging environment

⚠️ **WARNING**: Always verify which environment you're working with and which databases will be affected. Database restore operations will overwrite existing data.

### Docker Deployment
To build and deploy using Docker:

```bash
./deploy/build.sh
./deploy/start.sh
```
