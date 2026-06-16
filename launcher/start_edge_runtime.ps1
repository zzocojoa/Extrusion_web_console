[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$ApiPort = 0,

  [switch]$CheckOnly,

  [ValidateRange(5, 300)]
  [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  $scriptPath = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptPath "..")).Path
}

function Redact-EdgeRuntimeText {
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

function Write-EdgeRuntimeLog {
  param(
    [string]$Message,
    [string]$Level = "INFO"
  )
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$stamp][$Level] $(Redact-EdgeRuntimeText $Message)"
  Write-Host $line
  if ($script:EdgeRuntimeLogPath) {
    Add-Content -LiteralPath $script:EdgeRuntimeLogPath -Value $line -Encoding UTF8
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

function Resolve-LocalSupabaseApiPort {
  param([string]$RepoRoot)

  if ($ApiPort -gt 0) {
    return $ApiPort
  }

  $envValue = [Environment]::GetEnvironmentVariable("EWC_LOCAL_SUPABASE_API_PORT", "Process")
  if (-not [string]::IsNullOrWhiteSpace($envValue)) {
    $parsed = 0
    if ([int]::TryParse($envValue, [ref]$parsed) -and $parsed -ge 1024 -and $parsed -le 65535) {
      return $parsed
    }
  }

  $configPath = Join-Path $RepoRoot "supabase\config.toml"
  $configValue = Get-SupabaseTomlValue -ConfigPath $configPath -Section "api" -Key "port"
  if (-not [string]::IsNullOrWhiteSpace($configValue)) {
    $parsed = 0
    if ([int]::TryParse($configValue, [ref]$parsed) -and $parsed -ge 1024 -and $parsed -le 65535) {
      return $parsed
    }
  }

  return 55321
}

function Resolve-ProjectId {
  param([string]$RepoRoot)

  $configPath = Join-Path $RepoRoot "supabase\config.toml"
  $projectId = Get-SupabaseTomlValue -ConfigPath $configPath -Section "" -Key "project_id"
  if ([string]::IsNullOrWhiteSpace($projectId)) {
    return "Extrusion_web_console"
  }
  return $projectId
}

function Invoke-EdgeNoAuthProbe {
  param(
    [int]$Port,
    [string]$Method
  )

  $uri = "http://127.0.0.1:$Port/functions/v1/upload-metrics"
  try {
    if ($Method -eq "POST") {
      Invoke-WebRequest -Uri $uri -Method Post -Body "{}" -ContentType "application/json" -TimeoutSec 5 -UseBasicParsing | Out-Null
    } else {
      Invoke-WebRequest -Uri $uri -Method Get -TimeoutSec 5 -UseBasicParsing | Out-Null
    }
    return "unexpected_success"
  } catch {
    $statusCode = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
      $statusCode = [int]$_.Exception.Response.StatusCode
    }
    if ($statusCode -eq 401 -or $statusCode -eq 403) {
      return "auth_class"
    }
    if ($statusCode -eq 503) {
      return "unavailable_class"
    }
    if ($statusCode) {
      return "http_$statusCode"
    }
    return "unreachable"
  }
}

function Test-EdgeAuthBoundary {
  param([int]$Port)

  $getClass = Invoke-EdgeNoAuthProbe -Port $Port -Method "GET"
  $postClass = Invoke-EdgeNoAuthProbe -Port $Port -Method "POST"
  return [pscustomobject]@{
    GetClass = $getClass
    PostClass = $postClass
    Ready = ($getClass -eq "auth_class" -and $postClass -eq "auth_class")
  }
}

function Test-RepoFunctionEntrypoint {
  param([string]$RepoRoot)
  $entrypoint = Join-Path $RepoRoot "supabase\functions\upload-metrics\index.ts"
  return Test-Path -LiteralPath $entrypoint -PathType Leaf
}

function Get-ExpectedEdgeContainerId {
  param([string]$ProjectId)

  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) {
    return $null
  }

  $containerName = "supabase_edge_runtime_$ProjectId"
  try {
    $containerId = & $docker.Source ps --filter "name=^/$containerName$" --format "{{.ID}}" 2>$null | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($containerId)) {
      return $null
    }
    return $containerId.Trim()
  } catch {
    return $null
  }
}

function Test-ContainerFunctionEntrypoint {
  param([string]$ProjectId)

  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) {
    return "docker_unavailable"
  }

  $containerId = Get-ExpectedEdgeContainerId -ProjectId $ProjectId
  if ([string]::IsNullOrWhiteSpace($containerId)) {
    return "container_missing"
  }

  $probe = "find / -path '*/upload-metrics/index.ts' -print -quit 2>/dev/null | grep -q ."
  try {
    & $docker.Source exec $containerId sh -lc $probe 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      return "present"
    }
    return "missing"
  } catch {
    return "unknown"
  }
}

function Start-CurrentSourceEdgeRuntime {
  param(
    [string]$RepoRoot,
    [string]$StdOutPath,
    [string]$StdErrPath
  )

  $supabase = Get-Command supabase -ErrorAction SilentlyContinue
  if (-not $supabase) {
    throw "Supabase CLI is not available on PATH."
  }

  $arguments = @("functions", "serve", "--workdir", $RepoRoot, "--yes")
  return Start-Process -FilePath $supabase.Source `
    -ArgumentList $arguments `
    -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput $StdOutPath `
    -RedirectStandardError $StdErrPath `
    -WindowStyle Hidden `
    -PassThru
}

function Test-EdgeRuntimeReady {
  param(
    [int]$Port,
    [string]$ProjectId
  )

  $authBoundary = Test-EdgeAuthBoundary -Port $Port
  $entrypointClass = Test-ContainerFunctionEntrypoint -ProjectId $ProjectId
  return [pscustomobject]@{
    AuthBoundary = $authBoundary
    EntrypointClass = $entrypointClass
    Ready = ($authBoundary.Ready -eq $true -and $entrypointClass -eq "present")
  }
}

$repoRoot = Get-RepoRoot
$appData = Join-Path $env:APPDATA "ExtrusionWebConsole"
$logRoot = Join-Path $appData "logs\launcher"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$script:EdgeRuntimeLogPath = Join-Path $logRoot "edge-runtime-$timestamp.log"
$edgeStdOutPath = Join-Path $logRoot "edge-runtime-serve-$timestamp.log"
$edgeStdErrPath = Join-Path $logRoot "edge-runtime-serve-$timestamp.err.log"
$edgeLatestPath = Join-Path $logRoot "edge-runtime-latest.log"

$port = Resolve-LocalSupabaseApiPort -RepoRoot $repoRoot
$projectId = Resolve-ProjectId -RepoRoot $repoRoot

Write-EdgeRuntimeLog "Edge runtime recovery check starting. API port=$port."

if (-not (Test-RepoFunctionEntrypoint -RepoRoot $repoRoot)) {
  Write-EdgeRuntimeLog "Repository upload-metrics entrypoint is missing." "ERROR"
  exit 1
}

$initial = Test-EdgeRuntimeReady -Port $port -ProjectId $projectId
Write-EdgeRuntimeLog "Initial Edge classes: GET=$($initial.AuthBoundary.GetClass); POST=$($initial.AuthBoundary.PostClass); entrypoint=$($initial.EntrypointClass)."

if ($initial.Ready) {
  Write-EdgeRuntimeLog "Edge runtime already serves current upload-metrics entrypoint with auth boundary."
  Copy-Item -LiteralPath $script:EdgeRuntimeLogPath -Destination $edgeLatestPath -Force
  exit 0
}

if ($CheckOnly) {
  Write-EdgeRuntimeLog "CheckOnly requested; Edge runtime is not ready." "ERROR"
  Copy-Item -LiteralPath $script:EdgeRuntimeLogPath -Destination $edgeLatestPath -Force
  exit 1
}

Write-EdgeRuntimeLog "Starting Supabase Edge functions from current repository source."
$serveProcess = Start-CurrentSourceEdgeRuntime -RepoRoot $repoRoot -StdOutPath $edgeStdOutPath -StdErrPath $edgeStdErrPath
Write-EdgeRuntimeLog "Supabase functions serve process started. ProcessId=$($serveProcess.Id)."

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
  $current = Test-EdgeRuntimeReady -Port $port -ProjectId $projectId
  if ($current.Ready) {
    Write-EdgeRuntimeLog "Edge runtime ready. GET=$($current.AuthBoundary.GetClass); POST=$($current.AuthBoundary.PostClass); entrypoint=$($current.EntrypointClass)."
    Copy-Item -LiteralPath $script:EdgeRuntimeLogPath -Destination $edgeLatestPath -Force
    exit 0
  }
  if ($serveProcess.HasExited) {
    Write-EdgeRuntimeLog "Supabase functions serve exited before Edge runtime became ready. ExitCode=$($serveProcess.ExitCode)." "ERROR"
    Copy-Item -LiteralPath $script:EdgeRuntimeLogPath -Destination $edgeLatestPath -Force
    exit 1
  }
  Start-Sleep -Seconds 1
}

$final = Test-EdgeRuntimeReady -Port $port -ProjectId $projectId
Write-EdgeRuntimeLog "Timed out waiting for Edge runtime. GET=$($final.AuthBoundary.GetClass); POST=$($final.AuthBoundary.PostClass); entrypoint=$($final.EntrypointClass)." "ERROR"
Copy-Item -LiteralPath $script:EdgeRuntimeLogPath -Destination $edgeLatestPath -Force
exit 1
