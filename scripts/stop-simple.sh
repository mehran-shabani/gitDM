#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.simple.yml down -v
