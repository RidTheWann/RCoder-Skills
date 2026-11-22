# Shared MCP setup helpers for the RCoder PowerShell installer and terminal manager.
# Dot-source this file. Works on Windows PowerShell 5.1 and PowerShell 7+.

function Find-RCoderPython {
    # Returns @{ Exe = <path>; PreArgs = <string[]> } for a working Python 3, or $null.
    # A candidate must actually run: the Microsoft Store "python.exe" stub exists on PATH
    # but does not execute scripts, so being found is not enough.
    foreach ($candidate in @('python3', 'python', 'py')) {
        $found = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $found) { continue }
        $pre = @()
        if ($candidate -eq 'py') { $pre = @('-3') }
        $savedPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $probe = @($pre) + @('-c', 'import sys; print(sys.version_info[0])')
            $answer = & $found.Source @probe 2>$null
            if (("$answer").Trim() -eq '3') { return @{ Exe = $found.Source; PreArgs = $pre } }
        }
        catch { }
        finally { $ErrorActionPreference = $savedPreference }
    }
    return $null
}

function Invoke-RCoderMcpSetup {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('show', 'install')][string]$Mode,
        [Parameter(Mandatory = $true)][string]$TargetId,
        [Parameter(Mandatory = $true)][ValidateSet('project', 'user')][string]$Scope,
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$SkillDestination
    )
    $scriptsDir = Join-Path $SkillDestination 'scripts'
    $helper = Join-Path $scriptsDir 'rcoder_mcp_setup.py'
    $server = Join-Path $scriptsDir 'rcoder_mcp_modern.py'
    if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
        Write-Warning "MCP setup helper not found: $helper (install or update RCoder first)"
        return
    }
    $python = Find-RCoderPython
    if ($null -eq $python) {
        Write-Host ''
        Write-Host 'MCP setup skipped: Python 3 was not found (the MCP server is a Python script).'
        Write-Host 'Install Python 3 from https://www.python.org/downloads/ and run RCoder again,'
        Write-Host 'then choose "Set up MCP server".'
        return
    }
    $action = 'show'
    if ($Mode -eq 'install') { $action = 'apply' }
    $arguments = @($python.PreArgs) + @($helper, $action, '--host', $TargetId, '--scope', $Scope,
        '--base', $Base, '--server', $server)
    Write-Host ''
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $python.Exe @arguments }
    finally { $ErrorActionPreference = $savedPreference }
    if ($LASTEXITCODE -ne 0) { Write-Warning "MCP setup reported a problem (exit code $LASTEXITCODE)." }
}

function Show-McpMenu {
    Write-Host ''
    Write-Host 'MCP server (optional): lets your agent call RCoder tools such as RScan and RSaver.'
    Write-Host '  1. Show me the exact config to paste (default, changes nothing)'
    Write-Host '  2. Set it up automatically (safe merge, backup, then self-test)'
    Write-Host '  3. Skip for now'
}

function Read-McpSelection {
    Show-McpMenu
    $choice = (Read-Host 'MCP server').Trim()
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = '1' }
    switch ($choice) {
        '1' { return 'show' }
        '2' { return 'install' }
        '3' { return 'none' }
        default { throw "Invalid MCP selection: $choice" }
    }
}
