#!/usr/bin/env bash
# Reads Prometheus and Grafana, then kills a service on purpose. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
command -v docker >/dev/null || { echo "docker is not installed." >&2; exit 1; }
exec python3 .lab/ltcheck.py
