FROM node:22-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY studio/ ./studio/
COPY index.html main.js styles.css vite.config.ts tsconfig*.json tailwind.config.js postcss.config.js ./
COPY src/ ./src/
COPY shared/ ./shared/
COPY assets/ ./assets/
COPY fonts/ ./fonts/
RUN npm run build

FROM node:22-bookworm-slim AS harness
RUN npm install --global @qloo/qloo-harness@0.1.26

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
COPY --from=harness /usr/local/bin/node /usr/local/bin/node
COPY --from=harness /usr/local/lib/node_modules/@qloo /usr/local/lib/node_modules/@qloo
ENV QLOO_HARNESS_PATH=/usr/local/lib/node_modules/@qloo/qloo-harness \
    QLOO_BASE_URL=https://hackathon.api.qloo.com \
    QLOO_TRUSTED_BASE_URL=https://hackathon.api.qloo.com \
    CULTUREFORGE_STATIC_DIR=/app/dist \
    CULTUREFORGE_CACHE_DIR=/data/cache \
    CULTUREFORGE_DB=/data/platform.db \
    CULTUREFORGE_PROVIDER=qloo \
    PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --uid 10001 cultureforge && \
    mkdir -p /data/cache && chown -R cultureforge:cultureforge /data
COPY backend/ ./backend/
COPY shared/ ./shared/
COPY scripts/qloo_exec.mjs ./scripts/qloo_exec.mjs
COPY --from=web /app/dist ./dist
USER cultureforge
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health', timeout=4)"
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
