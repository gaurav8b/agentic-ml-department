#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARTS="$ROOT/.source/parts"
ARCHIVE="$ROOT/.source/agentic-ml-department-source.tar.xz"

if [[ ! -d "$PARTS" ]] || ! compgen -G "$PARTS/*.b64" >/dev/null; then
  echo "Missing .source/parts/*.b64. Run this script from the repository root." >&2
  exit 1
fi

cat "$PARTS"/*.b64 | tr -d '\r\n ' | base64 -d > "$ARCHIVE"
(cd "$ROOT" && sha256sum -c CHECKSUMS.txt)
tar -xJf "$ARCHIVE" -C "$ROOT"
echo "Source extracted to: $ROOT/agentic-ml-department"
echo "Next: cd agentic-ml-department && cp .env.example .env && docker compose up --build -d"
