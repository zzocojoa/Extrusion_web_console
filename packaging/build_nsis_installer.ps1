[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$PackageContainer,

  [string]$OutputRoot = "",
  [string]$MakensisPath = ""
)

$ErrorActionPreference = "Stop"

function Write-InstallerBuildInfo {
  param([string]$Message)
  Write-Host "[nsis-installer] $Message"
}

function Test-PathInsideOrEqual {
  param(
    [string]$BasePath,
    [string]$CandidatePath
  )

  $baseFullPath = [System.IO.Path]::GetFullPath($BasePath)
  $candidateFullPath = [System.IO.Path]::GetFullPath($CandidatePath)
  if ($candidateFullPath.Equals($baseFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $true
  }
  if (-not $baseFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
    $baseFullPath = $baseFullPath + [System.IO.Path]::DirectorySeparatorChar
  }
  return $candidateFullPath.StartsWith($baseFullPath, [System.StringComparison]::OrdinalIgnoreCase)
}

function Resolve-MakensisPath {
  param([string]$ExplicitPath)

  if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
    $fullPath = [System.IO.Path]::GetFullPath($ExplicitPath)
    if (-not (Test-Path -LiteralPath $fullPath)) {
      throw "makensis.exe was not found at MakensisPath: $ExplicitPath"
    }
    return $fullPath
  }

  $command = Get-Command makensis -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  $candidatePaths = @(
    "C:\Program Files\NSIS\makensis.exe",
    "C:\Program Files (x86)\NSIS\makensis.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\NSIS\makensis.exe"),
    (Join-Path $env:USERPROFILE "scoop\apps\nsis\current\makensis.exe")
  )

  $electronBuilderNsisCache = Join-Path $env:LOCALAPPDATA "electron-builder\Cache\nsis"
  if (Test-Path -LiteralPath $electronBuilderNsisCache) {
    Get-ChildItem -LiteralPath $electronBuilderNsisCache -Directory -Filter "nsis-*" |
      Sort-Object LastWriteTime -Descending |
      ForEach-Object {
        $candidatePaths += Join-Path $_.FullName "Bin\makensis.exe"
        $candidatePaths += Join-Path $_.FullName "makensis.exe"
      }
  }

  foreach ($candidatePath in $candidatePaths) {
    if (Test-Path -LiteralPath $candidatePath) {
      return $candidatePath
    }
  }

  throw "makensis.exe was not found. Install NSIS, restore the electron-builder NSIS cache, or pass -MakensisPath."
}

function Assert-SafeLabel {
  param([string]$Value)

  if ([string]::IsNullOrWhiteSpace($Value)) {
    throw "Package label is empty."
  }
  if ($Value -notmatch '^[A-Za-z0-9._-]+$') {
    throw "Package label contains unsupported characters: $Value"
  }
  if ([System.IO.Path]::IsPathRooted($Value) -or $Value.Contains("..")) {
    throw "Package label must not be a path: $Value"
  }
}

function Get-CheckedHash {
  param([string]$Path)

  return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Escape-NsisString {
  param([string]$Value)
  return $Value.Replace('$', '$$').Replace('"', '$\"')
}

function Assert-PackageMetadata {
  param(
    [object]$Metadata,
    [string]$PackageLabel
  )

  if ($Metadata.packageLabel -ne $PackageLabel) {
    throw "Package label mismatch: expected $PackageLabel but found $($Metadata.packageLabel)"
  }
  if ([string]::IsNullOrWhiteSpace([string]$Metadata.sourceCommit)) {
    throw "Package sourceCommit is empty."
  }
  if ($Metadata.frontendMode -ne "api") {
    throw "NSIS installer requires an API-mode package. Found frontendMode=$($Metadata.frontendMode)"
  }
  if ($Metadata.runtimeMode -ne "operator-ready") {
    throw "NSIS installer requires operator-ready runtime. Found runtimeMode=$($Metadata.runtimeMode)"
  }
  if ($Metadata.frontendBuildMetadataPresent -ne $true) {
    throw "frontendBuildMetadataPresent must be true."
  }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot ".."))
$packageContainerFull = [System.IO.Path]::GetFullPath($PackageContainer)

if (-not (Test-Path -LiteralPath $packageContainerFull)) {
  throw "PackageContainer does not exist: $PackageContainer"
}

$packageLabel = Split-Path -Leaf $packageContainerFull
Assert-SafeLabel -Value $packageLabel

