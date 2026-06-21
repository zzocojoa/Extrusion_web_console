[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,

  [switch]$NoBrowser,
  [switch]$BuildFrontend,
  [switch]$CheckOnly,
  [switch]$RequireFreshBackend,
  [switch]$AllowNonCanonicalSource
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

function Test-LanSafeHealth {
  param($Health)
  if (-not $Health) {
    return $false
  }
  $localhostOnly = ($Health.localhost_only -eq $true -or $Health.localhostOnly -eq $true)
  if (-not $localhostOnly) {
    return $false
  }

  $lanSecurity = $null
  if ($Health.PSObject.Properties.Name -contains "lan_security") {
    $lanSecurity = $Health.lan_security
  } elseif ($Health.PSObject.Properties.Name -contains "lanSecurity") {
    $lanSecurity = $Health.lanSecurity
  }
  if ($null -eq $lanSecurity) {
    return $false
  }
  return ($lanSecurity.status -eq "localhost_only" -and $lanSecurity.shared_local_token_allowed -eq $false)
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

function Get-SupabaseTomlValue {
  param(
    [string]$ConfigPath,
    [string]$Section,
    [string]$Key
  )

  if (-not (Test-Path -LiteralPath $ConfigPath)) {
    return $null
  }

  $currentSection = ""
  foreach ($line in Get-Content -LiteralPath $ConfigPath -Encoding UTF8) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith("#")) {
      continue
    }
    if ($trimmed -match '^\[(.+)\]$') {
      $currentSection = $Matches[1].Trim()
      continue
    }
    if ($currentSection -ne $Section) {
      continue
    }
    if ($trimmed -match "^\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*(#.*)?$") {
      return $Matches[1].Trim().Trim('"')
    }
  }
  return $null
}

function Resolve-OperatorPackagePort {
  param(
    [string]$EnvName,
    [string]$ConfigPath,
    [string]$Section,
    [int]$FallbackPort
  )

  $envValue = [Environment]::GetEnvironmentVariable($EnvName, "Process")
  if (-not [string]::IsNullOrWhiteSpace($envValue)) {
    $parsed = 0
    if ([int]::TryParse($envValue, [ref]$parsed)) {
      return $parsed
    }
  }

  $configValue = Get-SupabaseTomlValue -ConfigPath $ConfigPath -Section $Section -Key "port"
  if (-not [string]::IsNullOrWhiteSpace($configValue)) {
    $parsed = 0
    if ([int]::TryParse($configValue, [ref]$parsed)) {
      return $parsed
    }
  }

  return $FallbackPort
}

function Set-EnvDefault {
  param(
    [string]$Name,
    [string]$Value
  )

  if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($Name, "Process"))) {
    [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
  }
}

function Get-DevelopmentPlcSourceCandidate {
  $folderName = -join ([char[]](0xD1B5, 0xD569, 0x20, 0xB370, 0xC774, 0xD130, 0x20, 0x41, 0x72, 0x63, 0x68, 0x69, 0x76, 0x65))
  $drivePrefix = -join ([char[]](0x5A, 0x3A, 0x5C))
  return "$drivePrefix$folderName"
}

function Normalize-SourceForCompare {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) {
    return ""
  }
  return $Value.Trim().Trim('"').Trim("'").TrimEnd("\", "/")
}

function Test-CanonicalPlcSource {
  param([string]$Value)
  $normalized = Normalize-SourceForCompare -Value $Value
  $canonical = Normalize-SourceForCompare -Value (Get-DevelopmentPlcSourceCandidate)
  return [System.StringComparer]::OrdinalIgnoreCase.Equals($normalized, $canonical)
}

function Get-SourceClass {
  param([string]$Value)
  $normalized = Normalize-SourceForCompare -Value $Value
  if ([string]::IsNullOrWhiteSpace($normalized)) {
    return "empty"
  }
  if (Test-CanonicalPlcSource -Value $normalized) {
    return "canonical_mapped_drive"
  }
  if ($normalized -match '^[A-Za-z]:[\\/]') {
    return "noncanonical_drive"
  }
  if ($normalized.StartsWith("\\") -or $normalized.StartsWith("//")) {
    return "network_or_unc"
  }
  return "other"
}

