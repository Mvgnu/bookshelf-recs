#!/bin/sh
# musikconnect tags
# purpose: Install Node.js packages from local tarballs to enable ESLint offline
# inputs: package tarballs in frontend/offline_packages/
# outputs: node_modules directory populated with dependencies
# status: active
# depends_on: npm
# related_docs: README.md, refinement.md

set -e
SCRIPT_DIR="$(dirname "$0")"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
cd "$FRONTEND_DIR"

if [ -d node_modules ]; then
  echo "node_modules already installed"
  exit 0
fi

if [ ! -d offline_packages ]; then
  echo "offline_packages directory missing. Provide npm package .tgz files."
  exit 1
fi

for pkg in offline_packages/*.tgz; do
  npm install "${pkg}" --no-audit --no-fund --prefer-offline
done
