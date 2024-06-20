#!/bin/bash

sleep 5 # wait for postgres

echo "Run migrations..."
alembic upgrade head

echo "Run application..."
uvicorn src.main:app --host 0.0.0.0 --port 8000
