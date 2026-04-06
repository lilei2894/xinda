#!/bin/bash

echo "Starting Frontend Server..."

cd xinda-frontend

echo "Installing dependencies..."
npm install

echo "Starting Next.js development server..."
npm run dev
