FROM postgis/postgis:16-3.4

# Install Python 3.12, Wine, supervisord, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3-pip \
    curl supervisor \
    gnupg software-properties-common \
    && dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends wine wine32 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

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
