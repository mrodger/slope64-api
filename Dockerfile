FROM postgis/postgis:16-3.4

# Install Python, Wine, supervisord, curl
# postgis:16-3.4 is Debian Bullseye — python3 = 3.9, sufficient for FastAPI
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    curl supervisor \
    && dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends wine wine32 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Download slope64.exe if not bundled
RUN if [ ! -f bin/slope64.exe ]; then \
      mkdir -p bin && \
      curl -fsSL -o bin/slope64.exe \
        "https://inside.mines.edu/~vgriffit/slope64/slope64.exe"; \
    fi

# Pre-initialise Wine prefix so first request isn't slow
ENV WINEDEBUG=-all
RUN wineboot --init 2>/dev/null || true

# Copy supervisord config
COPY supervisord.conf /etc/supervisord.conf

# Entrypoint initialises postgres on first boot then starts supervisord
COPY entrypoint.sh /entrypoint.sh
COPY start_api.sh /start_api.sh
RUN chmod +x /entrypoint.sh /start_api.sh

EXPOSE 8110

ENTRYPOINT ["/entrypoint.sh"]
