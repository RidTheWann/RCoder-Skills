#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, existsSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'scripts', 'rcoder.mjs');
const temp = mkdtempSync(path.join(os.tmpdir(), 'rcoder-integration-'));
const project = path.join(temp, 'project');
const home = path.join(temp, 'home');
mkdirSync(project, { recursive: true });
mkdirSync(home, { recursive: true });

function run(args, expect = 0) {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd: root, encoding: 'utf8', timeout: 60000,
    env: { ...process.env, HOME: home, USERPROFILE: home }
  });
  assert.equal(result.status, expect, result.stderr || result.stdout);
  return result.stdout;
}

try {
  // OpenCode integration owns the skill and plugin paths in the isolated project only.
  const install = run(['integration', 'install', 'opencode', '--scope', 'project',
    '--root', project, '--home-dir', home]);
  const skill = path.join(project, '.opencode', 'skills', 'rcoder', 'SKILL.md');
  const plugin = path.join(project, '.opencode', 'plugins', 'rcoder.js');
  const featureManifest = path.join(project, '.opencode', '.rcoder-features.json');
  assert(existsSync(skill), install);
  assert(existsSync(plugin), install);
  assert(existsSync(featureManifest), install);
  assert.match(readFileSync(plugin, 'utf8'), /experimental\.chat\.system\.transform/);
  assert.match(readFileSync(plugin, 'utf8'), /RCoder:/);
  assert.match(readFileSync(plugin, 'utf8'), /selected Agent Skill is at \\${skillFile\\}/);

  const verify = run(['integration', 'verify', 'opencode', '--scope', 'project',
    '--root', project, '--home-dir', home]);
  assert.match(verify, /adapter: PRESENT/);
  assert.match(verify, /skill: PRESENT/);

  // Replacing an existing adapter is reversible and does not silently discard user content.
  writeFileSync(plugin, '// locally customized OpenCode plugin\n');
  run(['integration', 'install', 'opencode', '--scope', 'project', '--root', project, '--home-dir', home]);
  const backups = readdirSync(path.dirname(plugin)).filter((name) => name.startsWith('rcoder.js.rcoder-backup-'));
  assert.equal(backups.length, 1);
  assert.equal(readFileSync(path.join(path.dirname(plugin), backups[0]), 'utf8'),
    '// locally customized OpenCode plugin\n');
  assert.match(readFileSync(plugin, 'utf8'), /RCoderPlugin/);

  // Dry-run prints the exact native installer commands but does not require those CLIs.
  const gemini = run(['integration', 'install', 'gemini-cli', '--dry-run']);
  assert.match(gemini, /gemini extensions install https:\/\/github\.com\/RidTheWann\/RCoder-Skills/);
  const geminiVerify = run(['integration', 'verify', 'gemini-cli', '--dry-run']);
  assert.match(geminiVerify, /gemini extensions list/);
  const codex = run(['integration', 'install', 'codex', '--dry-run']);
  assert.match(codex, /codex plugin marketplace add RidTheWann\/RCoder-Skills/);
  const claude = run(['integration', 'install', 'claude-code']);
  assert.match(claude, /\/plugin marketplace add RidTheWann\/RCoder-Skills/);
  assert.match(claude, /\/plugin install rcoder@rcoder-skills/);

  // Uninstall removes the recognized adapter and the managed skill, but leaves MCP host settings alone.
  run(['integration', 'uninstall', 'opencode', '--scope', 'project', '--root', project, '--home-dir', home]);
  assert.equal(existsSync(plugin), false);
  assert.equal(existsSync(skill), false);
  assert.equal(existsSync(featureManifest), false);
  assert.equal(existsSync(path.join(project, 'opencode.json')), false,
    'integration uninstall must not fabricate or remove unrelated host MCP configuration');

  // A dry-run OpenCode integration does not create directories or files.
  const dryProject = path.join(temp, 'dry-project');
  mkdirSync(dryProject);
  const dry = run(['integration', 'install', 'opencode', '--scope', 'project',
    '--root', dryProject, '--home-dir', home, '--dry-run']);
  assert.match(dry, /DRY RUN/);
  assert.equal(existsSync(path.join(dryProject, '.opencode')), false);

  console.log('PASS RCoder host integrations: OpenCode install/verify/backup/uninstall, Gemini/Codex dry-run, Claude instructions');
} finally {
  rmSync(temp, { recursive: true, force: true });
}
