[CmdletBinding()]
param(
    [ValidateSet('claude-code','codex','cursor','gemini-cli','copilot','agents','qoder','opencode','antigravity','amp','zed','pi','openclaw','autohand','warp','kilocode','cline','roo-code','trae','factory')]
    [string]$Target = 'agents',
    [ValidateSet('project','user')]
    [string]$Scope = 'project',
    [string]$ProjectDir = (Get-Location).Path,
    [string]$HomeDir = $HOME,
    [switch]$DryRun,
    [switch]$Uninstall,
    [switch]$NoLauncher
)
$ErrorActionPreference = 'Stop'

function Assert-NoReparsePoint([string]$Base,[string]$Path) {
    $baseFull=[IO.Path]::GetFullPath($Base)
    $pathFull=[IO.Path]::GetFullPath($Path)
    $comparison=[System.StringComparison]::OrdinalIgnoreCase
    $prefix=$baseFull
    if(-not $prefix.EndsWith([string][IO.Path]::DirectorySeparatorChar)){$prefix += [IO.Path]::DirectorySeparatorChar}
    if(-not $pathFull.Equals($baseFull,$comparison) -and -not $pathFull.StartsWith($prefix,$comparison)){throw "Refusing to write outside selected scope: $Path"}
    $relative=if($pathFull.Equals($baseFull,$comparison)){''}else{$pathFull.Substring($prefix.Length)}
    $current=$baseFull
    foreach($part in ($relative -split '[\\/]+' | Where-Object {$_})){
        $current=Join-Path $current $part
        if(Test-Path -LiteralPath $current){
            $item=Get-Item -LiteralPath $current -Force
            if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Refusing symbolic link or reparse point: $current"}
        }
    }
}

function Test-SameDirectory([string]$Left,[string]$Right) {
    if(-not(Test-Path -LiteralPath $Left -PathType Container) -or -not(Test-Path -LiteralPath $Right -PathType Container)){return $false}
    $a=@(Get-ChildItem -LiteralPath $Left -File -Recurse | ForEach-Object {$_.FullName.Substring($Left.Length).TrimStart([char[]]@([char]92,[char]47))} | Sort-Object)
    $b=@(Get-ChildItem -LiteralPath $Right -File -Recurse | ForEach-Object {$_.FullName.Substring($Right.Length).TrimStart([char[]]@([char]92,[char]47))} | Sort-Object)
    if(($a -join "`n") -ne ($b -join "`n")){return $false}
    foreach($relative in $a){
        if((Get-FileHash -LiteralPath (Join-Path $Left $relative) -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $Right $relative) -Algorithm SHA256).Hash){return $false}
    }
    return $true
}