$packageRoot = Join-Path $packageContainerFull "ExtrusionWebConsole"
$metadataPath = Join-Path $packageRoot "package-build-info.json"
if (-not (Test-Path -LiteralPath $metadataPath)) {
  throw "Package metadata is missing: $metadataPath"
}

$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
Assert-PackageMetadata -Metadata $metadata -PackageLabel $packageLabel

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $OutputRoot = Split-Path -Parent $packageContainerFull
}
$outputRootFull = [System.IO.Path]::GetFullPath($OutputRoot)
if (Test-PathInsideOrEqual -BasePath $repoRoot -CandidatePath $outputRootFull) {
  throw "OutputRoot must be outside the repository root."
}
New-Item -ItemType Directory -Force -Path $outputRootFull | Out-Null

$zipPath = Join-Path (Split-Path -Parent $packageContainerFull) "$packageLabel.zip"
$checksumPath = "$zipPath.sha256"
if (-not (Test-Path -LiteralPath $zipPath)) {
  throw "Package zip is missing: $zipPath"
}
if (-not (Test-Path -LiteralPath $checksumPath)) {
  throw "Package checksum is missing: $checksumPath"
}

$expectedZipHash = ((Get-Content -LiteralPath $checksumPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actualZipHash = Get-CheckedHash -Path $zipPath
if ($actualZipHash -ne $expectedZipHash) {
  throw "Package zip checksum mismatch."
}
if (-not [string]::IsNullOrWhiteSpace([string]$metadata.zipSha256) -and $metadata.zipSha256 -ne "see-adjacent-sha256-file" -and $metadata.zipSha256.ToLowerInvariant() -ne $actualZipHash) {
  throw "Package metadata zipSha256 does not match adjacent checksum."
}

$resolvedMakensisPath = Resolve-MakensisPath -ExplicitPath $MakensisPath
$buildDir = Join-Path $outputRootFull "$packageLabel-nsis-build"
$setupPath = Join-Path $outputRootFull "$packageLabel-Setup.exe"
$setupChecksumPath = "$setupPath.sha256"
$installerIconPath = Join-Path $repoRoot "packaging\assets\installer.ico"

if (Test-Path -LiteralPath $buildDir) {
  throw "Installer build output already exists: $buildDir"
}
if ((Test-Path -LiteralPath $setupPath) -or (Test-Path -LiteralPath $setupChecksumPath)) {
  throw "Installer output already exists for package label: $packageLabel"
}
if (-not (Test-Path -LiteralPath $installerIconPath)) {
  throw "Installer icon is missing: packaging\assets\installer.ico"
}

New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
Copy-Item -LiteralPath $zipPath -Destination (Join-Path $buildDir (Split-Path -Leaf $zipPath))
Copy-Item -LiteralPath $checksumPath -Destination (Join-Path $buildDir (Split-Path -Leaf $checksumPath))
Copy-Item -LiteralPath $installerIconPath -Destination (Join-Path $buildDir "installer.ico")

$installScriptPath = Join-Path $buildDir "install_operator_package.ps1"
$installScript = @"
param()
`$ErrorActionPreference = 'Stop'

function Write-InstallerStatus {
  param([string]`$Message)
  Write-Host "[installer] `$Message"
}

function Test-PathInsideOrEqual {
  param(
    [string]`$BasePath,
    [string]`$CandidatePath
  )

  `$baseFullPath = [System.IO.Path]::GetFullPath(`$BasePath)
  `$candidateFullPath = [System.IO.Path]::GetFullPath(`$CandidatePath)
  if (`$candidateFullPath.Equals(`$baseFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    return `$true
  }
  if (-not `$baseFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
    `$baseFullPath = `$baseFullPath + [System.IO.Path]::DirectorySeparatorChar
  }
  return `$candidateFullPath.StartsWith(`$baseFullPath, [System.StringComparison]::OrdinalIgnoreCase)
}

