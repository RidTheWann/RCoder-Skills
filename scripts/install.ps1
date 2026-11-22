[CmdletBinding()]
param(
 [ValidateSet('claude-code','codex','cursor','gemini-cli','copilot','agents','qoder','opencode','antigravity','amp','zed','pi','openclaw','autohand','warp','kilocode','cline','roo-code','trae','factory')][string]$Target='agents',
 [ValidateSet('project','user')][string]$Scope='project',
 [string]$ProjectDir=(Get-Location).Path,[string]$HomeDir=$HOME,
  [switch]$DryRun,[switch]$Uninstall,
  [string]$Features='rsaver,rscan',[switch]$ListFeatures,
  [ValidateSet('none','show','install')][string]$Mcp='none'
)
$ErrorActionPreference='Stop'
if($ListFeatures){
 Write-Output 'RSaver: Context pruning, budgeting, and re-anchoring for long sessions'
 Write-Output 'RScan: Read-only project scan with ranked development options at session start'
 exit 0
}
$selectedFeatures=@()
if($Features -and $Features -ne 'none'){
 foreach($part in ($Features -split ',')){
  $name=$part.Trim().ToLowerInvariant()
  if($name -notin @('rsaver','rscan')){throw "Unknown optional tool: $name"}
  if($selectedFeatures -contains $name){throw "Duplicate optional tool: $name"}
  $selectedFeatures+=$name
 }
}
$scriptDir=if($PSScriptRoot){$PSScriptRoot}else{Split-Path -Parent $MyInvocation.MyCommand.Path}
$repoDir=[IO.Path]::GetFullPath((Join-Path $scriptDir '..'))
$sourceDir=Join-Path (Join-Path $repoDir 'skills') 'rcoder'
$catalog=Get-Content -LiteralPath (Join-Path $repoDir 'targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$config=@($catalog.targets | Where-Object {$_.id -eq $Target}) | Select-Object -First 1
if($null -eq $config){throw "Unsupported target: $Target"}
$baseInput=if($Scope -eq 'project'){$ProjectDir}else{$HomeDir}
if(-not(Test-Path -LiteralPath $baseInput -PathType Container)){throw "Selected $Scope directory does not exist: $baseInput"}
$base=(Resolve-Path -LiteralPath $baseInput).Path
$relativeRoot=if($Scope -eq 'project'){[string]$config.project_root}else{[string]$config.user_root}
$targetRoot=Join-Path $base $relativeRoot
$parent=Join-Path $targetRoot 'skills'
$dest=Join-Path $parent 'rcoder'
$backupParent=Join-Path $targetRoot '.rcoder-backups'
$backup=Join-Path $backupParent 'rcoder'
$legacyBackup=Join-Path $backupParent $Target
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
function Assert-Safe([string]$Base,[string]$Path){
 $root=[IO.Path]::GetFullPath($Base);$full=[IO.Path]::GetFullPath($Path);$prefix=$root
 if(-not $prefix.EndsWith([string][IO.Path]::DirectorySeparatorChar)){$prefix += [IO.Path]::DirectorySeparatorChar}
 if(-not $full.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)){throw "Refusing to write outside selected scope: $Path"}
 $current=$root
 foreach($part in ($full.Substring($prefix.Length) -split '[\\/]+' | Where-Object {$_})){
  $current=Join-Path $current $part
  if(Test-Path -LiteralPath $current){$item=Get-Item -LiteralPath $current -Force;if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Refusing symbolic link: $current"}}
 }
}
function Same-Tree([string]$A,[string]$B){
 if(-not(Test-Path -LiteralPath $A -PathType Container) -or -not(Test-Path -LiteralPath $B -PathType Container)){return $false}
 $x=@(Get-ChildItem -LiteralPath $A -File -Recurse | ForEach-Object {$_.FullName.Substring($A.Length).TrimStart([char[]]@([char]92,[char]47))}|Sort-Object)
 $y=@(Get-ChildItem -LiteralPath $B -File -Recurse | ForEach-Object {$_.FullName.Substring($B.Length).TrimStart([char[]]@([char]92,[char]47))}|Sort-Object)
 if(($x -join "`n") -ne ($y -join "`n")){return $false}
 foreach($f in $x){if((Get-FileHash -LiteralPath (Join-Path $A $f)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $B $f)).Hash){return $false}}
 return $true
}
function Invoke-McpStep{
 if($Mcp -eq 'none'){return}
 . (Join-Path (Join-Path $repoDir 'launcher') 'McpSetup.ps1')
 Invoke-RCoderMcpSetup -Mode $Mcp -TargetId $Target -Scope $Scope -Base $base -SkillDestination $dest
}
Assert-Safe -Base $base -Path $dest;Assert-Safe -Base $base -Path $backup;Assert-Safe -Base $base -Path $legacyBackup
if($Uninstall){
 Write-Output "Uninstall target: $Target -> $dest"
 if($DryRun){Write-Output "DRY RUN: preserve active install and restore newest backup under $backup";exit 0}
 if(Test-Path -LiteralPath $dest -PathType Container){New-Item -ItemType Directory -Force -Path $backup|Out-Null;Move-Item -LiteralPath $dest -Destination (Join-Path $backup "uninstalled-$stamp")}else{Write-Output 'No active RCoder installation found.'}
 $restore=Get-ChildItem -LiteralPath $backup -Directory -Filter 'install-*' -ErrorAction SilentlyContinue|Sort-Object Name|Select-Object -Last 1
 if($null -eq $restore){$restore=Get-ChildItem -LiteralPath $legacyBackup -Directory -Filter 'install-*' -ErrorAction SilentlyContinue|Sort-Object Name|Select-Object -Last 1}
  if($null -ne $restore){New-Item -ItemType Directory -Force -Path $parent|Out-Null;Move-Item -LiteralPath $restore.FullName -Destination $dest;Write-Output "Restored previous installation: $dest"}
  $featureManifest=Join-Path $targetRoot '.rcoder-features.json'
  if(Test-Path -LiteralPath $featureManifest){Remove-Item -LiteralPath $featureManifest -Force}
  exit 0
}
if(-not(Test-Path -LiteralPath (Join-Path $sourceDir 'SKILL.md') -PathType Leaf)){throw "Skill source missing: $(Join-Path $sourceDir 'SKILL.md')"}
if(Same-Tree -A $sourceDir -B $dest){Write-Output "RCoder is already current at $dest";if(-not $DryRun){Invoke-McpStep};exit 0}
Write-Output "Install target: $Target ($Scope) -> $dest"
if($DryRun){Write-Output 'DRY RUN: no files will be changed.';if($Mcp -ne 'none'){Write-Output "DRY RUN: MCP mode '$Mcp' would run after install."};exit 0}
New-Item -ItemType Directory -Force -Path $parent,$backup|Out-Null
$stage=Join-Path $parent ".rcoder-stage-$stamp";$saved=$null
try{
 Copy-Item -LiteralPath $sourceDir -Destination $stage -Recurse
 if(Test-Path -LiteralPath $dest){$saved=Join-Path $backup "install-$stamp";Move-Item -LiteralPath $dest -Destination $saved}
 Move-Item -LiteralPath $stage -Destination $dest
  Write-Output "Installed RCoder for $Target ($Scope): $dest"
  $featureManifest=Join-Path $targetRoot '.rcoder-features.json'
  $version=(Get-Content -LiteralPath (Join-Path $repoDir 'package.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version
  $state=([ordered]@{schema_version=1;version=$version;rsaver=($selectedFeatures -contains 'rsaver');rscan=($selectedFeatures -contains 'rscan')})|ConvertTo-Json
  # 'Set-Content -Encoding UTF8' adds a BOM on Windows PowerShell 5.1; strict JSON readers reject it.
  [IO.File]::WriteAllText($featureManifest,$state+"`n",(New-Object System.Text.UTF8Encoding($false)))
  Write-Output "Enabled optional tools: $Features"
  Invoke-McpStep
 }catch{
 if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue}
 if($saved -and (Test-Path -LiteralPath $saved) -and -not(Test-Path -LiteralPath $dest)){Move-Item -LiteralPath $saved -Destination $dest}
 throw
}
