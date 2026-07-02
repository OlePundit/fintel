#!/bin/bash
set -e

echo "==> Copying .env.example to .env (if not exists)"
[ ! -f .env ] && cp .env.example .env && echo "Edit .env with your credentials before continuing." && exit 1

echo "==> Building Docker image"
docker compose build

echo "==> Running DB migrations"
docker compose --profile setup run --rm migrate

echo "==> Starting services"
docker compose up -d postgres redis

echo "==> Waiting for dependencies..."
sleep 5

echo "==> Starting worker + beat"
docker compose up -d worker beat

echo ""
echo "✅ Fintel is running."
echo "   Logs:    docker compose logs -f worker"
echo "   Monitor: docker compose ps"