function Invoke-ShortcutInstaller {
  param(
    [string]`$PackageRoot,
    [bool]`$CheckOnly
  )

  `$shortcutScript = Join-Path `$PackageRoot 'launcher\install_shortcuts.ps1'
  if (-not (Test-Path -LiteralPath `$shortcutScript)) {
    throw 'Shortcut installer script missing in package.'
  }

  `$shortcutArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', `$shortcutScript)
  if (`$CheckOnly) {
    `$shortcutArgs += '-CheckOnly'
  }
  if (-not [string]::IsNullOrWhiteSpace(`$env:EWC_INSTALLER_DESKTOP_DIR)) {
    `$shortcutArgs += @('-DesktopDirectory', `$env:EWC_INSTALLER_DESKTOP_DIR)
  }
  if (-not [string]::IsNullOrWhiteSpace(`$env:EWC_INSTALLER_START_MENU_DIR)) {
    `$shortcutArgs += @('-StartMenuDirectory', `$env:EWC_INSTALLER_START_MENU_DIR)
  }

  Push-Location `$PackageRoot
  try {
    & powershell.exe @shortcutArgs
    if (`$LASTEXITCODE -ne 0) {
      throw "Shortcut installer failed with exit code `$LASTEXITCODE."
    }
  } finally {
    Pop-Location
  }
}

`$packageLabel = '$packageLabel'
`$expectedSourceCommit = '$($metadata.sourceCommit)'
`$expectedFrontendMode = '$($metadata.frontendMode)'
`$expectedRuntimeMode = '$($metadata.runtimeMode)'
`$zipPath = Join-Path `$PSScriptRoot (`$packageLabel + '.zip')
`$shaPath = Join-Path `$PSScriptRoot (`$packageLabel + '.zip.sha256')