function Get-DotenvValue {
  param(
    [string]$RepoRoot,
    [string]$Name
  )

  $dotenvPath = Join-Path $RepoRoot ".env"
  if (-not (Test-Path -LiteralPath $dotenvPath)) {
    return $null
  }

  foreach ($line in Get-Content -LiteralPath $dotenvPath -Encoding UTF8) {
    $candidate = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($candidate) -or $candidate.StartsWith("#")) {
      continue
    }
    if ($candidate.StartsWith("export ")) {
      $candidate = $candidate.Substring(7).Trim()
    }
    $parts = $candidate -split "=", 2
    if ($parts.Count -lt 2) {
      continue
    }
    $key = $parts[0].Trim()
    if ($key -eq $Name) {
      $value = $parts[1].Trim().Trim('"').Trim("'")
      return $value
    }
  }
  return $null
}

function Get-ConfigJsonValue {
  param(
    [string]$ConfigPath,
    [string]$Key
  )

  if (-not (Test-Path -LiteralPath $ConfigPath)) {
    return $null
  }

  try {
    $decoded = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
  } catch {
    return $null
  }

  if (-not ($decoded.PSObject.Properties.Name -contains $Key)) {
    return $null
  }
  return [string]$decoded.$Key
}

function Get-PlcSourceInputs {
  param(
    [string]$RepoRoot,
    [string]$ConfigPath
  )

  $inputs = @()
  $processValue = [Environment]::GetEnvironmentVariable("EWC_PLC_DATA_DIR", "Process")
  if ($null -ne $processValue) {
    $inputs += [pscustomobject]@{ Source = "process_env"; Class = Get-SourceClass -Value $processValue; Canonical = Test-CanonicalPlcSource -Value $processValue }
  }
  $dotenvValue = Get-DotenvValue -RepoRoot $RepoRoot -Name "EWC_PLC_DATA_DIR"
  if ($null -ne $dotenvValue) {
    $inputs += [pscustomobject]@{ Source = "repo_dotenv"; Class = Get-SourceClass -Value $dotenvValue; Canonical = Test-CanonicalPlcSource -Value $dotenvValue }
  }
  $configValue = Get-ConfigJsonValue -ConfigPath $ConfigPath -Key "plcDataDir"
  if ($null -ne $configValue) {
    $inputs += [pscustomobject]@{ Source = "config_json"; Class = Get-SourceClass -Value $configValue; Canonical = Test-CanonicalPlcSource -Value $configValue }
  }
  return $inputs
}

function Set-DevelopmentPlcSourceDefault {
  param(
    [string]$RepoRoot,
    [string]$ConfigPath,
    [bool]$AllowNonCanonical
  )

  $inputs = @(Get-PlcSourceInputs -RepoRoot $RepoRoot -ConfigPath $ConfigPath)
  if ($inputs.Count -gt 0) {
    $nonCanonical = @($inputs | Where-Object { -not $_.Canonical })
    if ($nonCanonical.Count -gt 0) {
      $summary = ($nonCanonical | ForEach-Object { "$($_.Source):$($_.Class)" }) -join ", "
      if (-not $AllowNonCanonical) {
        Write-LauncherLog "Non-canonical PLC source binding detected ($summary). Refusing to start so Preview cannot drift to the wrong source. Fix env/dotenv/config to the approved mapped-drive class or rerun with -AllowNonCanonicalSource for diagnostics only. Raw values hidden." "ERROR"
        exit 1
      }
      Write-LauncherLog "Non-canonical PLC source binding allowed by explicit -AllowNonCanonicalSource ($summary). Preview remains operator-controlled; raw values hidden." "WARNING"
      return
    }
    Write-LauncherLog "Canonical PLC source binding already provided by env/dotenv/config; launcher fallback skipped."
    return
  }

  $candidate = Get-DevelopmentPlcSourceCandidate
  if (Test-Path -LiteralPath $candidate -PathType Container) {
    [Environment]::SetEnvironmentVariable("EWC_PLC_DATA_DIR", $candidate, "Process")
    Write-LauncherLog "PLC source binding defaulted to accessible mapped-drive class for this launcher process; raw path hidden."
    return
  }

  if (-not $AllowNonCanonical) {
    Write-LauncherLog "Canonical PLC source binding was not configured and mapped-drive class is not accessible in this launcher process. Refusing to start; raw path hidden." "ERROR"
    exit 1
  }
  Write-LauncherLog "Canonical PLC source binding is missing or inaccessible, but -AllowNonCanonicalSource was set. Continuing for diagnostics only; raw path hidden." "WARNING"
}

