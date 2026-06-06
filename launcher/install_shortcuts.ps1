[CmdletBinding()]
param(
  [string]$ShortcutName = "Extrusion Web Console",
  [string]$DesktopDirectory,
  [string]$StartMenuDirectory,
  [switch]$SkipDesktop,
  [switch]$SkipStartMenu,
  [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  $scriptPath = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptPath "..")).Path
}

function Get-DefaultDesktopDirectory {
  return [Environment]::GetFolderPath("Desktop")
}

function Get-DefaultStartMenuDirectory {
  return [Environment]::GetFolderPath("Programs")
}

function Write-ShortcutStatus {
  param([string]$Message)
  Write-Host "[shortcut] $Message"
}

function Set-Shortcut {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ShortcutPath,
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$Description
  )

  $parent = Split-Path -Parent $ShortcutPath
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }

  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($ShortcutPath)
  $shortcut.TargetPath = $TargetPath
  $shortcut.WorkingDirectory = $WorkingDirectory
  $shortcut.Description = $Description
  $shortcut.WindowStyle = 1
  $shortcut.Save()
}

$repoRoot = Get-RepoRoot
$targetPath = Join-Path $repoRoot "launcher\start_web_console.bat"

if (-not (Test-Path -LiteralPath $targetPath)) {
  Write-Error "Shortcut target is missing: launcher\start_web_console.bat"
  exit 1
}

if ([string]::IsNullOrWhiteSpace($DesktopDirectory)) {
  $DesktopDirectory = Get-DefaultDesktopDirectory
}
if ([string]::IsNullOrWhiteSpace($StartMenuDirectory)) {
  $StartMenuDirectory = Get-DefaultStartMenuDirectory
}

$description = "Start the local Extrusion Web Console on 127.0.0.1."
$shortcutFileName = "$ShortcutName.lnk"
$plannedShortcuts = @()

if (-not $SkipDesktop) {
  $plannedShortcuts += [pscustomobject]@{
    Scope = "Desktop"
    Path = Join-Path $DesktopDirectory $shortcutFileName
  }
}

if (-not $SkipStartMenu) {
  $plannedShortcuts += [pscustomobject]@{
    Scope = "Start menu"
    Path = Join-Path $StartMenuDirectory $shortcutFileName
  }
}

if ($plannedShortcuts.Count -eq 0) {
  Write-ShortcutStatus "No shortcut scopes selected. Nothing to do."
  exit 0
}

Write-ShortcutStatus "Target: launcher\start_web_console.bat"
Write-ShortcutStatus "Working directory: package root"
Write-ShortcutStatus "Policy: updates shortcuts in place; does not delete AppData config, state, logs, Docker data, database data, or operational CSV files."

foreach ($planned in $plannedShortcuts) {
  Write-ShortcutStatus "$($planned.Scope): $($planned.Path)"
  if (-not $CheckOnly) {
    Set-Shortcut `
      -ShortcutPath $planned.Path `
      -TargetPath $targetPath `
      -WorkingDirectory $repoRoot `
      -Description $description
  }
}

if ($CheckOnly) {
  Write-ShortcutStatus "CheckOnly completed. No shortcuts were written."
} else {
  Write-ShortcutStatus "Shortcut installation completed."
}
