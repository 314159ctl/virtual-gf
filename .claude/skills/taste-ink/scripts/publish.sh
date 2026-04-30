#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/publish.sh <ink-draft.json>

Requirements:
  - User has explicitly approved publishing
  - JSON file contains: trigger, summary, body
  - Defaults to https://taste.ink (production)
  - Set TASTE_BASE_URL=http://localhost:8000 for local dev
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

draft_file="$1"
if [[ ! -f "$draft_file" ]]; then
  echo "Draft file not found: $draft_file" >&2
  exit 1
fi

BASE_URL="${TASTE_BASE_URL:-https://taste.ink}"

curl -sS -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
  -d @"$draft_file"
