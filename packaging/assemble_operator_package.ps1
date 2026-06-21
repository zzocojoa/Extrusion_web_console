[CmdletBinding()]
param(
  [string]$OutputRoot = "C:\tmp\ExtrusionWebConsole-packages",
  [string]$PackageLabel = "",
  [ValidateSet("auto", "mock", "api")]
  [string]$FrontendMode = "auto",
  [switch]$CreateZip,
  [switch]$AllowIncompleteRuntime
)

$ErrorActionPreference = "Stop"

function Write-AssemblyInfo {
  param([string]$Message)
  Write-Host "[operator-package] $Message"
}

function ConvertTo-ForwardSlash {
  param([string]$Path)
  return $Path.Replace("\", "/")
}

function Get-SafeRelativePath {
  param(
    [string]$BasePath,
    [string]$FullPath
  )

  $baseFullPath = [System.IO.Path]::GetFullPath($BasePath)
  if (-not $baseFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
    $baseFullPath = $baseFullPath + [System.IO.Path]::DirectorySeparatorChar
  }
  $targetFullPath = [System.IO.Path]::GetFullPath($FullPath)
  $baseUri = New-Object System.Uri($baseFullPath)
  $targetUri = New-Object System.Uri($targetFullPath)
  $relativeUri = $baseUri.MakeRelativeUri($targetUri).ToString()
  return [System.Uri]::UnescapeDataString($relativeUri).Replace("/", "\")
}

function Resolve-RepoRelativePath {
  param(
    [string]$RepoRoot,
    [string]$RelativePath
  )

  if ([string]::IsNullOrWhiteSpace($RelativePath)) {
    throw "Manifest path is empty."
  }
  if ([System.IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains("..")) {
    throw "Manifest path must be relative and must not contain traversal markers: $RelativePath"
  }

  $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $RelativePath))
  $repoFullPath = [System.IO.Path]::GetFullPath($RepoRoot)
  if (-not $fullPath.StartsWith($repoFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Manifest path escapes repository root: $RelativePath"
  }
  return $fullPath
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

function Test-RuntimeMetadataPath {
  param([string]$Path)

  $normalized = (ConvertTo-ForwardSlash $Path).ToLowerInvariant()
  $fileName = [System.IO.Path]::GetFileName($normalized)

  if ($normalized -match "(^|/)[^/]+\.dist-info(/|$)") {
    return $true
  }
  if ($fileName -match "^(metadata|record|wheel|entry_points\.txt)$") {
    return $true
  }
  if ($fileName -match "^(license|notice|copying)(\.|$)") {
    return $true
  }
  return $false
}

function Get-RuntimePruneClass {
  param([string]$Path)

  $normalized = (ConvertTo-ForwardSlash $Path).ToLowerInvariant()
  if ($normalized -match "(^|/)\.agents(/|$)") {
    return "agent"
  }

  if (Test-RuntimeMetadataPath $Path) {
    return ""
  }

  if ($normalized -match "(^|/)__pycache__(/|$)" -or $normalized -match "\.(pyc|pyo)$") {
    return "cache"
  }
  if ($normalized -match "(^|/)\.pytest_cache(/|$)") {
    return "cache"
  }
  if ($normalized -match "(^|/)(test|tests|testing|testsuite)(/|$)") {
    return "test"
  }
  return ""
}

function Copy-ManifestFile {
  param(
    [string]$Source,
    [string]$Destination
  )

  $destinationParent = Split-Path -Parent $Destination
  New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
  Copy-Item -LiteralPath $Source -Destination $Destination
}

function Copy-ManifestDirectory {
  param(
    [string]$Source,
    [string]$Destination,
    [bool]$FilterRuntime
  )

  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  Get-ChildItem -LiteralPath $Source -Force -Recurse | ForEach-Object {
    $relative = Get-SafeRelativePath -BasePath $Source -FullPath $_.FullName
    $pruneClass = Get-RuntimePruneClass $relative
    if ($pruneClass -eq "cache") {
      if ($FilterRuntime) {
        $script:runtimeCachePrunedCount += 1
      } else {
        $script:sourceCachePrunedCount += 1
      }
      return
    }
    if ($FilterRuntime) {
      if ($pruneClass -eq "agent") {
        $script:runtimeAgentPrunedCount += 1
        return
      }
      if ($pruneClass -eq "test") {
        $script:runtimeTestPrunedCount += 1
        return
      }
      if (Test-RuntimeMetadataPath $relative) {
        $script:runtimeMetadataPreservedCount += 1
      }
    }

    $target = Join-Path $Destination $relative
    if ($_.PSIsContainer) {
      New-Item -ItemType Directory -Force -Path $target | Out-Null
    } else {
      $targetParent = Split-Path -Parent $target
      New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
      Copy-Item -LiteralPath $_.FullName -Destination $target
    }
  }
}

function Get-RelativePackagePath {
  param(
    [string]$PackageRoot,
    [string]$FullPath
  )

  return ConvertTo-ForwardSlash (Get-SafeRelativePath -BasePath $PackageRoot -FullPath $FullPath)
}

function Test-DenylistedPackagePath {
  param([string]$RelativePath)

  $path = ConvertTo-ForwardSlash $RelativePath
  $lower = $path.ToLowerInvariant()
  $fileName = [System.IO.Path]::GetFileName($path)

  $blockedPrefixes = @(
    ".git/",
    ".gstack/",
    ".agents/",
    ".codex/",
    ".bkit-codex/",
    ".pytest_cache/",
    "frontend/node_modules/",
    "frontend/src/",
    "frontend/qa/",
    "tests/",
    "supabase/.branches/",
    "supabase/.temp/",
    "logs/",
    "tmp/",
    "temp/"
  )
  foreach ($prefix in $blockedPrefixes) {
    if ($lower -eq $prefix.TrimEnd("/") -or $lower.StartsWith($prefix)) {
      return $true
    }
  }

  if ($fileName -like ".env*") {
    return $true
  }
  if ($lower -match "(^|/)__pycache__(/|$)") {
    return $true
  }
  if ($lower -match "(^|/)\.pytest_cache(/|$)") {
    return $true
  }
  if ($lower.StartsWith(".venv/") -and $lower -match "(^|/)(test|tests|testing|testsuite)(/|$)") {
    return $true
  }
  if ($lower.StartsWith(".venv/") -and $lower -match "(^|/)\.agents(/|$)") {
    return $true
  }
  if ($lower -match "\.(dump|backup|db|db-shm|db-wal|sqlite|sqlite3|log|csv|zip|sha256|pyc|pyo)$") {
    return $true
  }

  return $false
}

function Assert-SupabasePackageAssets {
  param([string]$PackageRoot)

  $requiredSupabaseAssets = @(
    "supabase/config.toml",
    "supabase/README.md",
    "supabase/.gitignore",
    "supabase/functions/upload-metrics/index.ts",
    "supabase/migrations/20260608000001_create_all_metrics_upload_contract.sql"
  )

  foreach ($assetPath in $requiredSupabaseAssets) {
    $fullPath = Join-Path $PackageRoot $assetPath
    if (-not (Test-Path -LiteralPath $fullPath)) {
      throw "Package Supabase asset is missing: $assetPath"
    }
  }
}

function Test-TextFileForRedaction {
  param([string]$Path)

  $fileName = [System.IO.Path]::GetFileName($Path).ToLowerInvariant()
  $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
  $textExtensions = @(".bat", ".css", ".html", ".js", ".json", ".md", ".ps1", ".sql", ".toml", ".ts", ".txt")
  return $textExtensions.Contains($extension) -or $fileName -eq "version" -or $fileName -eq ".gitignore"
}

function Find-RedactionMatches {
  param([string]$PackageRoot)

  $matches = New-Object System.Collections.Generic.List[string]
  $patterns = @(
    @{ Name = "database-url-marker"; Regex = "postgres(?:ql)?://[^\s`"'<>)]+" },
    @{ Name = "authorization-bearer-marker"; Regex = "(?i)authorization\s*[:=]\s*bearer\s+\S+" },
    @{ Name = "credential-like-marker"; Regex = "(?i)(^|[^A-Z0-9_])(credential|secret|token|api[_ -]?key)\s*[:=]\s*['""]?[A-Za-z0-9._-]{8,}" },
    @{ Name = "jwt-like-marker"; Regex = "\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b" },
    @{ Name = "service-role-assignment-marker"; Regex = "(?i)(^|[^A-Z0-9_])service[_ -]role\s*[:=]" },
    @{ Name = "anon-key-assignment-marker"; Regex = "(?i)(^|[^A-Z0-9_])anon[_ -]key\s*[:=]" },
    @{ Name = "timestamp-style-csv-marker"; Regex = "\b\d{8}_\d{6}\.csv\b" },
    @{ Name = "operational-filename-family-marker"; Regex = "(?i)\bfactory[_-][A-Za-z0-9_-]*log\b" },
    @{ Name = "windows-absolute-path-marker"; Regex = "\b[A-Za-z]:\\[^\r\n`"'<>)]+" }
  )

  Get-ChildItem -LiteralPath $PackageRoot -Force -Recurse -File | ForEach-Object {
    $relativePath = Get-RelativePackagePath -PackageRoot $PackageRoot -FullPath $_.FullName
    if ($relativePath.StartsWith(".venv/")) {
      return
    }
    if (-not (Test-TextFileForRedaction $_.FullName)) {
      return
    }
    if ($_.Length -gt 5MB) {
      return
    }

    $content = Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($pattern in $patterns) {
      if ([regex]::IsMatch($content, $pattern.Regex)) {
        $matches.Add("$($pattern.Name):$relativePath")
      }
    }
  }

  return $matches
}

function Assert-PackageContents {
  param(
    [string]$PackageRoot,
    [object]$Manifest,
    [bool]$RuntimeIncomplete
  )

  foreach ($requiredPath in $Manifest.requiredPaths) {
    $fullPath = Join-Path $PackageRoot $requiredPath
    if (-not (Test-Path -LiteralPath $fullPath)) {
      throw "Package required path is missing: $requiredPath"
    }
  }

  foreach ($checkPath in $Manifest.operatorReadyChecks) {
    $fullPath = Join-Path $PackageRoot $checkPath
    if (-not (Test-Path -LiteralPath $fullPath)) {
      if ($RuntimeIncomplete -and $checkPath -eq ".venv/Scripts/python.exe") {
        continue
      }
      throw "Operator readiness check failed: $checkPath"
    }
  }

  Assert-SupabasePackageAssets -PackageRoot $PackageRoot

  $denylistMatches = New-Object System.Collections.Generic.List[string]
  Get-ChildItem -LiteralPath $PackageRoot -Force -Recurse | ForEach-Object {
    $relativePath = Get-RelativePackagePath -PackageRoot $PackageRoot -FullPath $_.FullName
    if (Test-DenylistedPackagePath $relativePath) {
      $denylistMatches.Add($relativePath)
    }
  }

  if ($denylistMatches.Count -gt 0) {
    throw "Package denylist validation failed. Match count: $($denylistMatches.Count). First match: $($denylistMatches[0])"
  }

  $redactionMatches = @(Find-RedactionMatches -PackageRoot $PackageRoot)
  if ($redactionMatches.Count -gt 0) {
    throw "Package redaction validation failed. Match count: $($redactionMatches.Count). First match: $($redactionMatches[0])"
  }

  Write-AssemblyInfo "required paths: present"
  Write-AssemblyInfo "supabase assets: present"
  Write-AssemblyInfo "operator readiness: $(if ($RuntimeIncomplete) { 'incomplete runtime allowed' } else { 'ready' })"
  Write-AssemblyInfo "denylist matches: 0"
  Write-AssemblyInfo "redaction matches: 0"
  Write-AssemblyInfo "source cache pruned: $script:sourceCachePrunedCount"
  Write-AssemblyInfo "runtime cache pruned: $script:runtimeCachePrunedCount"
  Write-AssemblyInfo "runtime test segments pruned: $script:runtimeTestPrunedCount"
  Write-AssemblyInfo "runtime agent entries pruned: $script:runtimeAgentPrunedCount"
  Write-AssemblyInfo "runtime metadata preserved: $script:runtimeMetadataPreservedCount"
}

function Get-FrontendBuildInfo {
  param([string]$RepoRoot)

  $buildInfoPath = Join-Path $RepoRoot "frontend/dist/frontend-build-info.json"
  if (-not (Test-Path -LiteralPath $buildInfoPath)) {
    return [pscustomobject]@{
      Mode = "unknown"
      MetadataPresent = $false
      MetadataPath = "frontend/dist/frontend-build-info.json"
    }
  }

  try {
    $decoded = Get-Content -LiteralPath $buildInfoPath -Raw | ConvertFrom-Json
  } catch {
    throw "Frontend build metadata is invalid JSON: frontend/dist/frontend-build-info.json"
  }

  $mode = [string]$decoded.frontendMode
  if ($mode -ne "mock" -and $mode -ne "api") {
    throw "Frontend build metadata has unsupported frontendMode: $mode"
  }

  return [pscustomobject]@{
    Mode = $mode
    MetadataPresent = $true
    MetadataPath = "frontend/dist/frontend-build-info.json"
  }
}

function Resolve-FrontendMode {
  param(
    [string]$ExpectedMode,
    [object]$BuildInfo
  )

  if ($ExpectedMode -eq "auto") {
    return $BuildInfo.Mode
  }

  if (-not $BuildInfo.MetadataPresent) {
    throw "Frontend build metadata is missing. Run npm run build for mock mode or npm run build:api for API mode before package assembly."
  }

  if ($BuildInfo.Mode -ne $ExpectedMode) {
    throw "Frontend mode mismatch: expected $ExpectedMode but found $($BuildInfo.Mode). Rebuild frontend/dist with the matching npm build script before package assembly."
  }

  return $BuildInfo.Mode
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot ".."))
$manifestPath = Join-Path $scriptRoot "operator-package.manifest.json"

if (-not (Test-Path -LiteralPath $manifestPath)) {
  throw "Manifest file is missing: packaging/operator-package.manifest.json"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1) {
  throw "Unsupported manifest schemaVersion: $($manifest.schemaVersion)"
}
if ($manifest.packageRoot -ne "ExtrusionWebConsole") {
  throw "Unsupported packageRoot: $($manifest.packageRoot)"
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss-fff")
$sourceCommit = "unknown"
try {
  $sourceCommit = (& git -C $repoRoot rev-parse --short HEAD 2>$null).Trim()
  if ([string]::IsNullOrWhiteSpace($sourceCommit)) {
    $sourceCommit = "unknown"
  }
} catch {
  $sourceCommit = "unknown"
}

if ([string]::IsNullOrWhiteSpace($PackageLabel)) {
  $PackageLabel = "$($manifest.packageRoot)-$sourceCommit-$timestamp"
}
if ([System.IO.Path]::IsPathRooted($PackageLabel) -or $PackageLabel.Contains("..")) {
  throw "PackageLabel must be a folder name, not a path."
}

$outputRootFull = [System.IO.Path]::GetFullPath($OutputRoot)
if (Test-PathInsideOrEqual -BasePath $repoRoot -CandidatePath $outputRootFull) {
  throw "OutputRoot must be outside the repository root to avoid packaging generated output into source control."
}

$packageContainer = Join-Path $outputRootFull $PackageLabel
$packageRoot = Join-Path $packageContainer $manifest.packageRoot

if (Test-Path -LiteralPath $packageContainer) {
  throw "Package output already exists. Choose a new PackageLabel or omit it for timestamped output."
}

$frontendBuildInfo = Get-FrontendBuildInfo -RepoRoot $repoRoot
$resolvedFrontendMode = Resolve-FrontendMode -ExpectedMode $FrontendMode -BuildInfo $frontendBuildInfo

$runtimeIncomplete = $false
foreach ($entry in $manifest.includeAllowlist) {
  $source = Resolve-RepoRelativePath -RepoRoot $repoRoot -RelativePath $entry.source
  $isRequired = [bool]$entry.required
  $allowIncompleteForEntry = ($entry.allowIncompleteSwitch -eq "AllowIncompleteRuntime" -and $AllowIncompleteRuntime)

  if (-not (Test-Path -LiteralPath $source)) {
    if ($isRequired -and -not $allowIncompleteForEntry) {
      throw "Required package source is missing: $($entry.source)"
    }
    if ($allowIncompleteForEntry) {
      $runtimeIncomplete = $true
    }
    continue
  }

  $sourceItem = Get-Item -LiteralPath $source
  if ($entry.type -eq "file" -and $sourceItem.PSIsContainer) {
    throw "Manifest expected a file but found a directory: $($entry.source)"
  }
  if ($entry.type -eq "directory" -and -not $sourceItem.PSIsContainer) {
    throw "Manifest expected a directory but found a file: $($entry.source)"
  }
  if ($entry.type -ne "file" -and $entry.type -ne "directory") {
    throw "Unsupported manifest include type: $($entry.type)"
  }
}

New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
$script:runtimeCachePrunedCount = 0
$script:runtimeTestPrunedCount = 0
$script:runtimeAgentPrunedCount = 0
$script:runtimeMetadataPreservedCount = 0
$script:sourceCachePrunedCount = 0

foreach ($entry in $manifest.includeAllowlist) {
  $source = Resolve-RepoRelativePath -RepoRoot $repoRoot -RelativePath $entry.source
  $target = Join-Path $packageRoot $entry.target
  $isRequired = [bool]$entry.required
  $allowIncompleteForEntry = ($entry.allowIncompleteSwitch -eq "AllowIncompleteRuntime" -and $AllowIncompleteRuntime)

  if (-not (Test-Path -LiteralPath $source)) {
    if ($isRequired -and -not $allowIncompleteForEntry) {
      throw "Required package source is missing: $($entry.source)"
    }
    if ($allowIncompleteForEntry) {
      Write-AssemblyInfo "python runtime: missing, incomplete mode allowed"
      continue
    }
  }

  if ($entry.type -eq "file") {
    if ((Get-Item -LiteralPath $source).PSIsContainer) {
      throw "Manifest expected a file but found a directory: $($entry.source)"
    }
    Copy-ManifestFile -Source $source -Destination $target
  } elseif ($entry.type -eq "directory") {
    if (-not (Get-Item -LiteralPath $source).PSIsContainer) {
      throw "Manifest expected a directory but found a file: $($entry.source)"
    }
    $filterRuntime = ($entry.source -eq ".venv")
    Copy-ManifestDirectory -Source $source -Destination $target -FilterRuntime $filterRuntime
  } else {
    throw "Unsupported manifest include type: $($entry.type)"
  }
}

$buildInfo = [ordered]@{
  schemaVersion = 1
  packageName = $manifest.packageName
  packageRoot = $manifest.packageRoot
  packageLabel = $PackageLabel
  sourceCommit = $sourceCommit
  createdUtc = (Get-Date).ToUniversalTime().ToString("o")
  runtimeMode = $(if ($runtimeIncomplete) { "maintainer-prep-incomplete" } else { "operator-ready" })
  frontendMode = $resolvedFrontendMode
  frontendBuildMetadataPresent = [bool]$frontendBuildInfo.MetadataPresent
  frontendBuildInfoPath = $frontendBuildInfo.MetadataPath
  zipCreated = $false
  zipSha256 = $null
}
$buildInfoPath = Join-Path $packageRoot "package-build-info.json"
$buildInfo | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $buildInfoPath -Encoding UTF8

Assert-PackageContents -PackageRoot $packageRoot -Manifest $manifest -RuntimeIncomplete $runtimeIncomplete

$zipPath = $null
if ($CreateZip) {
  $zipPath = Join-Path $outputRootFull "$PackageLabel.zip"
  $checksumPath = "$zipPath.sha256"
  if ((Test-Path -LiteralPath $zipPath) -or (Test-Path -LiteralPath $checksumPath)) {
    throw "Zip or checksum output already exists for package label: $PackageLabel"
  }

  $buildInfo.zipCreated = $true
  $buildInfo.zipSha256 = "see-adjacent-sha256-file"
  $buildInfo | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $buildInfoPath -Encoding UTF8

  Compress-Archive -LiteralPath $packageRoot -DestinationPath $zipPath -CompressionLevel Optimal
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash.ToLowerInvariant()
  "$hash  $(Split-Path -Leaf $zipPath)" | Set-Content -LiteralPath $checksumPath -Encoding ASCII

  $buildInfo.zipSha256 = $hash
  $buildInfo | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $buildInfoPath -Encoding UTF8

  Write-AssemblyInfo "zip: created"
  Write-AssemblyInfo "zip checksum: recorded"
}

Write-AssemblyInfo "package output: $packageRoot"
Write-AssemblyInfo "frontend mode: $resolvedFrontendMode"
if ($zipPath) {
  Write-AssemblyInfo "zip output: $zipPath"
}
Write-AssemblyInfo "smoke guidance:"
Write-AssemblyInfo "  1. Run launcher/start_web_console.ps1 -CheckOnly from the package root."
Write-AssemblyInfo "  2. Run launcher/install_shortcuts.ps1 -CheckOnly from the package root."
Write-AssemblyInfo "  3. Start the package with launcher/start_web_console.ps1 -NoBrowser and smoke /, /upload, /logs, /settings, /api/health, /api/config, /api/audit?limit=1, and sanitized /api/runtime/local-supabase status fields."
