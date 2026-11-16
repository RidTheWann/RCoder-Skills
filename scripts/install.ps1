[CmdletBinding()]
param(
 [ValidateSet('claude-code','codex','cursor','gemini-cli','copilot','agents')][string]$Target='agents',
 [ValidateSet('project','user')][string]$Scope='project',
 [string]$ProjectDir=(Get-Location).Path,[string]$HomeDir=$HOME,
 [switch]$DryRun,[switch]$Uninstall
)
$ErrorActionPreference='Stop'
$scriptDir=Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir=[IO.Path]::GetFullPath((Join-Path $scriptDir '..\skills\rcoder'))
if (-not (Test-Path -LiteralPath (Join-Path $sourceDir 'SKILL.md') -PathType Leaf)) { throw "Skill source missing: $sourceDir\SKILL.md" }
$base=if($Scope -eq 'project'){$ProjectDir}else{$HomeDir}
if([string]::IsNullOrWhiteSpace($base)){throw 'No base directory for selected scope.'}
$base=[IO.Path]::GetFullPath($base)
$rootName=switch($Target){'claude-code'{'.claude'} 'codex'{'.agents'} 'agents'{'.agents'} 'cursor'{'.cursor'} 'gemini-cli'{'.gemini'} 'copilot'{if($Scope -eq 'user'){'.copilot'}else{'.github'}}}
$targetRoot=Join-Path $base $rootName; $parent=Join-Path $targetRoot 'skills'; $dest=Join-Path $parent 'rcoder'
$backup=Join-Path (Join-Path $targetRoot '.rcoder-backups') $Target; $stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
if($Uninstall){
 Write-Output "Uninstall target: $dest"
 if($DryRun){Write-Output "DRY RUN: preserve active install and restore newest backup under $backup";exit 0}
 if(Test-Path -LiteralPath $dest -PathType Container){New-Item -ItemType Directory -Force -Path $backup|Out-Null;Move-Item -LiteralPath $dest -Destination (Join-Path $backup "uninstalled-$stamp")}else{Write-Output 'No active RCoder installation found.'}
 $restore=Get-ChildItem -LiteralPath $backup -Directory -Filter 'install-*' -ErrorAction SilentlyContinue|Sort-Object Name|Select-Object -Last 1
 if($null -ne $restore){New-Item -ItemType Directory -Force -Path $parent|Out-Null;Move-Item -LiteralPath $restore.FullName -Destination $dest;Write-Output "Restored previous installation: $dest"}
 exit 0
}
if(Test-Path -LiteralPath $dest -PathType Container){
 $srcFiles=@(Get-ChildItem -LiteralPath $sourceDir -File -Recurse|ForEach-Object{$_.FullName.Substring($sourceDir.Length).TrimStart([char[]]@('\\','/'))})
 $dstFiles=@(Get-ChildItem -LiteralPath $dest -File -Recurse|ForEach-Object{$_.FullName.Substring($dest.Length).TrimStart([char[]]@('\\','/'))})
 $same=(@($srcFiles|Sort-Object)-join "`n") -eq (@($dstFiles|Sort-Object)-join "`n")
 if($same){foreach($rel in $srcFiles){if((Get-FileHash -LiteralPath (Join-Path $sourceDir $rel)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $dest $rel)).Hash){$same=$false;break}}}
 if($same){Write-Output "RCoder is already current at $dest";exit 0}
}
Write-Output "Install target: $dest"
if($DryRun){if(Test-Path -LiteralPath $dest){Write-Output "DRY RUN: backup existing folder to $backup\install-$stamp"};Write-Output "DRY RUN: copy $sourceDir to $dest";exit 0}
New-Item -ItemType Directory -Force -Path $parent,$backup|Out-Null
$stage=Join-Path $parent ".rcoder-stage-$stamp"
try{Copy-Item -LiteralPath $sourceDir -Destination $stage -Recurse;if(Test-Path -LiteralPath $dest){$backupPath=Join-Path $backup "install-$stamp";Move-Item -LiteralPath $dest -Destination $backupPath;Write-Output "Backed up previous installation: $backupPath"};Move-Item -LiteralPath $stage -Destination $dest}
finally{if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force}}
Write-Output "Installed RCoder for $Target ($Scope): $dest"