function Set-OperatorPackageTargetDefaults {
  param([string]$RepoRoot)

  $supabaseConfig = Join-Path $RepoRoot "supabase\config.toml"
  $apiPort = Resolve-OperatorPackagePort -EnvName "EWC_LOCAL_SUPABASE_API_PORT" -ConfigPath $supabaseConfig -Section "api" -FallbackPort 55321
  $dbPort = Resolve-OperatorPackagePort -EnvName "EWC_LOCAL_SUPABASE_DB_PORT" -ConfigPath $supabaseConfig -Section "db" -FallbackPort 25433
  $studioPort = Resolve-OperatorPackagePort -EnvName "EWC_LOCAL_SUPABASE_STUDIO_PORT" -ConfigPath $supabaseConfig -Section "studio" -FallbackPort 55323
  $projectId = Get-SupabaseTomlValue -ConfigPath $supabaseConfig -Section "" -Key "project_id"
  if ([string]::IsNullOrWhiteSpace($projectId)) {
    $projectId = "Extrusion_web_console"
  }

  Set-EnvDefault -Name "EWC_LOCAL_SUPABASE_PROJECT_PATH" -Value $RepoRoot
  Set-EnvDefault -Name "EWC_LOCAL_SUPABASE_PROJECT_ID" -Value $projectId
  Set-EnvDefault -Name "EWC_LOCAL_SUPABASE_API_PORT" -Value "$apiPort"
  Set-EnvDefault -Name "EWC_LOCAL_SUPABASE_DB_PORT" -Value "$dbPort"
  Set-EnvDefault -Name "EWC_LOCAL_SUPABASE_STUDIO_PORT" -Value "$studioPort"
  Set-EnvDefault -Name "EWC_SUPABASE_URL" -Value "http://127.0.0.1:$apiPort"
  Set-EnvDefault -Name "EWC_SUPABASE_EDGE_URL" -Value "http://127.0.0.1:$apiPort/functions/v1/upload-metrics"

  $scheme = "postgres" + "ql"
  $user = "postgres"
  $database = "postgres"
  $separator = [char]64
  Set-EnvDefault -Name "EWC_SUPABASE_DB_URL" -Value "$scheme`://$user`:$user$separator`127.0.0.1`:$dbPort/$database"
}

$repoRoot = Get-RepoRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$frontendDist = Join-Path $frontendRoot "dist"
$frontendIndex = Join-Path $frontendDist "index.html"
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appData = Join-Path $env:APPDATA "ExtrusionWebConsole"
$configFilePath = [Environment]::GetEnvironmentVariable("EWC_CONFIG_FILE_PATH", "Process")
if ([string]::IsNullOrWhiteSpace($configFilePath)) {
  $configFilePath = Join-Path $appData "config.json"
}
$logRoot = Join-Path $appData "logs\launcher"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
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
Set-OperatorPackageTargetDefaults -RepoRoot $repoRoot
Write-LauncherLog "Operator package Supabase target defaults prepared; explicit process overrides respected; raw values hidden."
Set-DevelopmentPlcSourceDefault -RepoRoot $repoRoot -ConfigPath $configFilePath -AllowNonCanonical ([bool]$AllowNonCanonicalSource)

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
  Write-LauncherLog "API docs policy: disabled in operator mode."
  Write-LauncherLog "CheckOnly completed. No backend process was started."
  Copy-Item -LiteralPath $script:LauncherLogPath -Destination $launcherLatest -Force
  exit 0
}

if (Test-PortOpen -Port $BackendPort) {
  if ($RequireFreshBackend) {
    Write-LauncherLog "Backend port $BackendPort is already in use, and -RequireFreshBackend was set. Stop the existing backend before this QA run." "ERROR"
    exit 1
  }
  $health = Get-Health -Port $BackendPort
  if ($health -and $health.status -eq "ok" -and $health.service -eq "extrusion-web-console-api") {
    if (-not (Test-LanSafeHealth -Health $health)) {
      Write-LauncherLog "Existing backend is healthy but does not report localhost-only LAN-safe status. Close it and restart from this launcher." "ERROR"
      exit 1
    }
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
$env:EWC_API_DOCS_MODE = "disabled"
$env:EWC_LOCAL_TOKEN_MODE = "required"
$env:EWC_LOCAL_API_TOKEN = New-LocalApiToken
Write-LauncherLog "API docs policy: disabled in operator mode."
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