function Install-GlobalLauncher([string]$Repo,[string]$UserHome) {
    $launcherRoot=Join-Path $UserHome '.rcoder'
    $appRoot=Join-Path $launcherRoot 'app'
    $backupRoot=Join-Path $launcherRoot 'backups'
    Assert-NoReparsePoint -Base $UserHome -Path $launcherRoot
    Assert-NoReparsePoint -Base $UserHome -Path $appRoot
    Assert-NoReparsePoint -Base $UserHome -Path $backupRoot
    $stage=Join-Path $launcherRoot ('.app-stage-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path (Join-Path $stage 'scripts'),(Join-Path $stage 'launcher'),(Join-Path $stage 'skills') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $Repo 'scripts/rcoder.mjs') -Destination (Join-Path $stage 'scripts/rcoder.mjs')
    Copy-Item -LiteralPath (Join-Path $Repo 'targets.json') -Destination (Join-Path $stage 'targets.json')
    Copy-Item -LiteralPath (Join-Path $Repo 'package.json') -Destination (Join-Path $stage 'package.json')
    Copy-Item -LiteralPath (Join-Path $Repo 'launcher/RCoder.ps1') -Destination (Join-Path $stage 'launcher/RCoder.ps1')
    Copy-Item -LiteralPath (Join-Path $Repo 'skills/rcoder') -Destination (Join-Path $stage 'skills/rcoder') -Recurse
    if(Test-SameDirectory -Left $stage -Right $appRoot){Remove-Item -LiteralPath $stage -Recurse -Force}
    else {
        $saved=$null
        try {
            New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
            if(Test-Path -LiteralPath $appRoot){
                $saved=Join-Path $backupRoot ('app-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
                Move-Item -LiteralPath $appRoot -Destination $saved
            }
            Move-Item -LiteralPath $stage -Destination $appRoot
        } catch {
            if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue}
            if($saved -and (Test-Path -LiteralPath $saved) -and -not(Test-Path -LiteralPath $appRoot)){Move-Item -LiteralPath $saved -Destination $appRoot}
            throw
        }
    }
    $binRoot=Join-Path $launcherRoot 'bin'
    New-Item -ItemType Directory -Path $binRoot -Force | Out-Null
    $manager=Join-Path $appRoot 'launcher/RCoder.ps1'
    $cmd=Join-Path $binRoot 'RCoder.cmd'
    $cmdText="@echo off`r
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$manager`" %*`r
echo.`r
echo Close and reopen the terminal if RCoder was just added to PATH.`r
echo.`r
"
    Set-Content -LiteralPath $cmd -Value $cmdText -Encoding ASCII
    $oldPath=[Environment]::GetEnvironmentVariable('Path','User')
    $items=@()
    if($oldPath){$items=@($oldPath -split ';' | Where-Object {$_})}
    $present=$false
    foreach($entry in $items){if([String]::Equals($entry.TrimEnd([char]92),$binRoot.TrimEnd([char]92),[System.StringComparison]::OrdinalIgnoreCase)){$present=$true}}
    if(-not $present){$items += $binRoot;[Environment]::SetEnvironmentVariable('Path',($items -join ';'),'User')}
    Write-Host "Installed global terminal launcher: $cmd"
}

$baseInput=if($Scope -eq 'project'){$ProjectDir}else{$HomeDir}
if(-not(Test-Path -LiteralPath $baseInput -PathType Container)){throw "Selected $Scope directory does not exist: $baseInput"}
if(-not(Test-Path -LiteralPath $HomeDir -PathType Container)){throw "User home directory does not exist: $HomeDir"}
$base=(Resolve-Path -LiteralPath $baseInput).Path
$home=(Resolve-Path -LiteralPath $HomeDir).Path
$tempRoot=Join-Path ([IO.Path]::GetTempPath()) ('rcoder-bootstrap-'+[guid]::NewGuid().ToString('N'))
$archive=Join-Path $tempRoot 'rcoder.zip'
$extract=Join-Path $tempRoot 'source'
$repoUrl='https://github.com/RidTheWann/RCoder-Skills/archive/refs/heads/main.zip'
$stage=$null
$savedBackup=$null
$destination=$null
try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Write-Host 'Downloading the RCoder bundle over HTTPS...'
    if($PSVersionTable.PSVersion.Major -le 5){
        [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $repoUrl -OutFile $archive -UseBasicParsing
    } else {
        Invoke-WebRequest -Uri $repoUrl -OutFile $archive
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
    $repoDir=Get-ChildItem -LiteralPath $extract -Directory | Select-Object -First 1
    if($null -eq $repoDir){throw 'The repository archive did not contain a source directory.'}
    $repo=$repoDir.FullName
    $catalog=Get-Content -LiteralPath (Join-Path $repo 'targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $config=@($catalog.targets | Where-Object {$_.id -eq $Target}) | Select-Object -First 1
    if($null -eq $config){throw "Target is not present in the target catalog: $Target"}
    $relativeRoot=if($Scope -eq 'project'){[string]$config.project_root}else{[string]$config.user_root}
    $targetRoot=Join-Path $base $relativeRoot
    $skillsRoot=Join-Path $targetRoot 'skills'
    $destination=Join-Path $skillsRoot 'rcoder'
    $backupParent=Join-Path $targetRoot '.rcoder-backups'
    $backupRoot=Join-Path $backupParent 'rcoder'
    $legacyBackupRoot=Join-Path $backupParent $Target
    Assert-NoReparsePoint -Base $base -Path $destination
    Assert-NoReparsePoint -Base $base -Path $backupRoot
    Assert-NoReparsePoint -Base $base -Path $legacyBackupRoot
    Write-Host "Install target: $Target ($Scope) -> $destination"
    if($Uninstall){
        if($DryRun){Write-Host "DRY RUN: preserve active install and restore the newest backup from $backupRoot";return}
        $stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
        if(Test-Path -LiteralPath $destination -PathType Container){
            New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
            Move-Item -LiteralPath $destination -Destination (Join-Path $backupRoot "uninstalled-$stamp")
        } else {Write-Host 'No active RCoder installation was found.'}
        $backups=@(Get-ChildItem -LiteralPath $backupRoot -Directory -Filter 'install-*' -ErrorAction SilentlyContinue | Sort-Object Name)
        if($backups.Count -eq 0){$backups=@(Get-ChildItem -LiteralPath $legacyBackupRoot -Directory -Filter 'install-*' -ErrorAction SilentlyContinue | Sort-Object Name)}
        if($backups.Count -gt 0){
            New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
            Move-Item -LiteralPath $backups[-1].FullName -Destination $destination
            Write-Host "Restored previous installation: $destination"
        }
        return
    }
    $source=Join-Path $repo 'skills/rcoder'
    if(-not(Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)){throw 'Downloaded skill bundle is incomplete.'}
    if(-not(Test-SameDirectory -Left $source -Right $destination)){
        if($DryRun){Write-Host 'DRY RUN: no files will be changed.';return}
        New-Item -ItemType Directory -Path $skillsRoot,$backupRoot -Force | Out-Null
        $stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
        $stage=Join-Path $skillsRoot ".rcoder-stage-$stamp"
        Copy-Item -LiteralPath $source -Destination $stage -Recurse
        if(Test-Path -LiteralPath $destination){
            $savedBackup=Join-Path $backupRoot "install-$stamp"
            Move-Item -LiteralPath $destination -Destination $savedBackup
            Write-Host "Backed up previous skill: $savedBackup"
        }
        Move-Item -LiteralPath $stage -Destination $destination
        $stage=$null
        Write-Host "Installed RCoder skill: $destination"
    } else {Write-Host 'The selected RCoder skill installation is already current.'}
    if(-not $NoLauncher -and -not $DryRun){Install-GlobalLauncher -Repo $repo -UserHome $home}
    Write-Host ''
    Write-Host 'RCoder installation complete. Open a new terminal and type RCoder to manage agents.'
} catch {
    if($stage -and (Test-Path -LiteralPath $stage)){Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue}
    if($savedBackup -and (Test-Path -LiteralPath $savedBackup) -and -not(Test-Path -LiteralPath $destination)){Move-Item -LiteralPath $savedBackup -Destination $destination}
    throw
} finally {
    if(Test-Path -LiteralPath $tempRoot){Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue}
}
