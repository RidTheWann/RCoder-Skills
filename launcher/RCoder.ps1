[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$AppRoot = Split-Path -Parent $PSScriptRoot
$SkillSource = Join-Path $AppRoot 'skills\rcoder'
$CatalogPath = Join-Path $AppRoot 'targets.json'
$PackagePath = Join-Path $AppRoot 'package.json'
$HomeRoot = [IO.Path]::GetFullPath($HOME)

if (-not (Test-Path -LiteralPath (Join-Path $SkillSource 'SKILL.md') -PathType Leaf)) {
    throw "The bundled RCoder skill is missing: $SkillSource"
}
if (-not (Test-Path -LiteralPath $CatalogPath -PathType Leaf)) {
    throw "The RCoder target catalog is missing: $CatalogPath"
}

$Catalog = Get-Content -LiteralPath $CatalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Version = 'unknown'
if (Test-Path -LiteralPath $PackagePath -PathType Leaf) {
    $Version = (Get-Content -LiteralPath $PackagePath -Raw -Encoding UTF8 | ConvertFrom-Json).version
}

function Get-BackupDirectories {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $Path -Directory -Filter 'install-*' | Sort-Object -Property Name)
}

function Test-SameDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )
    if (-not (Test-Path -LiteralPath $Left -PathType Container)) { return $false }
    if (-not (Test-Path -LiteralPath $Right -PathType Container)) { return $false }

    $leftFiles = @(Get-ChildItem -LiteralPath $Left -File -Recurse |
        ForEach-Object { $_.FullName.Substring($Left.Length).TrimStart([char[]]@([char]92, [char]47)) } |
        Sort-Object)
    $rightFiles = @(Get-ChildItem -LiteralPath $Right -File -Recurse |
        ForEach-Object { $_.FullName.Substring($Right.Length).TrimStart([char[]]@([char]92, [char]47)) } |
        Sort-Object)

    if (($leftFiles -join [Environment]::NewLine) -ne ($rightFiles -join [Environment]::NewLine)) { return $false }
    foreach ($relative in $leftFiles) {
        $leftHash = (Get-FileHash -LiteralPath (Join-Path $Left $relative) -Algorithm SHA256).Hash
        $rightHash = (Get-FileHash -LiteralPath (Join-Path $Right $relative) -Algorithm SHA256).Hash
        if ($leftHash -ne $rightHash) { return $false }
    }
    return $true
}

function Assert-NoReparsePoint {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $baseFull = [IO.Path]::GetFullPath($Base)
    $pathFull = [IO.Path]::GetFullPath($Path)
    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    $basePrefix = $baseFull
    if (-not $basePrefix.EndsWith([string][IO.Path]::DirectorySeparatorChar)) {
        $basePrefix += [IO.Path]::DirectorySeparatorChar
    }

    if ($pathFull.Equals($baseFull, $comparison)) {
        $relative = ''
    }
    elseif ($pathFull.StartsWith($basePrefix, $comparison)) {
        $relative = $pathFull.Substring($basePrefix.Length)
    }
    else {
        throw "Refusing to write outside the selected scope: $Path"
    }

    $current = $baseFull
    foreach ($segment in ($relative -split '[\\/]' | Where-Object { $_ })) {
        $current = Join-Path $current $segment
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing to follow a symbolic link or reparse point: $current"
            }
        }
    }
}

