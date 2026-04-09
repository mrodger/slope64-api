FROM python:3.12-slim

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl wine wine32 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download slope64.exe if not bundled (binary is gitignored)
RUN if [ ! -f bin/slope64.exe ]; then \
      mkdir -p bin && \
      curl -fsSL -o bin/slope64.exe \
        "https://inside.mines.edu/~vgriffit/slope64/slope64.exe"; \
    fi

# Pre-initialise Wine prefix so first request isn't slow
ENV WINEDEBUG=-all
RUN wineboot --init 2>/dev/null || true

EXPOSE 8110
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8110"]
