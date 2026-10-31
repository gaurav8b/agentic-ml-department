#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="$ROOT/.source/agentic-ml-department-source.tar.xz"

if [[ ! -s "$ARCHIVE" ]]; then
  echo "Missing source archive: $ARCHIVE" >&2
  exit 1
fi

(cd "$ROOT" && sha256sum -c CHECKSUMS.txt)
tar -xJf "$ARCHIVE" -C "$ROOT"
echo "Source extracted to: $ROOT/agentic-ml-department"
echo "Next: cd agentic-ml-department && cp .env.example .env && docker compose up --build -d"
