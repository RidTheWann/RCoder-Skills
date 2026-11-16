$ErrorActionPreference='Stop'
$rootInstall = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) 'install.ps1'
$tokens = $null; $parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($rootInstall, [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count -gt 0) { throw "Root PowerShell bootstrap syntax error: $($parseErrors[0].Message)" }
$root=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path); $installer=Join-Path $root 'scripts/install.ps1'
$temp=Join-Path ([IO.Path]::GetTempPath()) ('rcoder-test-'+[guid]::NewGuid().ToString('N')); New-Item -ItemType Directory -Path $temp|Out-Null
try {
 foreach($target in @('claude-code','codex','cursor','gemini-cli','copilot','agents')){foreach($scope in @('project','user')){
  $project=Join-Path $temp "$target-$scope-project"; $homeDir=Join-Path $temp "$target-$scope-home"; New-Item -ItemType Directory -Force -Path $project,$homeDir|Out-Null
  $base=if($scope -eq 'project'){$project}else{$homeDir}; $folder=switch($target){'claude-code'{'.claude'} 'codex'{'.agents'} 'agents'{'.agents'} 'cursor'{'.cursor'} 'gemini-cli'{'.gemini'} 'copilot'{if($scope -eq 'user'){'.copilot'}else{'.github'}}}
  & $rootInstall -Target $target -Scope $scope -ProjectDir $project -HomeDir $homeDir -DryRun|Out-Null
  $dest=Join-Path (Join-Path $base $folder) 'skills/rcoder'; New-Item -ItemType Directory -Force -Path $dest|Out-Null; Set-Content -LiteralPath (Join-Path $dest 'original.txt') 'old'
  & $installer -Target $target -Scope $scope -ProjectDir $project -HomeDir $homeDir -DryRun|Out-Null
  if(-not(Test-Path -LiteralPath (Join-Path $dest 'original.txt'))){throw "Dry-run modified $target/$scope"}
  & $installer -Target $target -Scope $scope -ProjectDir $project -HomeDir $homeDir
  if(-not(Test-Path -LiteralPath (Join-Path $dest 'SKILL.md'))){throw "Install failed $target/$scope"}
  & $installer -Target $target -Scope $scope -ProjectDir $project -HomeDir $homeDir
  & $installer -Target $target -Scope $scope -ProjectDir $project -HomeDir $homeDir -Uninstall
  if(-not(Test-Path -LiteralPath (Join-Path $dest 'original.txt'))){throw "Backup restore failed $target/$scope"}
  if(Test-Path -LiteralPath (Join-Path $dest 'SKILL.md')){throw "Uninstall left skill $target/$scope"}; Write-Output "PASS $target / $scope"
 }}
 Write-Output 'PASS all 12 PowerShell target/scope combinations'
} finally {Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue}
