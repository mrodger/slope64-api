FROM python:3.12-slim

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends wine wine32 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-initialise Wine prefix so first request isn't slow
RUN WINEDEBUG=-all wineboot --init 2>/dev/null || true

EXPOSE 8110
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8110"]
