[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,

  [switch]$CheckOnly,
  [switch]$NoOpenOnStart,
  [switch]$OpenExisting,
  [switch]$ExitExisting
)

$ErrorActionPreference = "Stop"
$script:MutexName = "Local\ExtrusionWebConsoleTraySupervisor"
$script:OpenEventName = "Local\ExtrusionWebConsoleTrayOpen"
$script:ExitEventName = "Local\ExtrusionWebConsoleTrayExit"
$script:TrayLogPath = $null
$script:NotifyIcon = $null
$script:OpenEvent = $null
$script:ExitEvent = $null
$script:Mutex = $null
$script:ApplicationContext = $null

function Get-RepoRoot {
  $scriptPath = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptPath "..")).Path
}

function Redact-TrayText {
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

function Write-TrayLog {
  param(
    [string]$Message,
    [string]$Level = "INFO"
  )
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$stamp][$Level] $(Redact-TrayText $Message)"
  Write-Host $line
  if ($script:TrayLogPath) {
    Add-Content -LiteralPath $script:TrayLogPath -Value $line -Encoding UTF8
  }
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

function Invoke-HiddenLifecycleScript {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [Parameter(Mandatory = $true)]
    [string[]]$ScriptArguments,
    [bool]$WaitForExit
  )

  $powerShellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
  $arguments = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-WindowStyle",
    "Hidden",
    "-File",
    $ScriptPath
  ) + $ScriptArguments

  if ($WaitForExit) {
    $process = Start-Process -FilePath $powerShellPath -ArgumentList (Join-ProcessArguments -Parts $arguments) -WindowStyle Hidden -Wait -PassThru
    return $process.ExitCode
  }

  $process = Start-Process -FilePath $powerShellPath -ArgumentList (Join-ProcessArguments -Parts $arguments) -WindowStyle Hidden -PassThru
  return 0
}

function Set-NamedEvent {
  param([string]$EventName)

  try {
    $event = [System.Threading.EventWaitHandle]::OpenExisting($EventName)
    try {
      $event.Set() | Out-Null
      return $true
    } finally {
      $event.Dispose()
    }
  } catch [System.Threading.WaitHandleCannotBeOpenedException] {
    return $false
  }
}

function Invoke-OpenConsole {
  try {
    Write-TrayLog "Open requested. Starting or reusing backend on 127.0.0.1:$BackendPort."
    $startScript = Join-Path $script:LauncherRoot "start_web_console.ps1"
    $exitCode = Invoke-HiddenLifecycleScript -ScriptPath $startScript -ScriptArguments @("-BackendPort", "$BackendPort") -WaitForExit $false
    if ($exitCode -ne 0) {
      Write-TrayLog "Open request failed with exit code $exitCode." "ERROR"
      if ($script:NotifyIcon) {
        $script:NotifyIcon.ShowBalloonTip(4000, "Extrusion Web Console", "Open failed. Check launcher logs.", [System.Windows.Forms.ToolTipIcon]::Error)
      }
    }
  } catch {
    Write-TrayLog "Open request failed: $($_.Exception.Message)" "ERROR"
    if ($script:NotifyIcon) {
      $script:NotifyIcon.ShowBalloonTip(4000, "Extrusion Web Console", "Open failed. Check launcher logs.", [System.Windows.Forms.ToolTipIcon]::Error)
    }
  }
}

function Invoke-ExitSupervisor {
  try {
    Write-TrayLog "Exit requested. Safe stop will verify the backend before closing port $BackendPort."
    $stopScript = Join-Path $script:LauncherRoot "stop_web_console.ps1"
    $exitCode = Invoke-HiddenLifecycleScript -ScriptPath $stopScript -ScriptArguments @("-BackendPort", "$BackendPort") -WaitForExit $true
    if ($exitCode -ne 0) {
      Write-TrayLog "Safe stop failed with exit code $exitCode. Tray remains open." "ERROR"
      if ($script:NotifyIcon) {
        $script:NotifyIcon.ShowBalloonTip(5000, "Extrusion Web Console", "Exit failed. Backend was not safely stopped.", [System.Windows.Forms.ToolTipIcon]::Error)
      }
      return
    }
    Write-TrayLog "Safe stop completed. Exiting tray supervisor."
    if ($script:NotifyIcon) {
      $script:NotifyIcon.Visible = $false
    }
    if ($script:ApplicationContext) {
      $script:ApplicationContext.ExitThread()
    } else {
      [System.Windows.Forms.Application]::ExitThread()
    }
  } catch {
    Write-TrayLog "Exit request failed: $($_.Exception.Message)" "ERROR"
    if ($script:NotifyIcon) {
      $script:NotifyIcon.ShowBalloonTip(5000, "Extrusion Web Console", "Exit failed. Check launcher logs.", [System.Windows.Forms.ToolTipIcon]::Error)
    }
  }
}

$script:RepoRoot = Get-RepoRoot
$script:LauncherRoot = Join-Path $script:RepoRoot "launcher"
$startScriptPath = Join-Path $script:LauncherRoot "start_web_console.ps1"
$stopScriptPath = Join-Path $script:LauncherRoot "stop_web_console.ps1"
$iconPath = Join-Path $script:LauncherRoot "assets\extrusion-console.ico"
$appData = Join-Path $env:APPDATA "ExtrusionWebConsole"
$logRoot = Join-Path $appData "logs\launcher"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
$script:TrayLogPath = Join-Path $logRoot "tray-$timestamp.log"
$trayLatest = Join-Path $logRoot "tray-latest.log"

