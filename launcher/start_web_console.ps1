[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,

  [switch]$NoBrowser,
  [switch]$BuildFrontend,
  [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  $scriptPath = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptPath "..")).Path
}

function Redact-LauncherText {
  param([string]$Text)
  if ([string]::IsNullOrEmpty($Text)) {
    return $Text
  }
  $value = $Text
  $value = [regex]::Replace($value, '(?i)(authorization\s*:\s*bearer\s+)[^\s]+', '$1[redacted]')
  $value = [regex]::Replace($value, '(?i)(token|secret|service[_ -]?role|anon[_ -]?key|password)\s*[:=]\s*[^\s;]+', '$1=[redacted]')
  $value = [regex]::Replace($value, 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[redacted]')
  $value = [regex]::Replace($value, '(?i)\b[a-z]+://[^/\s:]+:[^@\s]+@[^\s]+', '[redacted-url]')
  return $value
}

function Write-LauncherLog {
  param(
    [string]$Message,
    [string]$Level = "INFO"
  )
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$stamp][$Level] $(Redact-LauncherText $Message)"
  Write-Host $line
  if ($script:LauncherLogPath) {
    Add-Content -LiteralPath $script:LauncherLogPath -Value $line -Encoding UTF8
  }
}

function Test-PortOpen {
  param([int]$Port)
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    if (-not $async.AsyncWaitHandle.WaitOne(500)) {
      return $false
    }
    $client.EndConnect($async)
    return $true
  } catch {
    return $false
  } finally {
    $client.Close()
  }
}

function Get-Health {
  param([int]$Port)
  try {
    return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
  } catch {
    return $null
  }
}

