#!/bin/bash

# Go to project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Load environment variables from root .env (not src/.env)
export $(grep -v '^#' .env | xargs)

# Run the Python app
python3 src/app.py

# Deactivate after running (optional)
deactivate