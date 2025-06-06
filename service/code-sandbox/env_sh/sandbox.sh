#!/bin/bash
set -eux

# -----------------------------------------------------------------------------
# This script downloads, builds, and installs SDUOJ’s sandbox into /opt/sandbox.
# It assumes all build dependencies (e.g. build-essential, libseccomp-dev,
# curl, unzip) are already present on the system.
# Usage: bash install_sandbox.sh
# -----------------------------------------------------------------------------

# 1. Create a temporary working directory
TEMP_DIR="$(mktemp -d)"
cd "$TEMP_DIR"

# 2. Download the latest SDUOJ sandbox source as a ZIP and unpack it
curl -fL "https://codeload.github.com/yhf2000/sduoj-sandbox/zip/master" -o sandbox.zip
unzip -o sandbox.zip
# The extracted folder name typically starts with "sduoj-sandbox-"
cd sduoj-sandbox*

# 3. Build the sandbox
make
make install


# 5. Clean up temporary directory
cd /
rm -rf "$TEMP_DIR"

echo "Installation complete: sandbox is available under /opt/sduoj-sandbox/bin."
