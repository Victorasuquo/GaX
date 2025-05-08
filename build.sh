#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r banking/requirements.txt

# Collect static files
cd banking
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate 