[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,

  [switch]$NoBrowser,
  [switch]$CheckOnly,
  [switch]$AllowNonCanonicalSource
)

$ErrorActionPreference = "Stop"

function Get-LauncherRoot {
  return Split-Path -Parent $PSCommandPath
}

function Write-RestartStatus {
  param([string]$Message)
  Write-Host "[restart] $Message"
}

function Quote-ProcessArgument {
  param([string]$Value)

  if ($Value -notmatch '[\s"]') {
    return $Value
  }
  return '"' + ($Value -replace '"', '\"') + '"'
}

function Join-ProcessArguments {
  param([string[]]$Parts)

  return (($Parts | ForEach-Object { Quote-ProcessArgument -Value $_ }) -join " ")
}

function Invoke-LifecycleScript {
  param(
    [string]$ScriptPath,
    [string[]]$ScriptArguments
  )

  $powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
  $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $ScriptPath) + $ScriptArguments
  $process = Start-Process -FilePath $powershell -ArgumentList (Join-ProcessArguments -Parts $arguments) -WindowStyle Hidden -Wait -PassThru
  return $process.ExitCode
}

$launcherRoot = Get-LauncherRoot
$stopScript = Join-Path $launcherRoot "stop_web_console.ps1"
$startScript = Join-Path $launcherRoot "start_web_console.ps1"

if (-not (Test-Path -LiteralPath $stopScript)) {
  Write-Error "Stop script is missing: launcher\stop_web_console.ps1"
  exit 1
}
if (-not (Test-Path -LiteralPath $startScript)) {
  Write-Error "Start script is missing: launcher\start_web_console.ps1"
  exit 1
}

Write-RestartStatus "Restart requested for 127.0.0.1:$BackendPort."

$stopArgs = @("-BackendPort", "$BackendPort")
$startArgs = @("-BackendPort", "$BackendPort")
if ($CheckOnly) {
  $stopArgs += "-CheckOnly"
  $startArgs += "-CheckOnly"
}
if ($NoBrowser) {
  $startArgs += "-NoBrowser"
}
if ($AllowNonCanonicalSource) {
  $startArgs += "-AllowNonCanonicalSource"
}

$stopExitCode = Invoke-LifecycleScript -ScriptPath $stopScript -ScriptArguments $stopArgs
if ($stopExitCode -ne 0) {
  Write-Error "Stop step failed with exit code $stopExitCode."
  exit $stopExitCode
}

if (-not $CheckOnly) {
  Start-Sleep -Milliseconds 500
}

$startExitCode = Invoke-LifecycleScript -ScriptPath $startScript -ScriptArguments $startArgs
if ($startExitCode -ne 0) {
  Write-Error "Start step failed with exit code $startExitCode."
  exit $startExitCode
}
