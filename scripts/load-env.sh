#!/usr/bin/env bash
# Shared environment loader. Source this, never execute it.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT

if [[ ! -f "$ROOT/.env" ]]; then
  echo "ERROR: .env not found. Run: make init" >&2
  exit 1
fi

# Preserve explicit CLI overrides for safety flags. Otherwise `.env` with
# ALLOW_BREAK=no would silently override `ALLOW_BREAK=yes ./bin/lab break`.
_ENV_ALLOW_BREAK="${ALLOW_BREAK-}"
_ENV_CONFIRM_BREAK="${CONFIRM_BREAK-}"
_ENV_CONFIRM_RESET="${CONFIRM_RESET-}"
_ENV_CONFIRM_DESTROY="${CONFIRM_DESTROY-}"

# shellcheck disable=SC1091
set -a
source "$ROOT/.env"
set +a

[[ -n "$_ENV_ALLOW_BREAK" ]] && export ALLOW_BREAK="$_ENV_ALLOW_BREAK"
[[ -n "$_ENV_CONFIRM_BREAK" ]] && export CONFIRM_BREAK="$_ENV_CONFIRM_BREAK"
[[ -n "$_ENV_CONFIRM_RESET" ]] && export CONFIRM_RESET="$_ENV_CONFIRM_RESET"
[[ -n "$_ENV_CONFIRM_DESTROY" ]] && export CONFIRM_DESTROY="$_ENV_CONFIRM_DESTROY"

: "${AWS_REGION:?AWS_REGION missing in .env}"
: "${LAB_ACCOUNT_ID:?LAB_ACCOUNT_ID missing in .env. Run make init}"
: "${LAB_PREFIX:?LAB_PREFIX missing in .env}"
: "${EXPIRY_DATE:?EXPIRY_DATE missing in .env}"
: "${CORE_STACK:=${LAB_PREFIX}-core}"
: "${APP_STACK:=${LAB_PREFIX}-app}"

export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_PAGER=""

# All resources get the same tags. CloudFormation also receives them.
export LAB_TAGS="Project=${LAB_PREFIX} Lab=soa-c03 ExpiryDate=${EXPIRY_DATE} Owner=learner"

mkdir -p "$ROOT/var" "$ROOT/progress"
