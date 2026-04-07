#!/bin/bash
# Download slope64.exe from Griffiths' page and set up the environment.
set -e

mkdir -p bin
echo "Downloading slope64.exe from inside.mines.edu..."
curl -o bin/slope64.exe "https://inside.mines.edu/~vgriffit/slope64/slope64.exe"
echo "Downloaded: $(ls -lh bin/slope64.exe | awk '{print $5}')"

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Done. Run with: uvicorn server:app --host 0.0.0.0 --port 8110"
