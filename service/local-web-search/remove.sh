#!/usr/bin/env bash
set -euo pipefail

error_exit() {
  echo "Error: $1" >&2
  exit 1
}

# ensure conda is available
command -v conda >/dev/null 2>&1 || error_exit "conda not found; please install Anaconda or Miniconda."

# locate environment.yml
ENV_YML="environment.yml"
[[ -f "$ENV_YML" ]] || error_exit "environment.yml not found in current directory."

# extract env name
ENV_NAME=$(grep -E '^name:' "$ENV_YML" | awk '{print $2}')
[[ -n "$ENV_NAME" ]] || error_exit "Could not extract 'name' from $ENV_YML."

# check and remove
if conda env list | awk '{print $1}' | grep -xq "$ENV_NAME"; then
  echo "Removing Conda environment '$ENV_NAME'..."
  conda env remove -n "$ENV_NAME" --yes \
    || error_exit "Failed to remove environment '$ENV_NAME'."
  echo "Environment '$ENV_NAME' removed."
else
  echo "Conda environment '$ENV_NAME' does not exist; nothing to remove."
fi