function Wait-ForHealth {
  param(
    [int]$Port,
    [int]$TimeoutSeconds = 30
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    $health = Get-Health -Port $Port
    if ($health -and $health.status -eq "ok" -and ($health.localhost_only -eq $true -or $health.localhostOnly -eq $true)) {
      return $true
    }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

function New-LocalApiToken {
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

function Test-FrontendBootstrap {
  param([int]$Port)
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2 -UseBasicParsing
    $body = [string]$response.Content
    return $body.Contains("__EWC_BOOTSTRAP__") -and $body.Contains("localApiToken")
  } catch {
    return $false
  }
}

$repoRoot = Get-RepoRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$frontendDist = Join-Path $frontendRoot "dist"
$frontendIndex = Join-Path $frontendDist "index.html"
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appData = Join-Path $env:APPDATA "ExtrusionWebConsole"
$logRoot = Join-Path $appData "logs\launcher"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$script:LauncherLogPath = Join-Path $logRoot "launcher-$timestamp.log"
$backendLogPath = Join-Path $logRoot "backend-$timestamp.log"
$backendErrorLogPath = Join-Path $logRoot "backend-$timestamp.err.log"
$launcherLatest = Join-Path $logRoot "launcher-latest.log"
$backendLatest = Join-Path $logRoot "backend-latest.log"

Write-LauncherLog "Extrusion Web Console operator launcher starting. Port=$BackendPort"
Write-LauncherLog "Repository root: $repoRoot"
Write-LauncherLog "Launcher log: $script:LauncherLogPath"
Write-LauncherLog "Backend log: $backendLogPath"
Write-LauncherLog "Backend error log: $backendErrorLogPath"

if (-not (Test-Path -LiteralPath $pythonExe)) {
  Write-LauncherLog "Python virtual environment is missing. Expected .venv\Scripts\python.exe." "ERROR"
  exit 1
}

if (-not (Test-Path -LiteralPath $frontendIndex)) {
  if ($BuildFrontend) {
    Write-LauncherLog "Frontend build is missing. Running npm run build because -BuildFrontend was set."
    Push-Location $frontendRoot
    try {
      npm run build
      if ($LASTEXITCODE -ne 0) {
        Write-LauncherLog "Frontend build failed. Review the npm output above." "ERROR"
        exit 1
      }
    } finally {
      Pop-Location
    }
    if (-not (Test-Path -LiteralPath $frontendIndex)) {
      Write-LauncherLog "Frontend build did not produce frontend\dist\index.html." "ERROR"
      exit 1
    }
  } else {
    Write-LauncherLog "Frontend build is missing. Run npm run build from frontend, or rerun this script with -BuildFrontend." "ERROR"
    exit 1
  }
}

if ($CheckOnly) {
  $checkToken = New-LocalApiToken
  if ([string]::IsNullOrWhiteSpace($checkToken)) {
    Write-LauncherLog "Local API token policy check failed. Token generation returned an empty value." "ERROR"
    exit 1
  }
  Write-LauncherLog "Local API token policy: required in operator mode; secure token generation is available; token value is hidden."
  Write-LauncherLog "CheckOnly completed. No backend process was started."
  Copy-Item -LiteralPath $script:LauncherLogPath -Destination $launcherLatest -Force
  exit 0
}

if (Test-PortOpen -Port $BackendPort) {
  $health = Get-Health -Port $BackendPort
  if ($health -and $health.status -eq "ok" -and $health.service -eq "extrusion-web-console-api") {
    if (-not (Test-FrontendBootstrap -Port $BackendPort)) {
      Write-LauncherLog "Existing backend is healthy but does not expose the local token bootstrap page. Close it and restart from this launcher." "ERROR"
      exit 1
    }
    Write-LauncherLog "Existing Extrusion Web Console backend is already running on 127.0.0.1:$BackendPort. Reusing it."
    if (-not $NoBrowser) {
      Start-Process "http://127.0.0.1:$BackendPort/"
    }
    Copy-Item -LiteralPath $script:LauncherLogPath -Destination $launcherLatest -Force
    exit 0
  }
  Write-LauncherLog "Port $BackendPort is already in use by another process. Close that process or choose a different port." "ERROR"
  exit 1
}

$env:EWC_HOST = "127.0.0.1"
$env:EWC_PORT = "$BackendPort"
$env:EWC_FRONTEND_DIST_PATH = $frontendDist
$env:EWC_LOCAL_TOKEN_MODE = "required"
$env:EWC_LOCAL_API_TOKEN = New-LocalApiToken
Write-LauncherLog "Local API token policy: required; token presence is present; token value is hidden."
$arguments = @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort")

Write-LauncherLog "Starting backend on 127.0.0.1:$BackendPort."
$backendProcess = Start-Process -FilePath $pythonExe `
  -ArgumentList $arguments `
  -WorkingDirectory $repoRoot `
  -RedirectStandardOutput $backendLogPath `
  -RedirectStandardError $backendErrorLogPath `
  -WindowStyle Hidden `
  -PassThru

try {
  if (-not (Wait-ForHealth -Port $BackendPort -TimeoutSeconds 30)) {
    Write-LauncherLog "Backend did not become healthy within 30 seconds." "ERROR"
    if (-not $backendProcess.HasExited) {
      Stop-Process -Id $backendProcess.Id
    }
    exit 1
  }

  Write-LauncherLog "Backend is healthy at http://127.0.0.1:$BackendPort/."
  if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$BackendPort/"
  } else {
    Write-LauncherLog "Browser open skipped. Open http://127.0.0.1:$BackendPort/ manually."
  }

  Copy-Item -LiteralPath $script:LauncherLogPath -Destination $launcherLatest -Force
  if (Test-Path -LiteralPath $backendLogPath) {
    Copy-Item -LiteralPath $backendLogPath -Destination $backendLatest -Force
  }

  Write-LauncherLog "Press Ctrl+C or close this window to stop the launcher-owned backend."
  while (-not $backendProcess.HasExited) {
    Start-Sleep -Seconds 1
  }
} finally {
  if ($backendProcess -and -not $backendProcess.HasExited) {
    Write-LauncherLog "Stopping launcher-owned backend process."
    Stop-Process -Id $backendProcess.Id
  }
}
