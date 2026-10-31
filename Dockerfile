# Build from the repository root: docker build -t sih26263 .
FROM node:22-bookworm-slim AS web-build
WORKDIR /workspace/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS api-deps
WORKDIR /workspace
COPY services/api/requirements.txt services/api/requirements.lock ./services/api/
RUN pip install --no-cache-dir -r services/api/requirements.txt -c services/api/requirements.lock

FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home-dir /workspace app
COPY --from=api-deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
WORKDIR /workspace
COPY services/api/ ./services/api/
COPY --from=web-build /workspace/apps/web/package.json ./apps/web/package.json
COPY --from=web-build /workspace/apps/web/node_modules ./apps/web/node_modules
COPY --from=web-build /workspace/apps/web/.next ./apps/web/.next
RUN mkdir -p /workspace/apps/web/.next/cache && chown -R app:app /workspace/apps/web/.next/cache
USER app
ENV NODE_ENV=production PYTHONUNBUFFERED=1
EXPOSE 3000 8000
CMD ["bash", "-c", "cd /workspace/services/api && python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-proxy-headers & api_pid=$!; cd /workspace/apps/web && node node_modules/next/dist/bin/next start --hostname 0.0.0.0 --port 3000 & web_pid=$!; trap 'kill $api_pid $web_pid 2>/dev/null || true' TERM INT; wait -n $api_pid $web_pid; status=$?; kill $api_pid $web_pid 2>/dev/null || true; wait || true; exit $status"]