function Invoke-RCoderTarget {
    param(
        [Parameter(Mandatory = $true)][object]$Target,
        [Parameter(Mandatory = $true)][ValidateSet('project', 'user')][string]$Scope,
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][ValidateSet('install', 'uninstall')][string]$Action,
        [string]$Features = 'rsaver,rscan'
    )
    $selectedFeatures = @()
    foreach ($part in ($Features -split ',')) {
        $name = $part.Trim().ToLowerInvariant()
        if ($name -in @('rsaver', 'rscan') -and $selectedFeatures -notcontains $name) { $selectedFeatures += $name }
    }

    $relativeRoot = if ($Scope -eq 'project') { [string]$Target.project_root } else { [string]$Target.user_root }
    $targetRoot = [IO.Path]::GetFullPath((Join-Path $Base $relativeRoot))
    $skillsRoot = Join-Path $targetRoot 'skills'
    $destination = Join-Path $skillsRoot 'rcoder'
    $backupParent = Join-Path $targetRoot '.rcoder-backups'
    $backupRoot = Join-Path $backupParent 'rcoder'
    $legacyBackupRoot = Join-Path $backupParent ([string]$Target.id)

    Assert-NoReparsePoint -Base $Base -Path $destination
    Assert-NoReparsePoint -Base $Base -Path $backupRoot
    Assert-NoReparsePoint -Base $Base -Path $legacyBackupRoot

    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)

    if ($Action -eq 'uninstall') {
        Write-Host "Uninstall $($Target.label): $destination"
        if (Test-Path -LiteralPath $destination -PathType Container) {
            New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
            Move-Item -LiteralPath $destination -Destination (Join-Path $backupRoot "uninstalled-$stamp")
        }
        else {
            Write-Host '  No active RCoder installation was found.'
        }

        $backups = @(Get-BackupDirectories -Path $backupRoot)
        if ($backups.Count -eq 0) { $backups = @(Get-BackupDirectories -Path $legacyBackupRoot) }
        if ($backups.Count -gt 0) {
            New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
            Move-Item -LiteralPath $backups[-1].FullName -Destination $destination
            Write-Host "  Restored previous installation: $destination"
        }
        $featureManifest = Join-Path $targetRoot '.rcoder-features.json'
        if (Test-Path -LiteralPath $featureManifest) { Remove-Item -LiteralPath $featureManifest -Force }
        return
    }

    if (Test-SameDirectory -Left $SkillSource -Right $destination) {
        Write-Host "Already current: $($Target.label) ($destination)"
        return
    }

    Write-Host "Install target: $($Target.label) ($Scope) -> $destination"
    New-Item -ItemType Directory -Path $skillsRoot, $backupRoot -Force | Out-Null
    $stage = Join-Path $skillsRoot ".rcoder-stage-$stamp"
    $savedBackup = $null

    try {
        Copy-Item -LiteralPath $SkillSource -Destination $stage -Recurse
        if (Test-Path -LiteralPath $destination -PathType Container) {
            $savedBackup = Join-Path $backupRoot "install-$stamp"
            Move-Item -LiteralPath $destination -Destination $savedBackup
            Write-Host "  Backed up previous installation: $savedBackup"
        }
        Move-Item -LiteralPath $stage -Destination $destination
        Write-Host "Installed RCoder $Version for $($Target.label): $destination"
        $featureManifest = Join-Path $targetRoot '.rcoder-features.json'
        $state = @{schema_version=1;version=$Version;rsaver=($selectedFeatures -contains 'rsaver');rscan=($selectedFeatures -contains 'rscan')}|ConvertTo-Json
        Set-Content -LiteralPath $featureManifest -Value $state -Encoding UTF8
        Write-Host "Enabled optional tools: $Features"
    }
    catch {
        if (Test-Path -LiteralPath $stage) {
            Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
        }
        if ($savedBackup -and (Test-Path -LiteralPath $savedBackup) -and -not (Test-Path -LiteralPath $destination)) {
            Move-Item -LiteralPath $savedBackup -Destination $destination
        }
        throw
    }
}

function Show-SupportedTargets {
    Write-Host ''
    Write-Host 'Supported Agentic AI and CLI hosts'
    for ($index = 0; $index -lt $Catalog.targets.Count; $index++) {
        $target = $Catalog.targets[$index]
        Write-Host (' {0,2}. {1,-30} {2}' -f ($index + 1), $target.label, $target.id)
    }
}

function Show-OptionalTools {
    Write-Host ''
    Write-Host 'Optional tools:'
    Write-Host '  1. RSaver   Context pruning, budgeting, and re-anchoring for long sessions'
    Write-Host '  2. RScan    Read-only project scan with ranked development options at session start'
}

