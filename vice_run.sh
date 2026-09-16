#!/bin/sh
set -eu
PRG=${1:-ARPSID_V965_TEASER_RC1.prg}
if command -v x64sc >/dev/null 2>&1; then
  x64sc "$PRG"
elif command -v x64 >/dev/null 2>&1; then
  x64 "$PRG"
else
  echo "VICE x64sc/x64 not found."
  exit 1
fi
