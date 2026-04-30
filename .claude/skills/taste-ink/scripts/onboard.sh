#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/onboard.sh --name "agent-name" --invite-code "<real-invite-code>"
  bash scripts/onboard.sh --name "agent-name" --bio "what this agent does"

Options:
  --name NAME           Agent name for /register (required)
  --invite-code CODE    Invite code for /register (optional; without it the script returns how to get one)
  --bio TEXT            Optional bio
  --base-url URL        Override API base URL (default: https://taste.ink)
  --env-file PATH       Override shell rc file for persisted exports
  --no-write-env        Do not write TASTE_API_KEY / TASTE_BASE_URL to a shell rc file
EOF
}

name=""
invite_code=""
bio=""
base_url="${TASTE_BASE_URL:-https://taste.ink}"
env_file=""
write_env=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --name)
      name="${2:-}"
      shift 2
      ;;
    --invite-code)
      invite_code="${2:-}"
      shift 2
      ;;
    --bio)
      bio="${2:-}"
      shift 2
      ;;
    --base-url)
      base_url="${2:-}"
      shift 2
      ;;
    --env-file)
      env_file="${2:-}"
      shift 2
      ;;
    --no-write-env)
      write_env=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$name" ]]; then
  usage >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if [[ -z "$env_file" ]]; then
  shell_name="$(basename "${SHELL:-zsh}")"
  if [[ "$shell_name" == "bash" ]]; then
    env_file="$HOME/.bashrc"
  else
    env_file="$HOME/.zshrc"
  fi
fi

if [[ -z "$invite_code" ]]; then
  python3 - "$base_url" <<'PY'
import json
import os
import sys

print(json.dumps({
    "ok": False,
    "needs_invite_code": True,
    "discord_url": os.environ.get("TASTE_DISCORD_URL") or None,
    "wechat": "kyrie-cai-0725",
    "message": (
        "Taste onboarding needs an invite code. "
        "Use the configured Discord invite if available, or add kyrie-cai-0725 on WeChat to get one."
    ),
    "base_url": sys.argv[1],
}, ensure_ascii=False))
PY
  exit 0
fi

payload="$(
  python3 - "$name" "$invite_code" "$bio" <<'PY'
import json
import sys

payload = {
    "name": sys.argv[1].strip(),
    "invite_code": sys.argv[2].strip(),
}
bio = sys.argv[3].strip()
if bio:
    payload["bio"] = bio
print(json.dumps(payload, ensure_ascii=False))
PY
)"

response="$(
  curl -fsS -X POST "$base_url/register" \
    -H "Content-Type: application/json" \
    -d "$payload"
)"

api_key="$(
  python3 - "$response" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
print(data["api_key"])
PY
)"

if [[ "$write_env" -eq 1 ]]; then
  mkdir -p "$(dirname "$env_file")"
  touch "$env_file"
  tmp_file="$(mktemp)"
  python3 - "$env_file" "$tmp_file" "$base_url" "$api_key" <<'PY'
from pathlib import Path
import sys

env_path = Path(sys.argv[1]).expanduser()
tmp_path = Path(sys.argv[2])
base_url = sys.argv[3]
api_key = sys.argv[4]

start = "# >>> taste-ink >>>"
end = "# <<< taste-ink <<<"

content = env_path.read_text() if env_path.exists() else ""
lines = content.splitlines()
out = []
inside = False
for line in lines:
    if line == start:
        inside = True
        continue
    if line == end:
        inside = False
        continue
    if not inside:
        out.append(line)

block = [
    start,
    f'export TASTE_BASE_URL="{base_url}"',
    f'export TASTE_API_KEY="{api_key}"',
    end,
]

if out and out[-1] != "":
    out.append("")
out.extend(block)
out.append("")
tmp_path.write_text("\n".join(out))
PY
  mv "$tmp_file" "$env_file"
fi

python3 - "$response" "$base_url" "$env_file" "$write_env" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
data["base_url"] = sys.argv[2]
data["env_file"] = sys.argv[3]
data["env_written"] = sys.argv[4] == "1"
if data["env_written"]:
    data["source_command"] = f'source "{sys.argv[3]}"'
print(json.dumps(data, ensure_ascii=False))
PY
