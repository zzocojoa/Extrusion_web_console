[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,

  [ValidateRange(1, 120)]
  [int]$TimeoutSeconds = 15,

  [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

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

function Write-StopLog {
  param(
    [string]$Message,
    [string]$Level = "INFO"
  )
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$stamp][$Level] $(Redact-LauncherText $Message)"
  Write-Host $line
  if ($script:StopLogPath) {
    Add-Content -LiteralPath $script:StopLogPath -Value $line -Encoding UTF8
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

function Get-HealthProperty {
  param(
    [object]$Health,
    [string[]]$Names
  )
  foreach ($name in $Names) {
    if ($Health.PSObject.Properties.Name -contains $name) {
      return $Health.$name
    }
  }
  return $null
}

function Assert-VerifiedHealth {
  param([object]$Health)

  if (-not $Health) {
    Write-StopLog "No health response was returned by 127.0.0.1:$BackendPort." "ERROR"
    exit 1
  }
  if ($Health.status -ne "ok") {
    Write-StopLog "Health response status is not ok. Refusing to stop." "ERROR"
    exit 1
  }
  if ($Health.service -ne "extrusion-web-console-api") {
    Write-StopLog "Health response service is not extrusion-web-console-api. Refusing to stop." "ERROR"
    exit 1
  }

  $localhostOnly = (Get-HealthProperty -Health $Health -Names @("localhost_only", "localhostOnly"))
  if ($localhostOnly -ne $true) {
    Write-StopLog "Health response is not localhost-only. Refusing to stop." "ERROR"
    exit 1
  }

  $processIdValue = Get-HealthProperty -Health $Health -Names @("process_id", "processId")
  $processId = 0
  if ($null -eq $processIdValue -or -not [int]::TryParse([string]$processIdValue, [ref]$processId) -or $processId -le 0) {
    Write-StopLog "Health response did not include a valid process_id. Refusing to stop." "ERROR"
    exit 1
  }
  return $processId
}

function Assert-BackendProcessMatchesHealth {
  param(
    [int]$ProcessId,
    [int]$Port
  )

  $processInfo = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
  if (-not $processInfo) {
    Write-StopLog "Health process_id no longer exists. Nothing was stopped." "ERROR"
    exit 1
  }

  $name = [string]$processInfo.Name
  $commandLine = [string]$processInfo.CommandLine
  if ($name -ne "python.exe") {
    Write-StopLog "Verified health process is not python.exe. Refusing to stop." "ERROR"
    exit 1
  }
  if ($commandLine -notmatch "(?i)(^|\s)-m\s+uvicorn(\s|$)") {
    Write-StopLog "Verified health process was not started through uvicorn. Refusing to stop." "ERROR"
    exit 1
  }
  if ($commandLine -notmatch [regex]::Escape("backend.app.main:app")) {
    Write-StopLog "Verified health process does not run backend.app.main:app. Refusing to stop." "ERROR"
    exit 1
  }
  if ($commandLine -notmatch "(?i)--host\s+127\.0\.0\.1") {
    Write-StopLog "Verified health process does not bind 127.0.0.1. Refusing to stop." "ERROR"
    exit 1
  }
  if ($commandLine -notmatch "(?i)--port\s+$Port(\s|$)") {
    Write-StopLog "Verified health process is not on the requested backend port. Refusing to stop." "ERROR"
    exit 1
  }

  return $processInfo
}

function Wait-ForPortClosed {
  param(
    [int]$Port,
    [int]$Timeout
  )
  $deadline = (Get-Date).AddSeconds($Timeout)
  while ((Get-Date) -lt $deadline) {
    if (-not (Test-PortOpen -Port $Port)) {
      return $true
    }
    Start-Sleep -Milliseconds 250
  }
  return (-not (Test-PortOpen -Port $Port))
}

$appData = Join-Path $env:APPDATA "ExtrusionWebConsole"
$logRoot = Join-Path $appData "logs\launcher"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
$script:StopLogPath = Join-Path $logRoot "stop-$timestamp.log"
$stopLatest = Join-Path $logRoot "stop-latest.log"

Write-StopLog "Extrusion Web Console stop requested. Port=$BackendPort CheckOnly=$([bool]$CheckOnly)"

$health = Get-Health -Port $BackendPort
if (-not $health) {
  if (Test-PortOpen -Port $BackendPort) {
    Write-StopLog "Port $BackendPort is open but did not return a verified Extrusion Web Console health response." "ERROR"
    Copy-Item -LiteralPath $script:StopLogPath -Destination $stopLatest -Force
    exit 1
  }
  Write-StopLog "No Extrusion Web Console backend is running on 127.0.0.1:$BackendPort."
  Copy-Item -LiteralPath $script:StopLogPath -Destination $stopLatest -Force
  exit 0
}

$processId = Assert-VerifiedHealth -Health $health
$null = Assert-BackendProcessMatchesHealth -ProcessId $processId -Port $BackendPort

if ($CheckOnly) {
  Write-StopLog "CheckOnly completed. Verified backend process id $processId would be stopped; no process was stopped."
  Copy-Item -LiteralPath $script:StopLogPath -Destination $stopLatest -Force
  exit 0
}

Write-StopLog "Stopping verified Extrusion Web Console backend process id $processId."
Stop-Process -Id $processId -ErrorAction Stop

if (-not (Wait-ForPortClosed -Port $BackendPort -Timeout $TimeoutSeconds)) {
  Write-StopLog "Backend process stop was requested, but port $BackendPort is still open after $TimeoutSeconds seconds." "ERROR"
  Copy-Item -LiteralPath $script:StopLogPath -Destination $stopLatest -Force
  exit 1
}

Write-StopLog "Backend stopped and port $BackendPort is closed."
Copy-Item -LiteralPath $script:StopLogPath -Destination $stopLatest -Force
