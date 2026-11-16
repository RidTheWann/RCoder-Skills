[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $appRoot 'skills\rcoder'
$catalogPath = Join-Path $appRoot 'targets.json'
$packagePath = Join-Path $appRoot 'package.json'

if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
    throw "The bundled RCoder skill is missing: $source"
}
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "The RCoder target catalog is missing: $catalogPath"
}
$catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
$version = 'unknown'
if (Test-Path -LiteralPath $packagePath -PathType Leaf) {
    $version = (Get-Content -LiteralPath $packagePath -Raw -Encoding UTF8 | ConvertFrom-Json).version
}
$homeRoot = [IO.Path]::GetFullPath($HOME)

function Get-BackupDirectories([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $Path -Directory -Filter 'install-*' | Sort-Object Name)
}

function Test-SameDirectory([string]$Left, [string]$Right) {
    if (-not (Test-Path -LiteralPath $Left -PathType Container) -or
        -not (Test-Path -LiteralPath $Right -PathType Container)) { return $false }
    $leftFiles = @(Get-ChildItem -LiteralPath $Left -File -Recurse | ForEach-Object {
        $_.FullName.Substring($Left.Length).TrimStart([char[]]@([char]92, [char]47))
    } | Sort-Object)
    $rightFiles = @(Get-ChildItem -LiteralPath $Right -File -Recurse | ForEach-Object {
        $_.FullName.Substring($Right.Length).TrimStart([char[]]@([char]92, [char]47))
    } | Sort-Object)
    if (($leftFiles -join "`n") -ne ($rightFiles -join "`n")) { return $false }
    foreach ($relative in $leftFiles) {
        $a = (Get-FileHash -LiteralPath (Join-Path $Left $relative) -Algorithm SHA256).Hash
        $b = (Get-FileHash -LiteralPath (Join-Path $Right $relative) -Algorithm SHA256).Hash
        if ($a -ne $b) { return $false }
    }
    return $true
}

function Assert-NoReparsePoint([string]$Base, [string]$Path) {
    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    $baseFull = [IO.Path]::GetFullPath($Base)
    $pathFull = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($baseFull)
    if ($baseFull.Length -gt $root.Length) {
        $baseFull = $baseFull.TrimEnd([char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar))
    }
    if ($pathFull.Equals($baseFull, $comparison)) { $relative = '' }
    else {
        $prefix = $baseFull
        if (-not $prefix.EndsWith([string][IO.Path]::DirectorySeparatorChar)) { $prefix += [IO.Path]::DirectorySeparatorChar }
        if (-not $pathFull.StartsWith($prefix, $comparison)) {
            throw "Refusing to write outside the selected scope: $Path"
        }
        $relative = $pathFull.Substring($prefix.Length)
    }
    $current = $baseFull
    foreach ($segment in ($relative -split '[\\/]+' | Where-Object { $_ })) {
        $current = Join-Path $current $segment
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing to follow a symbolic link or reparse point: $current"
            }
        }
    }
}

