#!/bin/bash

echo "Starting Backend Server..."

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
uvicorn main:app --reload --host 0.0.0.0 --port 8000
