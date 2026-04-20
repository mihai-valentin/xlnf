#!/usr/bin/env bash
# Stamp the footer of index.html with the current HEAD commit hash, then commit.
# Intentionally stamps *parent* commit (rev-parse HEAD before stamping) because
# a commit cannot contain its own hash — that's fine, the footer refers to the
# source state the build was made from.
#
# Usage: ./build.sh

set -euo pipefail

cd "$(dirname "$0")"

HASH=$(git rev-parse --short=8 HEAD | tr '[:lower:]' '[:upper:]')

if ! grep -qE '# build 0x[A-Fa-f0-9]+' index.html; then
  echo "error: no '# build 0x...' token found in index.html" >&2
  exit 1
fi

sed -i.bak -E "s/# build 0x[A-Fa-f0-9]+/# build 0x${HASH}/" index.html
rm -f index.html.bak

if git diff --quiet index.html; then
  echo "footer already at 0x${HASH}, nothing to commit."
  exit 0
fi

git add index.html
git commit -m "build: stamp footer with 0x${HASH}"
echo "stamped 0x${HASH} and committed."
