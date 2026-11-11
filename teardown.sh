#!/usr/bin/env bash
# Removes the lab's containers, volumes, networks, image and cloned source. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")"
docker compose -f compose.beanie.yaml -f compose.grafana.yaml -f compose.observability.yaml down -v --remove-orphans 2>&1 | tail -3
docker compose -f compose.beanie.yaml down -v --remove-orphans >/dev/null 2>&1
docker image rm beanie:0.1.0 >/dev/null 2>&1 && echo "removed the image beanie:0.1.0"
rm -rf beanie .env
echo "Now run ./verify-teardown.sh"
