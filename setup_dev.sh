#!/bin/bash
# Setup script for IGLO development environment

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced, not executed."
    echo "Please run:"
    echo "source setup_dev.sh"
    exit 1
fi

# Ensure script is executed from the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR"

# Use project-specific virtual environment at .venv/
VENV_PATH="$PROJECT_ROOT/.venv"

# Create or activate virtualenv
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtualenv
if [ -f "$VENV_PATH/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Error: Virtual environment activation script not found at $VENV_PATH/bin/activate"
    return 1 2>/dev/null || exit 1  # return if sourced, exit otherwise
fi

# Install poetry if needed
if ! command -v poetry &> /dev/null; then
    echo "Installing poetry..."
    pip install poetry
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Set environment variables
export IGLO_DB_PORT=15432
export CELERY_TASK_ALWAYS_EAGER=True
export ENABLE_PROFILING=False
export FAST_IGOR=True
export IGOR_MAX_STEPS=120  # Maximum steps for IGOR calculations

# Add bin directory to PATH for easier access to the idev script
export PATH="$PROJECT_ROOT/bin:$PATH"
echo "Added $PROJECT_ROOT/bin to PATH. You can now use idev directly."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Starting Docker..."
    sudo systemctl start docker
fi

# Check if Postgres container exists
NEW_DB=false
if docker ps -a --format '{{.Names}}' | grep -q '^iglo-db$'; then
    # Container exists, restart it
    echo "Restarting existing PostgreSQL container..."
    docker restart iglo-db
else
    # Container doesn't exist, create it
    echo "Creating new PostgreSQL container..."
    docker run -e POSTGRES_PASSWORD=postgres --name iglo-db -p ${IGLO_DB_PORT}:5432 -d postgres
    NEW_DB=true
fi

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker exec iglo-db pg_isready -U postgres -q; do
    echo -n "."
    sleep 1
done
echo " Ready!"

# Only run migrations, load fixtures and create superuser for a new database
if [ "$NEW_DB" = true ]; then
    echo "New database detected. Running initial setup..."
    
    # Apply migrations
    echo "Applying migrations..."
    "$PROJECT_ROOT/bin/idev" migrate
    
    # Load sample data
    echo "Loading sample data..."
    "$PROJECT_ROOT/bin/idev" load_seasons fixtures/seasons.json
    
    # Create test superuser
    echo "Creating superuser..."
    echo "from accounts.models import User; User.objects.create_superuser(email='test@test.com', password='test')" | "$PROJECT_ROOT/bin/idev" shell
    
    echo "Database initialization complete."
else
    echo "Using existing database. Skipping migrations and fixture loading."
    echo "idev migrate  # Run database migrations manually"
    echo "idev load_seasons fixtures/seasons.json  # Load sample data manually"
fi

echo ""
echo "Setup complete! Available commands:"
echo ""
echo "# Development server"
echo "idev runserver  # Start the development server"
echo ""
echo "# Database commands"
echo "idev migrate  # Apply database migrations"
echo "idev load_seasons fixtures/seasons.json  # Load sample data"
echo "idev shell  # Open Django shell"
echo ""
echo "# Testing"
echo "idev test iglo  # Run all tests"
echo "idev test league.tests.test_egd_export  # Run specific tests"
echo ""
echo "# Translation"
echo "idev makemessages --all  # Update translation files"
echo ""
echo "# Performance profiling"
echo "export ENABLE_PROFILING=True  # Enable performance profiling"
echo "idev shell  # Then run: from logging import getLogger; logger = getLogger('misc.middleware'); print(logger.dump_profile_stats())"
echo ""
echo "# PostgreSQL access"
echo "docker exec -it iglo-db bash  # Connect to PostgreSQL container"
echo "docker exec -it iglo-db psql -U postgres  # Start PostgreSQL CLI"
echo ""
echo "# Package management"
echo "poetry update --lock  # Update dependencies"
echo "poetry add <package>  # Add a new package"
echo ""
echo "# URLs"
echo "Visit http://127.0.0.1:8000/  # Main site"
echo "Visit http://127.0.0.1:8000/admin/  # Admin interface (login: test@test.com, password: test)"
echo "Visit http://127.0.0.1:8000/league/admin  # League admin interface"
echo ""