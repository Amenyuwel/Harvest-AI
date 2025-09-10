# run.ps1 - Quick launcher script

# Always run from project directory
Set-Location -Path $PSScriptRoot

# Activate virtual environment
. .\.venv\Scripts\Activate.ps1

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -notmatch '^\s*#' -and $_ -match '^(.*?)=(.*)$') {
            Set-Item -Path Env:$($matches[1]) -Value $matches[2]
        }
    }
}

# Run your Python app as module to handle relative imports
python -m src.app
