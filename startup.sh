#!/bin/bash
# Azure Web App startup script (optional)

# Install dependencies
pip install -r requirements.txt

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 600 app:app