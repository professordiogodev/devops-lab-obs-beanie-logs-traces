#!/usr/bin/env bash
# Proves the lab left nothing on your machine. Run with: ./verify-teardown.sh
set -u
cd "$(dirname "$0")"
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
check "no container of the project beanie-lt" bash -c '[ -z "$(docker ps -aq --filter label=com.docker.compose.project=beanie-lt)" ]'
check "no volume of the project beanie-lt" bash -c '[ -z "$(docker volume ls -q --filter label=com.docker.compose.project=beanie-lt)" ]'
check "no network of the project beanie-lt" bash -c '[ -z "$(docker network ls -q --filter label=com.docker.compose.project=beanie-lt)" ]'
check "the image beanie:0.1.0 is gone" bash -c '! docker image inspect beanie:0.1.0'
check "the cloned Beanie source is gone from this folder" bash -c '[ ! -d beanie ]'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) on this machine"; else echo "NOT CLEAN: $failn leftover(s). Remove them and run this again."; fi
exit "$failn"
