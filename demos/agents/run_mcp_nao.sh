#!/usr/bin/env bash
set -euo pipefail

cd /Users/landon/Desktop/SAIL
source .venv/bin/activate

# If provided, always store --nao-ip into NAO_IP (overrides existing NAO_IP).
# If NAO_IP is still unset afterwards, error.
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --nao-ip)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "ERROR: --nao-ip requires a value." >&2
        exit 2
      fi
      export NAO_IP="$2"
      shift 2
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ -z "${NAO_IP:-}" ]]; then
  echo "ERROR: NAO_IP is not set. Set NAO_IP or pass --nao-ip <ip>." >&2
  exit 2
fi

python sic_applications/demos/agents/mcp_nao.py