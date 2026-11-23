#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'scripts', 'rcoder.mjs');
const result = spawnSync(process.execPath, [cli, 'doctor', '--json'], {
  cwd: root, encoding: 'utf8', timeout: 30000
});
assert.equal(result.status, 0, result.stderr || result.stdout);
const report = JSON.parse(result.stdout);
assert.equal(report.tool, 'RCoder doctor');
assert.equal(report.ok, true, JSON.stringify(report.checks.filter((x) => x.status === 'FAIL')));
assert(report.checks.some((x) => x.id === 'version-parity' && x.status === 'PASS'));
assert(report.checks.some((x) => x.id === 'mcp:streamable-http' && x.status === 'PASS'));
console.log('PASS rcoder doctor CLI (version parity, contract, runtimes)');
