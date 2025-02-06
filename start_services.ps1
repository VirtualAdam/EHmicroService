<#
.SYNOPSIS
  A PowerShell script to start RabbitMQ (Docker) and run all microservices in separate windows.
#>

# 1. Check if Docker is installed and running
Write-Host "Checking Docker..."
docker version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker doesn't seem to be running or installed. Please start Docker Desktop or install Docker."
    exit 1
}

# 2. Pull and run RabbitMQ Docker container if not running
Write-Host "Starting RabbitMQ container (if not already)..."
# Use a container name 'rabbitmq' and publish management ports
docker ps --filter "name=rabbitmq" --filter "status=running" | Select-String "rabbitmq" > $null
if ($?) {
    Write-Host "RabbitMQ container 'rabbitmq' is already running."
} else {
    # If not running, try to start if exists, else run
    docker start rabbitmq 2>$null
    if ($LASTEXITCODE -ne 0) {
        # Container doesn't exist, so run a new one
        docker run -d --hostname rabbitmq --name rabbitmq `
          -p 5672:5672 -p 15672:15672 `
          rabbitmq:3-management
        Write-Host "RabbitMQ container started on ports 5672 and 15672."
    } else {
        Write-Host "RabbitMQ container was stopped, now started."
    }
}

# 3. Optional: Create/Activate Python venv if you want isolation
$venvPath = ".\venv"
if (!(Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv $venvPath
}
Write-Host "Activating virtual environment..."
. "$venvPath\Scripts\activate.ps1"

# 4. Install Python requirements
Write-Host "Installing Python requirements..."
pip install -r requirements.txt

Write-Host "Launching microservices in new PowerShell windows..."

# 5. Start Entitlement Service
Start-Process powershell -NoExit -ArgumentList "`. $venvPath\Scripts\activate; python .\entitlement_service.py`"

# 6. Start Controller
Start-Process powershell -NoExit -ArgumentList "`. $venvPath\Scripts\activate; python .\controller.py`"

# 7. Start Data Service
Start-Process powershell -NoExit -ArgumentList "`. $venvPath\Scripts\activate; python .\data_service.py`"

Write-Host "All services launched! Check the new windows for logs."
Write-Host "You can run 'python .\test_frontdoor_publisher.py' in this window to send test messages."
