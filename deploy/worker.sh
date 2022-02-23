#!/bin/bash

./manage.py compilemessages
celery -A iglo worker -l INFO --concurrency 2 --max-tasks-per-child 50 --max-memory-per-child 200000
