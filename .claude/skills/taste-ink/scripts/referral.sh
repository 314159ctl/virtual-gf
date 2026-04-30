#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/referral.sh --url "https://example.com/post" --platform "xhs" --summary "What was shared"
  bash scripts/referral.sh --file referral-draft.json
EOF
}

BASE_URL="${TASTE_BASE_URL:-https://taste.ink}"
payload_file=""
url=""
platform=""
summary=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --file)
      payload_file="${2:-}"
      shift 2
      ;;
    --url)
      url="${2:-}"
      shift 2
      ;;
    --platform)
      platform="${2:-}"
      shift 2
      ;;
    --summary)
      summary="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$payload_file" ]]; then
  curl -sS -X POST "$BASE_URL/referral" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
    -d @"$payload_file"
  exit 0
fi

if [[ -z "$url" || -z "$platform" ]]; then
  usage >&2
  exit 1
fi

payload="$(
  python3 - "$url" "$platform" "$summary" <<'PY'
import json
import sys

payload = {
    "url": sys.argv[1].strip(),
    "platform": sys.argv[2].strip(),
}
summary = sys.argv[3].strip()
if summary:
    payload["content_summary"] = summary
print(json.dumps(payload, ensure_ascii=False))
PY
)"

curl -sS -X POST "$BASE_URL/referral" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${TASTE_API_KEY:?Set TASTE_API_KEY env var}" \
  -d "$payload"
