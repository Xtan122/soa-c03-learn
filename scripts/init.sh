#!/usr/bin/env bash
# Create .env from .env.example and fill account/region from the AWS CLI.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  echo "==> .env already exists; not overwriting."
else
  cp .env.example .env
  echo "==> Created .env from .env.example"
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: aws CLI v2 is required." >&2
  exit 1
fi

ACCOUNT="$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)"
REGION="$(aws configure get region 2>/dev/null || true)"
REGION="${REGION:-ap-southeast-1}"

if [[ -z "$ACCOUNT" ]]; then
  echo "WARN: could not read AWS identity. Edit .env manually." >&2
else
  # Portable in-place edit (GNU/BSD).
  python3 - "$ACCOUNT" "$REGION" <<'PY'
import pathlib, sys
account, region = sys.argv[1], sys.argv[2]
p = pathlib.Path(".env")
lines = []
for line in p.read_text().splitlines():
    if line.startswith("LAB_ACCOUNT_ID="):
        line = f"LAB_ACCOUNT_ID={account}"
    elif line.startswith("AWS_REGION="):
        line = f"AWS_REGION={region}"
    lines.append(line)
p.write_text("\n".join(lines) + "\n")
PY
  echo "==> Account: $ACCOUNT   Region: $REGION"
fi

echo
echo "Next:"
echo "  1. Edit .env  -> ALERT_EMAIL (optional), EXPIRY_DATE (default 2026-12-01)"
echo "  2. make doctor"
echo "  3. make bootstrap"
echo "  4. ./bin/lab list"
