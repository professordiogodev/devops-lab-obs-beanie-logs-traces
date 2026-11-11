#!/usr/bin/env bash
# Clones Beanie, builds the image. Run: ./setup.sh
set -u
cd "$(dirname "$0")"
for c in docker git curl python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo "Docker is not running."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is missing (docker compose version)."; exit 1; }
[ -d beanie ] || git clone -q -c advice.detachedHead=false --depth 1 --branch v0.1.0 https://github.com/professordiogodev/beanie.git beanie || { echo "could not clone beanie"; exit 1; }
docker compose -f compose.beanie.yaml build -q || { echo "image build failed"; exit 1; }
echo "Ready. Start Beanie alone:  docker compose -f compose.beanie.yaml up -d      (http://localhost:8000/api/menu)"
echo "Then write the TODO files and start everything: docker compose -f compose.beanie.yaml -f compose.grafana.yaml -f compose.observability.yaml up -d"
