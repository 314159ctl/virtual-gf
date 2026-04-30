#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${TASTE_BASE_URL:-https://taste.ink}"

curl -sS "$BASE_URL/me" \
  -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}"
