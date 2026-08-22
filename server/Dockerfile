# Dockerfile for APK Sentinel Backend
# Includes Python 3.11+, Java JRE (for jadx), and jadx decompilation toolchain.

FROM python:3.11-slim

# Install system dependencies & JRE (required by jadx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install jadx release
ENV JADX_VERSION=1.5.1
RUN wget -q "https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip" -O /tmp/jadx.zip \
    && mkdir -p /opt/jadx \
    && unzip -q /tmp/jadx.zip -d /opt/jadx \
    && rm /tmp/jadx.zip \
    && ln -s /opt/jadx/bin/jadx /usr/local/bin/jadx

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY app/ ./app/
COPY fixtures/ ./fixtures/
COPY scripts/ ./scripts/

# Create runtime storage directories
RUN mkdir -p storage/apks storage/decompiled storage/reports

EXPOSE 8000

ENV PORT=8000
ENV DATABASE_URL=sqlite:///./sentinel.db
ENV STORAGE_DIR=./storage
ENV JADX_PATH=jadx

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
