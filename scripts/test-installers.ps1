$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$filesToParse = @(
    (Join-Path $repoRoot 'install.ps1'),
    (Join-Path $repoRoot 'launcher/RCoder.ps1')
)
foreach ($file in $filesToParse) {
    $tokens = $null; $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count -gt 0) { throw "PowerShell syntax error in $file : $($parseErrors[0].Message)" }
}
$catalog = Get-Content -LiteralPath (Join-Path $repoRoot 'targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$installer = Join-Path $repoRoot 'scripts/install.ps1'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('rcoder-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    foreach ($target in $catalog.targets) {
        foreach ($scope in @('project', 'user')) {
            $project = Join-Path $temp "$($target.id)-$scope-project"
            $homeDir = Join-Path $temp "$($target.id)-$scope-home"
            New-Item -ItemType Directory -Force -Path $project,$homeDir | Out-Null
            $base = if ($scope -eq 'project') { $project } else { $homeDir }
            $relativeRoot = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $discovery = Join-Path $base $relativeRoot
            $dest = Join-Path $discovery 'skills/rcoder'
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
            Set-Content -LiteralPath (Join-Path $dest 'original.txt') 'preserve this backup'

            & $installer -Target $target.id -Scope $scope -ProjectDir $project -HomeDir $homeDir -DryRun | Out-Null
            if (-not (Test-Path -LiteralPath (Join-Path $dest 'original.txt'))) { throw "Dry-run modified $($target.id)/$scope" }
            if (Test-Path -LiteralPath (Join-Path $dest 'SKILL.md')) { throw "Dry-run installed $($target.id)/$scope" }

            & $installer -Target $target.id -Scope $scope -ProjectDir $project -HomeDir $homeDir
            if (-not (Test-Path -LiteralPath (Join-Path $dest 'SKILL.md'))) { throw "Install failed: $($target.id)/$scope" }
            $backupRoot = Join-Path (Join-Path $discovery '.rcoder-backups') 'rcoder'
            $backups = @(Get-ChildItem -LiteralPath $backupRoot -Directory -Filter 'install-*')
            if ($backups.Count -ne 1) { throw "Expected one backup for $($target.id)/$scope, got $($backups.Count)" }

            & $installer -Target $target.id -Scope $scope -ProjectDir $project -HomeDir $homeDir
            $afterRepeat = @(Get-ChildItem -LiteralPath $backupRoot -Directory -Filter 'install-*')
            if ($afterRepeat.Count -ne 1) { throw "Repeat install was not idempotent for $($target.id)/$scope" }

            & $installer -Target $target.id -Scope $scope -ProjectDir $project -HomeDir $homeDir -Uninstall
            if (-not (Test-Path -LiteralPath (Join-Path $dest 'original.txt'))) { throw "Backup restore failed: $($target.id)/$scope" }
            if (Test-Path -LiteralPath (Join-Path $dest 'SKILL.md')) { throw "Uninstall left RCoder: $($target.id)/$scope" }
            Write-Output "PASS $($target.id) / $scope"
        }
    }
    Write-Output 'PASS all 40 PowerShell target/scope combinations'
    $featureOutput = & $installer -ListFeatures
    $featureText = $featureOutput -join "`n"
    if ($featureText -notmatch 'RSaver:' -or $featureText -notmatch 'RScan:') { throw 'Feature descriptions are missing' }
    $featureProject = Join-Path $temp 'feature-project'
    $featureHome = Join-Path $temp 'feature-home'
    New-Item -ItemType Directory -Force -Path $featureProject,$featureHome | Out-Null
    & $installer -Target agents -Scope project -ProjectDir $featureProject -HomeDir $featureHome -Features rscan | Out-Null
    $featureManifest = Join-Path (Join-Path $featureProject '.agents') '.rcoder-features.json'
    $featureState = Get-Content -LiteralPath $featureManifest -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $featureState.rscan -or $featureState.rsaver) { throw 'Optional tool manifest is incorrect' }
    Write-Output 'PASS PowerShell optional tool selection'
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
