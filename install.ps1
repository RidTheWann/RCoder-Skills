[CmdletBinding()]
param(
    [ValidateSet('claude-code', 'codex', 'cursor', 'gemini-cli', 'copilot', 'agents')]
    [string]$Target = 'agents',
    [ValidateSet('project', 'user')]
    [string]$Scope = 'project',
    [string]$ProjectDir = (Get-Location).Path,
    [string]$HomeDir = $HOME,
    [switch]$DryRun,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

function Get-BackupDirectories([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $Path -Directory -Filter 'install-*' | Sort-Object Name)
}

function Test-SameDirectory([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Destination -PathType Container)) { return $false }
    $sourceFiles = @(Get-ChildItem -LiteralPath $Source -File -Recurse | ForEach-Object {
        $_.FullName.Substring($Source.Length).TrimStart([char[]]@([char]92, [char]47))
    } | Sort-Object)
    $destinationFiles = @(Get-ChildItem -LiteralPath $Destination -File -Recurse | ForEach-Object {
        $_.FullName.Substring($Destination.Length).TrimStart([char[]]@([char]92, [char]47))
    } | Sort-Object)
    if (($sourceFiles -join "`n") -ne ($destinationFiles -join "`n")) { return $false }
    foreach ($relativePath in $sourceFiles) {
        $sourceHash = (Get-FileHash -LiteralPath (Join-Path $Source $relativePath) -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath (Join-Path $Destination $relativePath) -Algorithm SHA256).Hash
        if ($sourceHash -ne $destinationHash) { return $false }
    }
    return $true
}

function Assert-NoReparsePoint([string]$Base, [string]$Path) {
    # GetRelativePath is unavailable in Windows PowerShell 5.1/.NET Framework.
    # Compare normalized absolute paths instead, using Windows case-insensitive rules.
    $comparison = [StringComparison]::Ordinal
    if ([IO.Path]::DirectorySeparatorChar -eq [char]92) {
        $comparison = [StringComparison]::OrdinalIgnoreCase
    }

    $baseFullPath = [IO.Path]::GetFullPath($Base)
    $pathFullPath = [IO.Path]::GetFullPath($Path)
    $baseRoot = [IO.Path]::GetPathRoot($baseFullPath)
    if ($baseFullPath.Length -gt $baseRoot.Length) {
        $baseFullPath = $baseFullPath.TrimEnd([char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar))
    }

    if ($pathFullPath.Equals($baseFullPath, $comparison)) {
        $relative = ''
    }
    else {
        $basePrefix = $baseFullPath
        if (-not $basePrefix.EndsWith([string][IO.Path]::DirectorySeparatorChar)) {
            $basePrefix += [IO.Path]::DirectorySeparatorChar
        }
        if (-not $pathFullPath.StartsWith($basePrefix, $comparison)) {
            throw "Refusing to write outside the selected scope: $Path"
        }
        $relative = $pathFullPath.Substring($basePrefix.Length)
    }

    $current = $baseFullPath
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

$baseInput = if ($Scope -eq 'project') { $ProjectDir } else { $HomeDir }
if (-not (Test-Path -LiteralPath $baseInput -PathType Container)) {
    throw "The selected $Scope directory does not exist: $baseInput"
}
$base = (Resolve-Path -LiteralPath $baseInput).Path
$rootName = switch ($Target) {
    'claude-code' { '.claude' }
    'codex' { '.agents' }
    'agents' { '.agents' }
    'cursor' { '.cursor' }
    'gemini-cli' { '.gemini' }
    'copilot' { if ($Scope -eq 'user') { '.copilot' } else { '.github' } }
}
$targetRoot = Join-Path $base $rootName
$skillsRoot = Join-Path $targetRoot 'skills'
$destination = Join-Path $skillsRoot 'rcoder'
$backupRoot = Join-Path (Join-Path $targetRoot '.rcoder-backups') $Target
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)

Assert-NoReparsePoint -Base $base -Path $destination
Assert-NoReparsePoint -Base $base -Path $backupRoot

if ($Uninstall) {
    Write-Host "Uninstall target: $destination"
    if ($DryRun) {
        Write-Host "DRY RUN: preserve the active folder and restore the latest backup from $backupRoot, if present."
        return
    }
    if (Test-Path -LiteralPath $destination -PathType Container) {
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        Move-Item -LiteralPath $destination -Destination (Join-Path $backupRoot "uninstalled-$stamp")
    }
    else {
        Write-Host 'No active RCoder installation was found.'
    }
    $backups = @(Get-BackupDirectories -Path $backupRoot)
    if ($backups.Count -gt 0) {
        New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
        Move-Item -LiteralPath $backups[-1].FullName -Destination $destination
        Write-Host "Restored previous installation: $destination"
    }
    return
}

Write-Host "Install target: $destination"
if ($DryRun) {
    Write-Host 'DRY RUN: no files will be changed.'
    return
}

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('rcoder-bootstrap-' + [guid]::NewGuid().ToString('N'))
$archivePath = Join-Path $tempRoot 'rcoder.zip'
$extractPath = Join-Path $tempRoot 'source'
$repositoryArchive = 'https://github.com/RidTheWann/RCoder-Skills/archive/refs/heads/main.zip'
$stage = $null
$savedBackup = $null

try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Write-Host 'Downloading the RCoder skill bundle over HTTPS...'
    Invoke-WebRequest -Uri $repositoryArchive -OutFile $archivePath
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractPath -Force

    $repositoryRoot = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
    if ($null -eq $repositoryRoot) { throw 'The repository archive did not contain a source directory.' }
    $source = Join-Path $repositoryRoot.FullName 'skills/rcoder'
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw 'The downloaded skill bundle is incomplete.'
    }

    if (Test-SameDirectory -Source $source -Destination $destination) {
        Write-Host 'The installed RCoder skill is already current.'
        return
    }

    New-Item -ItemType Directory -Path $skillsRoot, $backupRoot -Force | Out-Null
    $stage = Join-Path $skillsRoot ".rcoder-stage-$stamp"
    Copy-Item -LiteralPath $source -Destination $stage -Recurse

    if (Test-Path -LiteralPath $destination) {
        $savedBackup = Join-Path $backupRoot "install-$stamp"
        Move-Item -LiteralPath $destination -Destination $savedBackup
        Write-Host "Backed up the previous installation: $savedBackup"
    }
    Move-Item -LiteralPath $stage -Destination $destination
    $stage = $null
    Write-Host "Installed RCoder for $Target ($Scope): $destination"
}
catch {
    if ($stage -and (Test-Path -LiteralPath $stage)) {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($savedBackup -and (Test-Path -LiteralPath $savedBackup) -and -not (Test-Path -LiteralPath $destination)) {
        Move-Item -LiteralPath $savedBackup -Destination $destination
    }
    throw
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
