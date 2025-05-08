#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r banking/requirements.txt

# Add the project directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/opt/render/project/src

# Collect static files
cd banking
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate 