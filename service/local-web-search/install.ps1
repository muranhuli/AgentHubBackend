<#
.SYNOPSIS
  Create a Conda environment from environment.yml if it does not already exist.
#>

param()

function Error-Exit([string]$Message) {
    Write-Error "Error: $Message"
    exit 1
}

# 1. Verify that conda is available
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Error-Exit "conda not found; please install Anaconda or Miniconda first."
}

# 2. Ensure environment.yml exists in the current directory
$envYml = Join-Path (Get-Location) 'environment.yml'
if (-not (Test-Path $envYml)) {
    Error-Exit "Could not find environment.yml in current directory."
}

# 3. Extract the environment name from environment.yml
$match = Select-String -Path $envYml -Pattern '^\s*name:\s*(\S+)'
if (-not $match) {
    Error-Exit "Could not extract 'name' field from environment.yml."
}
$envName = $match.Matches[0].Groups[1].Value

# 4. Check if the environment already exists
$json = conda env list --json | ConvertFrom-Json
$existingNames = $json.envs | ForEach-Object { Split-Path $_ -Leaf }
if ($existingNames -contains $envName) {
    Write-Host "Conda environment '$envName' already exists; skipping creation."
} else {
    Write-Host "Creating Conda environment '$envName' from environment.yml..."
    conda env create -f $envYml | Write-Host
    if ($LASTEXITCODE -ne 0) {
        Error-Exit "Failed to create environment."
    }
    Write-Host "Environment '$envName' created successfully."
}
# 5. Install Playwright in the Conda environment
conda run -n playwright_markitdown_env playwright install