#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const server = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'skills', 'rcoder', 'scripts', 'rcoder_mcp_modern.py');
const forwarded = process.argv.slice(2);
const override = process.env.RCODER_PYTHON;
const candidates = override ? [[override, []]] : (process.platform === 'win32' ? [['python', []], ['py', ['-3']]] : [['python3', []], ['python', []]]);

for (const [executable, prefix] of candidates) {
  const result = spawnSync(executable, [...prefix, server, ...forwarded], { stdio: 'inherit', env: process.env, windowsHide: true });
  if (result.error?.code === 'ENOENT' && !override) continue;
  if (result.error) { process.stderr.write('RCoder MCP launcher: ' + result.error.message + '\\n'); process.exitCode = 1; }
  else if (result.signal) process.exitCode = 1;
  else process.exitCode = result.status ?? 1;
  process.exit();
}
process.stderr.write('RCoder MCP launcher: Python 3 not found. Install Python 3 or set RCODER_PYTHON.\\n');
process.exitCode = 127;