Write-TrayLog "Extrusion Web Console tray supervisor starting. Port=$BackendPort CheckOnly=$([bool]$CheckOnly)"
Write-TrayLog "Repository root: $script:RepoRoot"

if (-not (Test-Path -LiteralPath $startScriptPath)) {
  Write-TrayLog "Start script is missing: launcher\start_web_console.ps1" "ERROR"
  exit 1
}
if (-not (Test-Path -LiteralPath $stopScriptPath)) {
  Write-TrayLog "Stop script is missing: launcher\stop_web_console.ps1" "ERROR"
  exit 1
}
if (-not (Test-Path -LiteralPath $iconPath)) {
  Write-TrayLog "Tray icon is missing: launcher\assets\extrusion-console.ico" "ERROR"
  exit 1
}

if ($CheckOnly) {
  Write-TrayLog "Tray technology: PowerShell System.Windows.Forms.NotifyIcon."
  Write-TrayLog "Menu: Open, Exit."
  Write-TrayLog "Open action: hidden start_web_console.ps1; browser close does not stop the tray."
  Write-TrayLog "Exit action: hidden stop_web_console.ps1 safe stop verification."
  Write-TrayLog "CheckOnly completed. No backend process or tray icon was started."
  Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  exit 0
}

if ($OpenExisting) {
  if (Set-NamedEvent -EventName $script:OpenEventName) {
    Write-TrayLog "Open signal sent to existing tray supervisor."
    Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
    exit 0
  }
  Write-TrayLog "No existing tray supervisor accepted the open signal." "ERROR"
  Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  exit 1
}

if ($ExitExisting) {
  if (Set-NamedEvent -EventName $script:ExitEventName) {
    Write-TrayLog "Exit signal sent to existing tray supervisor."
    Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
    exit 0
  }
  Write-TrayLog "No existing tray supervisor accepted the exit signal." "ERROR"
  Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  exit 1
}

$createdNew = $false
$script:Mutex = New-Object System.Threading.Mutex($true, $script:MutexName, [ref]$createdNew)
if (-not $createdNew) {
  Write-TrayLog "Another tray supervisor is already running. Signaling Open instead of starting a duplicate."
  if (-not (Set-NamedEvent -EventName $script:OpenEventName)) {
    Write-TrayLog "Existing tray supervisor did not accept the open signal." "ERROR"
    exit 1
  }
  Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  exit 0
}

try {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  [System.Windows.Forms.Application]::EnableVisualStyles()

  $script:OpenEvent = New-Object System.Threading.EventWaitHandle($false, [System.Threading.EventResetMode]::AutoReset, $script:OpenEventName)
  $script:ExitEvent = New-Object System.Threading.EventWaitHandle($false, [System.Threading.EventResetMode]::AutoReset, $script:ExitEventName)

  $menu = New-Object System.Windows.Forms.ContextMenuStrip
  $openItem = $menu.Items.Add("Open")
  $exitItem = $menu.Items.Add("Exit")
  $openItem.Add_Click({ Invoke-OpenConsole })
  $exitItem.Add_Click({ Invoke-ExitSupervisor })

  $script:NotifyIcon = New-Object System.Windows.Forms.NotifyIcon
  $script:NotifyIcon.Icon = New-Object System.Drawing.Icon($iconPath)
  $script:NotifyIcon.Text = "Extrusion Web Console"
  $script:NotifyIcon.ContextMenuStrip = $menu
  $script:NotifyIcon.Visible = $true
  $script:NotifyIcon.Add_DoubleClick({ Invoke-OpenConsole })

  $timer = New-Object System.Windows.Forms.Timer
  $timer.Interval = 1000
  $timer.Add_Tick({
      if ($script:OpenEvent -and $script:OpenEvent.WaitOne(0)) {
        Invoke-OpenConsole
      }
      if ($script:ExitEvent -and $script:ExitEvent.WaitOne(0)) {
        Invoke-ExitSupervisor
      }
    })
  $timer.Start()

  if (-not $NoOpenOnStart) {
    Invoke-OpenConsole
  } else {
    Write-TrayLog "Initial browser open skipped by -NoOpenOnStart."
  }

  Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  $script:ApplicationContext = New-Object System.Windows.Forms.ApplicationContext
  [System.Windows.Forms.Application]::Run($script:ApplicationContext)
} finally {
  if ($timer) {
    $timer.Stop()
    $timer.Dispose()
  }
  if ($script:NotifyIcon) {
    $script:NotifyIcon.Visible = $false
    $script:NotifyIcon.Dispose()
  }
  if ($menu) {
    $menu.Dispose()
  }
  if ($script:OpenEvent) {
    $script:OpenEvent.Dispose()
  }
  if ($script:ExitEvent) {
    $script:ExitEvent.Dispose()
  }
  if ($script:Mutex) {
    $script:Mutex.ReleaseMutex()
    $script:Mutex.Dispose()
  }
  if ($script:TrayLogPath -and (Test-Path -LiteralPath $script:TrayLogPath)) {
    Copy-Item -LiteralPath $script:TrayLogPath -Destination $trayLatest -Force
  }
}
