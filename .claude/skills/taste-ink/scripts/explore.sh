#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/explore.sh "user context summary"
  bash scripts/explore.sh --limit 3 "user context summary"
  bash scripts/explore.sh --file explore-payload.json
EOF
}

BASE_URL="${TASTE_BASE_URL:-https://taste.ink}"
limit=5
payload_file=""
context=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --limit)
      limit="${2:-}"
      shift 2
      ;;
    --file)
      payload_file="${2:-}"
      shift 2
      ;;
    *)
      context="${context:+$context }$1"
      shift
      ;;
  esac
done

if [[ -n "$payload_file" ]]; then
  curl -sS -X POST "$BASE_URL/explore" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
    -d @"$payload_file"
  exit 0
fi

if [[ -z "$context" ]]; then
  usage >&2
  exit 1
fi

payload="$(
  python3 - "$context" "$limit" <<'PY'
import json
import sys

print(json.dumps({"context": sys.argv[1].strip(), "limit": int(sys.argv[2])}, ensure_ascii=False))
PY
)"

curl -sS -X POST "$BASE_URL/explore" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
  -d "$payload"
