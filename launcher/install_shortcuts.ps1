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

function Quote-ShortcutArgument {
  param([string]$Value)

  if ($Value -notmatch '[\s"]') {
    return $Value
  }
  return '"' + ($Value -replace '"', '\"') + '"'
}

function Join-ShortcutArguments {
  param([string[]]$Parts)

  return (($Parts | ForEach-Object { Quote-ShortcutArgument -Value $_ }) -join " ")
}

function Assert-SafeShortcutName {
  param([string]$Name)

  if ([string]::IsNullOrWhiteSpace($Name)) {
    Write-Error "ShortcutName must not be empty."
    exit 1
  }

  $invalidChars = [System.IO.Path]::GetInvalidFileNameChars()
  if ($Name.IndexOfAny($invalidChars) -ge 0) {
    Write-Error "ShortcutName must be a file name, not a path."
    exit 1
  }

  if ($Name -eq "." -or $Name -eq ".." -or $Name.Contains("..")) {
    Write-Error "ShortcutName must not contain path traversal markers."
    exit 1
  }

  if ([System.IO.Path]::IsPathRooted($Name)) {
    Write-Error "ShortcutName must be a file name, not an absolute path."
    exit 1
  }
}

function Set-Shortcut {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ShortcutPath,
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,
    [Parameter(Mandatory = $true)]
    [string]$Arguments,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$Description,
    [Parameter(Mandatory = $true)]
    [string]$IconLocation
  )

  $parent = Split-Path -Parent $ShortcutPath
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }

  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($ShortcutPath)
  $shortcut.TargetPath = $TargetPath
  $shortcut.Arguments = $Arguments
  $shortcut.WorkingDirectory = $WorkingDirectory
  $shortcut.Description = $Description
  $shortcut.IconLocation = $IconLocation
  $shortcut.WindowStyle = 7
  $shortcut.Save()
}

$repoRoot = Get-RepoRoot
$powerShellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
$iconPath = Join-Path $repoRoot "launcher\assets\extrusion-console.ico"
$shortcutSpecs = @(
  [pscustomobject]@{
    Action = "Start"
    Name = $ShortcutName
    RelativeScript = "launcher\start_web_console.ps1"
    Description = "Start or open the local Extrusion Web Console on 127.0.0.1."
  },
  [pscustomobject]@{
    Action = "Stop"
    Name = "$ShortcutName Stop"
    RelativeScript = "launcher\stop_web_console.ps1"
    Description = "Stop the verified local Extrusion Web Console backend."
  },
  [pscustomobject]@{
    Action = "Restart"
    Name = "$ShortcutName Restart"
    RelativeScript = "launcher\restart_web_console.ps1"
    Description = "Restart the local Extrusion Web Console backend and reopen the browser."
  }
)

Assert-SafeShortcutName -Name $ShortcutName
foreach ($shortcutSpec in $shortcutSpecs) {
  Assert-SafeShortcutName -Name $shortcutSpec.Name
}

foreach ($shortcutSpec in $shortcutSpecs) {
  $scriptPath = Join-Path $repoRoot $shortcutSpec.RelativeScript
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    Write-Error "Shortcut script is missing: $($shortcutSpec.RelativeScript)"
    exit 1
  }
  $shortcutSpec | Add-Member -NotePropertyName ScriptPath -NotePropertyValue $scriptPath
  $shortcutSpec | Add-Member -NotePropertyName ShortcutArguments -NotePropertyValue (Join-ShortcutArguments -Parts @(
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-WindowStyle",
      "Hidden",
      "-File",
      $scriptPath
    ))
}
if (-not (Test-Path -LiteralPath $iconPath)) {
  Write-Error "Shortcut icon is missing: launcher\assets\extrusion-console.ico"
  exit 1
}

if ([string]::IsNullOrWhiteSpace($DesktopDirectory)) {
  $DesktopDirectory = Get-DefaultDesktopDirectory
}
if ([string]::IsNullOrWhiteSpace($StartMenuDirectory)) {
  $StartMenuDirectory = Get-DefaultStartMenuDirectory
}

$plannedShortcuts = @()

foreach ($shortcutSpec in $shortcutSpecs) {
  $shortcutFileName = "$($shortcutSpec.Name).lnk"
  if (-not $SkipDesktop) {
    $plannedShortcuts += [pscustomobject]@{
      Action = $shortcutSpec.Action
      Scope = "Desktop"
      Path = Join-Path $DesktopDirectory $shortcutFileName
      Spec = $shortcutSpec
    }
  }

  if (-not $SkipStartMenu) {
    $plannedShortcuts += [pscustomobject]@{
      Action = $shortcutSpec.Action
      Scope = "Start menu"
      Path = Join-Path $StartMenuDirectory $shortcutFileName
      Spec = $shortcutSpec
    }
  }
}

if ($plannedShortcuts.Count -eq 0) {
  Write-ShortcutStatus "No shortcut scopes selected. Nothing to do."
  exit 0
}

Write-ShortcutStatus "Target executable: powershell.exe"
Write-ShortcutStatus "Target mode: -WindowStyle Hidden"
Write-ShortcutStatus "Icon: launcher\assets\extrusion-console.ico"
Write-ShortcutStatus "Working directory: package root"
Write-ShortcutStatus "Policy: updates shortcuts in place; does not delete AppData config, state, logs, Docker data, database data, or operational CSV files."

foreach ($planned in $plannedShortcuts) {
  Write-ShortcutStatus "$($planned.Action) shortcut $($planned.Scope): $($planned.Path)"
  Write-ShortcutStatus "$($planned.Action) script: $($planned.Spec.RelativeScript)"
  if (-not $CheckOnly) {
    Set-Shortcut `
      -ShortcutPath $planned.Path `
      -TargetPath $powerShellPath `
      -Arguments $planned.Spec.ShortcutArguments `
      -WorkingDirectory $repoRoot `
      -Description $planned.Spec.Description `
      -IconLocation $iconPath
  }
}

if ($CheckOnly) {
  Write-ShortcutStatus "CheckOnly completed. No shortcuts were written."
} else {
  Write-ShortcutStatus "Shortcut installation completed."
}