function Invoke-Target([object]$Target, [string]$Scope, [string]$Base, [string]$Action) {
    $relativeRoot = if ($Scope -eq 'project') { [string]$Target.project_root } else { [string]$Target.user_root }
    $targetRoot = [IO.Path]::GetFullPath((Join-Path $Base $relativeRoot))
    $skillsRoot = Join-Path $targetRoot 'skills'
    $destination = Join-Path $skillsRoot 'rcoder'
    $backupRoot = Join-Path (Join-Path $targetRoot '.rcoder-backups') ([string]$Target.id)
    Assert-NoReparsePoint -Base $Base -Path $destination
    Assert-NoReparsePoint -Base $Base -Path $backupRoot

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
        return
    }

    if (Test-SameDirectory -Left $source -Right $destination) {
        Write-Host "Already current: $($Target.label) ($destination)"
        return
    }
    New-Item -ItemType Directory -Path $skillsRoot, $backupRoot -Force | Out-Null
    $stage = Join-Path $skillsRoot ".rcoder-stage-$stamp"
    $savedBackup = $null
    try {
        Copy-Item -LiteralPath $source -Destination $stage -Recurse
        if (Test-Path -LiteralPath $destination) {
            $savedBackup = Join-Path $backupRoot "install-$stamp"
            Move-Item -LiteralPath $destination -Destination $savedBackup
            Write-Host "  Backed up previous installation: $savedBackup"
        }
        Move-Item -LiteralPath $stage -Destination $destination
        Write-Host "Installed RCoder $version for $($Target.label): $destination"
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

function Show-Targets {
    Write-Host ''
    Write-Host 'Supported coding agents and CLI hosts'
    $index = 1
    foreach ($target in $catalog.targets) {
        Write-Host (' {0,2}. {1,-30} {2}' -f $index, $target.label, $target.id)
        $index += 1
    }
}

try {
    while ($true) {
        Write-Host ''
        Write-Host "RCoder $version - Agent Skill Manager"
        Write-Host '  1. Install / Update RCoder'
        Write-Host '  2. Uninstall RCoder'
        Write-Host '  3. Show supported agents'
        Write-Host '  0. Exit'
        $actionChoice = (Read-Host 'Choose an action').Trim()
        if ($actionChoice -eq '0' -or [string]::IsNullOrWhiteSpace($actionChoice)) { break }
        if ($actionChoice -eq '3') { Show-Targets; continue }
        if ($actionChoice -ne '1' -and $actionChoice -ne '2') {
            Write-Warning 'Invalid action selection.'
            continue
        }

        Show-Targets
        $selection = (Read-Host 'Select one or more targets (for example 1,7,10; A = all)').Trim()
        if ($selection -match '(?i)^a(l(l)?)? {
            $selected = @($catalog.targets)
        }
        else {
            $indices = @($selection -split ',' | ForEach-Object {
                $number = 0
                if (-not [int]::TryParse($_.Trim(), [ref]$number) -or $number -lt 1 -or $number -gt $catalog.targets.Count) {
                    throw "Invalid target selection: $selection"
                }
                $number - 1
            } | Select-Object -Unique)
            $selected = @($indices | ForEach-Object { $catalog.targets[$_] })
        }
        if ($selected.Count -eq 0) { Write-Warning 'No targets selected.'; continue }

        Write-Host ''
        Write-Host '  1. Project - current project only'
        Write-Host '  2. User - available across projects'
        $scopeChoice = (Read-Host 'Choose installation scope').Trim()
        if ($scopeChoice -ne '1' -and $scopeChoice -ne '2') { Write-Warning 'Invalid scope.'; continue }
        $scope = if ($scopeChoice -eq '1') { 'project' } else { 'user' }
        if ($actionChoice -eq '2') {
            $confirmation = (Read-Host 'Confirm uninstall and backup the current RCoder folder? (y/N)').Trim()
            if ($confirmation -notmatch '^(?i:y|yes)
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
        foreach ($target in $selected) {
            $rootPath = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $key = [IO.Path]::GetFullPath((Join-Path $base (Join-Path $rootPath 'skills\rcoder'))).ToLowerInvariant()
            if ($seen.ContainsKey($key)) {
                Write-Host "Skipped duplicate discovery root for $($target.label)."
                continue
            }
            $seen[$key] = $true
            $action = if ($actionChoice -eq '1') { 'install' } else { 'uninstall' }
            Invoke-Target -Target $target -Scope $scope -Base $base -Action $action
        }
        Write-Host ''
        Write-Host 'Operation completed. Start a new agent session or reload its skills.'
    }
}
catch {
    Write-Error "RCoder launcher error: $($_.Exception.Message)"
    exit 1
}
) {
            $selected = @($catalog.targets)
        }
        else {
            $indices = @($selection -split ',' | ForEach-Object {
                $number = 0
                if (-not [int]::TryParse($_.Trim(), [ref]$number) -or $number -lt 1 -or $number -gt $catalog.targets.Count) {
                    throw "Invalid target selection: $selection"
                }
                $number - 1
            } | Select-Object -Unique)
            $selected = @($indices | ForEach-Object { $catalog.targets[$_] })
        }
        if ($selected.Count -eq 0) { Write-Warning 'No targets selected.'; continue }

        Write-Host ''
        Write-Host '  1. Project - current project only'
        Write-Host '  2. User - available across projects'
        $scopeChoice = (Read-Host 'Choose installation scope').Trim()
        if ($scopeChoice -ne '1' -and $scopeChoice -ne '2') { Write-Warning 'Invalid scope.'; continue }
        $scope = if ($scopeChoice -eq '1') { 'project' } else { 'user' }
        $base = $homeRoot
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
        foreach ($target in $selected) {
            $rootPath = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $key = [IO.Path]::GetFullPath((Join-Path $base (Join-Path $rootPath 'skills\rcoder'))).ToLowerInvariant()
            if ($seen.ContainsKey($key)) {
                Write-Host "Skipped duplicate discovery root for $($target.label)."
                continue
            }
            $seen[$key] = $true
            $action = if ($actionChoice -eq '1') { 'install' } else { 'uninstall' }
            Invoke-Target -Target $target -Scope $scope -Base $base -Action $action
        }
        Write-Host ''
        Write-Host 'Operation completed. Start a new agent session or reload its skills.'
    }
}
catch {
    Write-Error "RCoder launcher error: $($_.Exception.Message)"
    exit 1
}
) {
                Write-Host 'Uninstall cancelled.'
                continue
            }
        }
        $base = $homeRoot
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
        foreach ($target in $selected) {
            $rootPath = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $key = [IO.Path]::GetFullPath((Join-Path $base (Join-Path $rootPath 'skills\rcoder'))).ToLowerInvariant()
            if ($seen.ContainsKey($key)) {
                Write-Host "Skipped duplicate discovery root for $($target.label)."
                continue
            }
            $seen[$key] = $true
            $action = if ($actionChoice -eq '1') { 'install' } else { 'uninstall' }
            Invoke-Target -Target $target -Scope $scope -Base $base -Action $action
        }
        Write-Host ''
        Write-Host 'Operation completed. Start a new agent session or reload its skills.'
    }
}
catch {
    Write-Error "RCoder launcher error: $($_.Exception.Message)"
    exit 1
}
) {
            $selected = @($catalog.targets)
        }
        else {
            $indices = @($selection -split ',' | ForEach-Object {
                $number = 0
                if (-not [int]::TryParse($_.Trim(), [ref]$number) -or $number -lt 1 -or $number -gt $catalog.targets.Count) {
                    throw "Invalid target selection: $selection"
                }
                $number - 1
            } | Select-Object -Unique)
            $selected = @($indices | ForEach-Object { $catalog.targets[$_] })
        }
        if ($selected.Count -eq 0) { Write-Warning 'No targets selected.'; continue }

        Write-Host ''
        Write-Host '  1. Project - current project only'
        Write-Host '  2. User - available across projects'
        $scopeChoice = (Read-Host 'Choose installation scope').Trim()
        if ($scopeChoice -ne '1' -and $scopeChoice -ne '2') { Write-Warning 'Invalid scope.'; continue }
        $scope = if ($scopeChoice -eq '1') { 'project' } else { 'user' }
        $base = $homeRoot
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
        foreach ($target in $selected) {
            $rootPath = if ($scope -eq 'project') { [string]$target.project_root } else { [string]$target.user_root }
            $key = [IO.Path]::GetFullPath((Join-Path $base (Join-Path $rootPath 'skills\rcoder'))).ToLowerInvariant()
            if ($seen.ContainsKey($key)) {
                Write-Host "Skipped duplicate discovery root for $($target.label)."
                continue
            }
            $seen[$key] = $true
            $action = if ($actionChoice -eq '1') { 'install' } else { 'uninstall' }
            Invoke-Target -Target $target -Scope $scope -Base $base -Action $action
        }
        Write-Host ''
        Write-Host 'Operation completed. Start a new agent session or reload its skills.'
    }
}
catch {
    Write-Error "RCoder launcher error: $($_.Exception.Message)"
    exit 1
}