if (-not (Test-Path -LiteralPath `$zipPath)) { throw "Payload zip missing: `$zipPath" }
if (-not (Test-Path -LiteralPath `$shaPath)) { throw "Checksum file missing: `$shaPath" }

`$expectedHash = ((Get-Content -Raw -LiteralPath `$shaPath).Trim() -split '\s+')[0].ToLowerInvariant()
`$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath `$zipPath).Hash.ToLowerInvariant()
if (`$actualHash -ne `$expectedHash) {
  throw "Payload checksum mismatch. Expected `$expectedHash but got `$actualHash"
}

if ([string]::IsNullOrWhiteSpace(`$env:EWC_INSTALL_BASE)) {
  `$installBase = Join-Path `$env:LOCALAPPDATA 'Programs\ExtrusionWebConsole'
} else {
  `$installBase = [System.IO.Path]::GetFullPath(`$env:EWC_INSTALL_BASE)
}

New-Item -ItemType Directory -Force -Path `$installBase | Out-Null
`$staging = Join-Path `$installBase ('_staging_' + `$packageLabel + '_' + (Get-Date -Format 'yyyyMMddHHmmss'))
New-Item -ItemType Directory -Force -Path `$staging | Out-Null

try {
  Expand-Archive -LiteralPath `$zipPath -DestinationPath `$staging -Force
  `$rootA = Join-Path `$staging 'ExtrusionWebConsole'
  if (Test-Path -LiteralPath (Join-Path `$rootA 'package-build-info.json')) {
    `$expandedRoot = `$rootA
  } elseif (Test-Path -LiteralPath (Join-Path `$staging 'package-build-info.json')) {
    `$expandedRoot = `$staging
  } else {
    throw 'Expanded package metadata not found.'
  }

  `$metadataPath = Join-Path `$expandedRoot 'package-build-info.json'
  `$metadata = Get-Content -Raw -LiteralPath `$metadataPath | ConvertFrom-Json
  if (`$metadata.sourceCommit -ne `$expectedSourceCommit) { throw "Unexpected sourceCommit: `$(`$metadata.sourceCommit)" }
  if (`$metadata.frontendMode -ne `$expectedFrontendMode) { throw "Unexpected frontendMode: `$(`$metadata.frontendMode)" }
  if (`$metadata.runtimeMode -ne `$expectedRuntimeMode) { throw "Unexpected runtimeMode: `$(`$metadata.runtimeMode)" }
  if (`$metadata.frontendBuildMetadataPresent -ne `$true) { throw 'frontendBuildMetadataPresent is not true.' }

  if (`$env:EWC_INSTALLER_CHECK_ONLY -eq '1') {
    Invoke-ShortcutInstaller -PackageRoot `$expandedRoot -CheckOnly `$true
    if (Test-Path -LiteralPath `$staging) {
      Remove-Item -LiteralPath `$staging -Recurse -Force
    }
    Write-InstallerStatus 'CheckOnly completed. No package was installed and no shortcuts were written.'
    exit 0
  }

  `$finalDir = Join-Path `$installBase `$packageLabel
  if (Test-Path -LiteralPath `$finalDir) {
    `$existingMetadataPath = Join-Path `$finalDir 'package-build-info.json'
    if (-not (Test-Path -LiteralPath `$existingMetadataPath)) {
      throw "Install target already exists without package metadata: `$finalDir"
    }
    `$existingMetadata = Get-Content -Raw -LiteralPath `$existingMetadataPath | ConvertFrom-Json
    if (`$existingMetadata.sourceCommit -ne `$expectedSourceCommit -or `$existingMetadata.frontendMode -ne `$expectedFrontendMode -or `$existingMetadata.runtimeMode -ne `$expectedRuntimeMode) {
      throw "Install target already exists with different metadata: `$finalDir"
    }
    if (Test-Path -LiteralPath `$staging) {
      Remove-Item -LiteralPath `$staging -Recurse -Force
    }
    `$expandedRoot = `$finalDir
  } else {
    Move-Item -LiteralPath `$expandedRoot -Destination `$finalDir
    if (Test-Path -LiteralPath `$staging) {
      Remove-Item -LiteralPath `$staging -Recurse -Force
    }
    `$expandedRoot = `$finalDir
  }

  `$shortcutCheckOnly = (`$env:EWC_INSTALLER_SHORTCUT_CHECK_ONLY -eq '1')
  Invoke-ShortcutInstaller -PackageRoot `$expandedRoot -CheckOnly `$shortcutCheckOnly
  Write-InstallerStatus "Installed Extrusion Web Console to `$expandedRoot"
  if (`$shortcutCheckOnly) {
    Write-InstallerStatus 'Shortcut installer check-only completed; no shortcuts were written.'
  } else {
    Write-InstallerStatus 'Desktop and Start menu Extrusion Web Console tray shortcuts have been created or refreshed.'
  }
} catch {
  if (Test-Path -LiteralPath `$staging) {
    if (Test-PathInsideOrEqual -BasePath `$installBase -CandidatePath `$staging) {
      Remove-Item -LiteralPath `$staging -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  throw
}
"@
$installScript | Set-Content -LiteralPath $installScriptPath -Encoding UTF8

$nsiPath = Join-Path $buildDir "installer.nsi"
$nsi = @"
Unicode true
!include LogicLib.nsh

Name "Extrusion Web Console"
OutFile "$(Escape-NsisString $setupPath)"
Icon "installer.ico"
RequestExecutionLevel user
SetCompressor /SOLID lzma
InstallDir "`$LOCALAPPDATA\Programs\ExtrusionWebConsole\$packageLabel"
ShowInstDetails show

Function .onInit
  ReadEnvStr `$0 "EWC_INSTALLER_CHECK_ONLY"
  `$`{If`} `$0 == "1"
    SetSilent silent
  `$`{EndIf`}
FunctionEnd

Section "Install"
  InitPluginsDir
  SetOutPath "`$PLUGINSDIR"
  File "install_operator_package.ps1"
  File "$(Split-Path -Leaf $zipPath)"
  File "$(Split-Path -Leaf $checksumPath)"
  DetailPrint "Installing Extrusion Web Console package $packageLabel"
  nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "`$PLUGINSDIR\install_operator_package.ps1"'
  Pop `$0
  `$`{If`} `$0 != 0
    DetailPrint "Install script failed with exit code `$0"
    Abort "Install script failed with exit code `$0"
  `$`{EndIf`}
SectionEnd
"@
$nsi | Set-Content -LiteralPath $nsiPath -Encoding UTF8

Push-Location $buildDir
try {
  & $resolvedMakensisPath $nsiPath
  if ($LASTEXITCODE -ne 0) {
    throw "makensis failed with exit code $LASTEXITCODE."
  }
} finally {
  Pop-Location
}

if (-not (Test-Path -LiteralPath $setupPath)) {
  throw "NSIS did not create installer output: $setupPath"
}

$setupHash = Get-CheckedHash -Path $setupPath
"$setupHash  $(Split-Path -Leaf $setupPath)" | Set-Content -LiteralPath $setupChecksumPath -Encoding ASCII

Write-InstallerBuildInfo "makensis: $resolvedMakensisPath"
Write-InstallerBuildInfo "package sourceCommit: $($metadata.sourceCommit)"
Write-InstallerBuildInfo "package frontendMode: $($metadata.frontendMode)"
Write-InstallerBuildInfo "package runtimeMode: $($metadata.runtimeMode)"
Write-InstallerBuildInfo "installer output: $setupPath"
Write-InstallerBuildInfo "installer sha256: $setupHash"
Write-InstallerBuildInfo "check-only smoke: set EWC_INSTALLER_CHECK_ONLY=1 and run the EXE with Start-Process -Wait -PassThru"