function Read-FeatureSelection {
    Show-OptionalTools
    Write-Host '  1. Both tools (default)'
    Write-Host '  2. RSaver only'
    Write-Host '  3. RScan only'
    Write-Host '  4. Neither'
    $choice = (Read-Host 'Enable optional tools').Trim()
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = '1' }
    if ($choice -notin @('1', '2', '3', '4')) { throw "Invalid optional tool selection: $choice" }
    return @{1='rsaver,rscan';2='rsaver';3='rscan';4='none'}[[int]$choice]
}

function Read-TargetSelection {
    Show-SupportedTargets
    $selection = (Read-Host 'Select targets by number (comma-separated), or A for all').Trim()
    if ($selection -match '^(?i:a|all)$') { return @($Catalog.targets) }

    $indices = @()
    foreach ($value in ($selection -split ',')) {
        $number = 0
        if (-not [int]::TryParse($value.Trim(), [ref]$number) -or
            $number -lt 1 -or $number -gt $Catalog.targets.Count) {
            throw "Invalid target selection: $selection"
        }
        if (-not $indices.Contains($number)) { $indices += $number }
    }
    return @($indices | ForEach-Object { $Catalog.targets[$_ - 1] })
}

try {
    while ($true) {
        Write-Host ''
        Write-Host "RCoder $Version - Agent Skill Manager"
        Write-Host '  1. Install / Update RCoder'
        Write-Host '  2. Uninstall RCoder'
        Write-Host '  3. Show supported agents'
        Write-Host '  0. Exit'

        $actionChoice = (Read-Host 'Choose an action').Trim()
        if ($actionChoice -eq '0' -or [string]::IsNullOrWhiteSpace($actionChoice)) { break }
        if ($actionChoice -eq '3') { Show-SupportedTargets; continue }
        if ($actionChoice -ne '1' -and $actionChoice -ne '2') {
            Write-Warning 'Invalid action selection.'
            continue
        }

        $selectedTargets = @(Read-TargetSelection)
        if ($selectedTargets.Count -eq 0) {
            Write-Warning 'No targets selected.'
            continue
        }

        Write-Host ''
        Write-Host '  1. Project - current project only'
        Write-Host '  2. User - available across projects'
        $scopeChoice = (Read-Host 'Choose installation scope').Trim()
        if ($scopeChoice -ne '1' -and $scopeChoice -ne '2') {
            Write-Warning 'Invalid scope selection.'
            continue
        }
        $scope = if ($scopeChoice -eq '1') { 'project' } else { 'user' }

        $features = 'rsaver,rscan'
        if ($actionChoice -eq '1') { $features = Read-FeatureSelection }
        if ($actionChoice -eq '2') {
            $confirmation = (Read-Host 'Confirm uninstall and restore the previous installation? (y/N)').Trim()
            if ($confirmation.ToLowerInvariant() -notin @('y', 'yes')) {
                Write-Host 'Uninstall cancelled.'
                continue
            }
        }

        $base = $HomeRoot
        if ($scope -eq 'project') {
            $defaultProject = (Get-Location).Path
            $entered = Read-Host "Project directory [$defaultProject]"
            $base = if ([string]::IsNullOrWhiteSpace($entered)) { $defaultProject } else { $entered.Trim('"') }
            if (-not (Test-Path -LiteralPath $base -PathType Container)) {
                Write-Warning "Project directory does not exist: $base"
                continue
            }
            $base = (Resolve-Path -LiteralPath $base).Path
        }

        $seen = @{}
        foreach ($target in $selectedTargets) {
            $rootPath = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $destinationKey = [IO.Path]::GetFullPath(
                (Join-Path $base (Join-Path $rootPath 'skills\rcoder'))
            ).ToLowerInvariant()

            if ($seen.ContainsKey($destinationKey)) {
                Write-Host "Skipped duplicate discovery root for $($target.label)."
                continue
            }
            $seen[$destinationKey] = $true

            $action = if ($actionChoice -eq '1') { 'install' } else { 'uninstall' }
            Invoke-RCoderTarget -Target $target -Scope $scope -Base $base -Action $action -Features $features
        }

        Write-Host ''
        Write-Host 'Operation completed. Start a new agent session or reload its skills.'
    }
}
catch {
    Write-Error "RCoder launcher error: $($_.Exception.Message)"
    exit 1
}
