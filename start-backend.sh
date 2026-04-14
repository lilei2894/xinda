#!/bin/bash

BACKEND_PORT=${BACKEND_PORT:-8000}

echo "Starting Backend Server on port ${BACKEND_PORT}..."

cd xinda-backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating necessary directories..."
mkdir -p uploads data

echo "Starting FastAPI server..."
export BACKEND_PORT
uvicorn main:app --reload --host 0.0.0.0 --port ${BACKEND_PORT}
