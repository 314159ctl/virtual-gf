#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/query.sh "problem + context + constraints"
  bash scripts/query.sh --file query-payload.json

Notes:
  - Defaults to https://taste.ink (production)
  - Set TASTE_BASE_URL=http://localhost:8000 for local dev
EOF
}

BASE_URL="${TASTE_BASE_URL:-https://taste.ink}"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--file" ]]; then
  if [[ $# -ne 2 ]]; then
    usage >&2
    exit 1
  fi

  curl -sS -X POST "$BASE_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
    -d @"$2"
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to JSON-encode the query string. Use --file as a fallback." >&2
  exit 1
fi

payload="$(
  python3 - "$@" <<'PY'
import json
import sys

query = " ".join(sys.argv[1:]).strip()
print(json.dumps({"query": query}, ensure_ascii=False))
PY
)"

curl -sS -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
  -d "$payload"
