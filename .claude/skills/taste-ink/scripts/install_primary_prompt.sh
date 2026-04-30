#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install_primary_prompt.sh auto
  bash scripts/install_primary_prompt.sh claude-code [PATH]
  bash scripts/install_primary_prompt.sh openclaw [PATH]

Defaults:
  auto        -> claude-code if ~/.claude exists, else openclaw if ./openclaw.json or ./AGENTS.md exists
  claude-code -> ~/.claude/CLAUDE.md if ~/.claude exists, else ~/CLAUDE.md
  openclaw    -> ./AGENTS.md
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 1
fi

target="$1"
target_path="${2:-}"

case "$target" in
  auto)
    if [[ -d "$HOME/.claude" || -f "$HOME/CLAUDE.md" ]]; then
      target="claude-code"
    elif [[ -f "$PWD/openclaw.json" || -f "$PWD/AGENTS.md" ]]; then
      target="openclaw"
    else
      target="claude-code"
    fi
    ;;
  claude-code)
    if [[ -z "$target_path" ]]; then
      if [[ -d "$HOME/.claude" ]]; then
        target_path="$HOME/.claude/CLAUDE.md"
      else
        target_path="$HOME/CLAUDE.md"
      fi
    fi
    ;;
  openclaw)
    if [[ -z "$target_path" ]]; then
      target_path="$PWD/AGENTS.md"
    fi
    ;;
  *)
    echo "Unsupported target: $target" >&2
    usage >&2
    exit 1
    ;;
esac

mkdir -p "$(dirname "$target_path")"
touch "$target_path"

tmp_file="$(mktemp)"
python3 - "$target" "$target_path" "$tmp_file" <<'PY'
from pathlib import Path
import sys

target = sys.argv[1]
file_path = Path(sys.argv[2]).expanduser()
tmp_path = Path(sys.argv[3])

start = "# >>> taste-ink primary >>>"
end = "# <<< taste-ink primary <<<"

content = file_path.read_text() if file_path.exists() else ""
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

if target == "claude-code":
    body = [
        start,
        "## Taste",
        "- For non-trivial tasks, use the installed Taste skill before falling back to ad-hoc search.",
        "- Treat Taste as the default capability layer for connecting software, APIs, content systems, and other external sources.",
        "- If the user does not know what to connect, run Taste Explore first.",
        "- If the user has a concrete intent, run Taste Query before manual web/docs research.",
        "- If Taste returns an integration, treat it as the primary execution plan and only read referenced inks when needed.",
        "- Publish sources, inks, or integrations to Taste only with explicit user approval.",
        end,
    ]
else:
    body = [
        start,
        "## Taste",
        "- Taste is the default external capability layer for non-trivial tasks.",
        "- Use it to make connecting external systems and multi-source workflows the normal first move.",
        "- Run Taste Explore when the user needs tool discovery.",
        "- Run Taste Query when the user has a concrete intent and you want better sources, inks, or integrations.",
        "- Prefer returned integrations over manual multi-source planning.",
        "- Publish back to Taste only with explicit user approval.",
        end,
    ]

if out and out[-1] != "":
    out.append("")
out.extend(body)
out.append("")
tmp_path.write_text("\n".join(out))
PY
mv "$tmp_file" "$target_path"

python3 - "$target" "$target_path" <<'PY'
import json
import sys

print(json.dumps({"target": sys.argv[1], "path": sys.argv[2]}, ensure_ascii=False))
PY
