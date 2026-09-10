#!/usr/bin/env bash
set -e

echo "[*] Granting local container access to host X11 display..."
xhost +local:docker > /dev/null

echo "[*] Ensuring permissions for SQLite volume..."
mkdir -p data imports
sudo chown -R 1000:1000 data imports

echo "[*] Building Flux RDM..."
docker compose build

echo "[*] Starting Flux RDM..."
docker compose run --rm flux-rdm
