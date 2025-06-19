#!/usr/bin/env bash
# filepath: /home/liuyu/Agent/AgentHubBackend/service/ocr-service/install.sh
set -euo pipefail

error_exit() {
  echo "Error: $1" >&2
  exit 1
}

# 1. Verify that conda is installed
command -v conda >/dev/null 2>&1 || error_exit "conda not found; please install Anaconda or Miniconda first."

# 2. Ensure environment.yml exists in the current directory
ENV_YML="environment.yml"
[[ -f "$ENV_YML" ]] || error_exit "Could not find $ENV_YML in the current directory."

# 3. Extract the environment name from environment.yml
ENV_NAME=$(grep -E '^name:' "$ENV_YML" | awk '{print $2}')
[[ -n "$ENV_NAME" ]] || error_exit "Could not extract 'name' field from $ENV_YML."

echo "Environment name: $ENV_NAME"

# 4. Check if the environment already exists
if conda env list | awk '{print $1}' | grep -xq "$ENV_NAME"; then
  echo "Conda environment '$ENV_NAME' already exists; skipping creation."
else
  echo "Creating Conda environment '$ENV_NAME' from $ENV_YML..."
  conda env create -f "$ENV_YML" || error_exit "Failed to create environment."
  echo "Environment '$ENV_NAME' created successfully."
fi

conda run -n $ENV_NAME pip install -r ../../requirements.txt