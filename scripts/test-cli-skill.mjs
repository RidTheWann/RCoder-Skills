#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, existsSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'scripts', 'rcoder.mjs');
const temp = mkdtempSync(path.join(os.tmpdir(), 'rcoder-cli-skill-'));
const skill = path.join(temp, 'cli-skill');
function run(args, expect = 0) {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd: root, encoding: 'utf8', timeout: 30000
  });
  assert.equal(result.status, expect, result.stderr || result.stdout);
  return result.stdout;
}
try {
  const created = run(['skill', 'new', 'cli-skill', '--dest', skill,
    '--description', 'Use this skill to build and verify a focused CLI workflow.']);
  assert.match(created, /Created Agent Skill/);
  assert.match(run(['skill', 'lint', skill]), /PASS:/);
  const packed = run(['skill', 'package', skill, '--out', path.join(temp, 'cli-skill.zip'), '--json']);
  const report = JSON.parse(packed);
  assert(existsSync(report.path));
  assert(existsSync(report.checksum_file));
  const help = run(['skill', '--help']);
  assert.match(help, /new/);
  assert.match(help, /lint/);
  assert.match(help, /package/);
  assert.match(readFileSync(path.join(skill, 'SKILL.md'), 'utf8'), /name: cli-skill/);
  console.log('PASS Node CLI skill subcommands: new, lint, package');
} finally {
  rmSync(temp, { recursive: true, force: true });
}
