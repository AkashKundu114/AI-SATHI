#!/usr/bin/env bash
set -e

# Install Node dependencies
echo "Installing npm dependencies..."
npm ci

# Build the frontend assets
echo "Building frontend with Vite..."
npm run build

# Copy the built assets to the backend static directory
DEST_DIR="../backend/frontend/dist"
if [ -d "$DEST_DIR" ]; then
  echo "Cleaning old assets in $DEST_DIR"
  rm -rf "$DEST_DIR/*"
fi

echo "Copying new assets to $DEST_DIR"
mkdir -p "$DEST_DIR"
cp -r dist/* "$DEST_DIR/"

echo "Frontend build complete."
