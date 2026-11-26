#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const currentFile = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(currentFile), '..');
const entryName = process.env.RCODER_MCP_ENTRY === 'core' ? 'rcoder_mcp.py' : 'rcoder_mcp_modern.py';
const server = path.join(repoRoot, 'skills', 'rcoder', 'scripts', entryName);
const forwarded = process.argv.slice(2);
const override = process.env.RCODER_PYTHON;

function findPython() {
  const probes = override
    ? [[override, []]]
    : process.platform === 'win32'
      ? [['py', ['-3']], ['python', []], ['python3', []]]
      : [['python3', []], ['python', []]];

  for (const [command, prefixArgs] of probes) {
    const probe = spawnSync(
      command,
      [...prefixArgs, '-c', 'import sys; assert sys.version_info >= (3, 9); print(sys.executable)'],
      { encoding: 'utf8', timeout: 4000, windowsHide: true }
    );
    const executable = (probe.stdout || '').trim();
    const stub = executable.toLowerCase().includes('windowsapps');
    if (probe.status === 0 && executable && !stub) return { command, prefixArgs };
  }
  throw new Error('RCoder MCP requires Python >= 3.9 in PATH (or set RCODER_PYTHON).');
}

let selected;
try {
  selected = findPython();
} catch (error) {
  process.stderr.write('RCoder MCP launcher: ' + error.message + '\n');
  process.exit(127);
}

const child = spawn(selected.command, [...selected.prefixArgs, server, ...forwarded], {
  stdio: 'inherit',
  windowsHide: true,
  env: {
    ...process.env,
    PYTHONUTF8: '1',
    PYTHONIOENCODING: 'utf-8',
    RCODER_WORKSPACE_ROOT: process.env.RCODER_WORKSPACE_ROOT || process.cwd(),
  },
});

child.on('error', (error) => {
  process.stderr.write('RCoder MCP launcher: ' + error.message + '\n');
  process.exitCode = 1;
});
child.on('exit', (code, signal) => {
  if (signal) {
    try { process.kill(process.pid, signal); } catch { process.exitCode = 1; }
  } else {
    process.exitCode = code ?? 0;
  }
});
