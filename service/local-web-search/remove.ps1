<#
.SYNOPSIS
  Remove the Conda environment named in environment.yml if it exists.
#>

function Error-Exit([string]$Message) {
    Write-Error "Error: $Message"
    exit 1
}

# verify conda
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Error-Exit "conda not found; install Anaconda or Miniconda first."
}

# verify environment.yml
$envYml = Join-Path (Get-Location) 'environment.yml'
if (-not (Test-Path $envYml)) {
    Error-Exit "environment.yml not found in current directory."
}

# extract name
$match = Select-String -Path $envYml -Pattern '^\s*name:\s*(\S+)'
if (-not $match) {
    Error-Exit "Could not extract 'name' from environment.yml."
}
$envName = $match.Matches[0].Groups[1].Value

# list existing envs
$json = conda env list --json | ConvertFrom-Json
$existing = $json.envs | ForEach-Object { Split-Path $_ -Leaf }

if ($existing -contains $envName) {
    Write-Host "Removing Conda environment '$envName'..."
    conda env remove -n $envName --yes | Out-Default
    if ($LASTEXITCODE -ne 0) {
        Error-Exit "Failed to remove environment '$envName'."
    }
    Write-Host "Environment '$envName' removed."
} else {
    Write-Host "Conda environment '$envName' does not exist; nothing to remove."
}
