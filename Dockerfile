FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Sistema: ffmpeg (Whisper dep), curl, build essentials p/ faster-whisper + claude CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Claude CLI instalado no container (usa OAuth do volume em runtime)
# Installer precisa de bash, não sh
RUN curl -fsSL https://claude.ai/install.sh | bash -s -- latest && \
    ln -sf /root/.local/bin/claude /usr/local/bin/claude && \
    /usr/local/bin/claude --version

WORKDIR /app

# Deps Python
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Código aplicação
COPY app/ /app/

# Porta webhook
EXPOSE 4300

# State/cache volumes mounted via compose
VOLUME ["/data", "/root/.claude", "/var/log/maestro"]

CMD ["python", "-u", "webhook.py"]
