#!/usr/bin/env bash
# Publish episodes: compress new audio locally, rebuild feed, commit, push.
# Compressing BEFORE push keeps files under GitHub's 100MB limit.
#
# Usage:
#   ./publish.sh                 # auto commit message
#   ./publish.sh "Episode title" # custom commit message
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Compressing new episodes..."
python3 compress.py

echo "==> Rendering episode artwork..."
python3 episode_art.py

echo "==> Rebuilding feed..."
python3 generate.py

if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "Nothing to publish (no changes)."
  exit 0
fi

msg="${1:-Add/update episodes}"
git add -A
git commit -q -m "$msg"

echo "==> Pushing..."
# feed.xml is generated; on conflict always prefer our freshly-built copy.
for attempt in 1 2 3; do
  git push -q origin master 2>/dev/null && break
  echo "   remote moved, rebasing (attempt $attempt)..."
  git pull -q --rebase -X ours --autostash origin master 2>&1 | tail -1 || true
done

echo "==> Done. Feed: $(python3 -c "import json;print(json.load(open('config.json'))['base_url']+'/feed.xml')")"
echo "    Live in ~1 min."
