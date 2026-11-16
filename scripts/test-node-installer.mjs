#!/usr/bin/env node
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, existsSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'scripts', 'rcoder.mjs');
const catalog = JSON.parse(readFileSync(path.join(root, 'targets.json'), 'utf8'));
const targets = catalog.targets;
const temp = mkdtempSync(path.join(os.tmpdir(), 'rcoder-node-installer-'));

function run(args) {
  return execFileSync(process.execPath, [cli, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}
function destinationFor(target, scope, projectDir, homeDir) {
  const base = scope === 'project' ? projectDir : homeDir;
  const rootName = scope === 'project' ? target.project_root : target.user_root;
  return path.join(base, ...rootName.split('/'), 'skills', 'rcoder');
}

try {
  assert.match(run(['--help']), /RCoder/);
  const list = run(['--list-targets']);
  for (const target of targets) assert.ok(list.includes(target.id), `Missing target: ${target.id}`);

  for (const target of targets) {
    for (const scope of ['project', 'user']) {
      const projectDir = path.join(temp, `${target.id}-${scope}-project`);
      const homeDir = path.join(temp, `${target.id}-${scope}-home`);
      mkdirSync(projectDir, { recursive: true });
      mkdirSync(homeDir, { recursive: true });
      const destination = destinationFor(target, scope, projectDir, homeDir);
      mkdirSync(destination, { recursive: true });
      writeFileSync(path.join(destination, 'previous-install.txt'), 'preserve this backup');
      const common = ['--target', target.id, '--scope', scope, '--project-dir', projectDir, '--home-dir', homeDir, '--no-launcher'];

      run([...common, '--dry-run']);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), false, `${target.id}/${scope}: dry-run installed files`);
      run(common);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), true, `${target.id}/${scope}: install failed`);

      const targetRoot = path.dirname(path.dirname(destination));
      const backupRoot = path.join(targetRoot, '.rcoder-backups', target.id);
      const backups = readdirSync(backupRoot).filter((name) => name.startsWith('install-'));
      assert.equal(backups.length, 1, `${target.id}/${scope}: expected one backup`);
      assert.equal(readFileSync(path.join(backupRoot, backups[0], 'previous-install.txt'), 'utf8'), 'preserve this backup');

      run(common);
      assert.equal(readdirSync(backupRoot).filter((name) => name.startsWith('install-')).length, 1,
        `${target.id}/${scope}: repeated install was not idempotent`);

      run([...common, '--uninstall']);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), false, `${target.id}/${scope}: uninstall left RCoder`);
      assert.equal(readFileSync(path.join(destination, 'previous-install.txt'), 'utf8'), 'preserve this backup');
      console.log(`PASS ${target.id} / ${scope}`);
    }
  }

  const launcherHome = path.join(temp, 'launcher-home');
  const launcherProject = path.join(temp, 'launcher-project');
  mkdirSync(launcherHome, { recursive: true });
  mkdirSync(launcherProject, { recursive: true });
  run(['--target', 'agents', '--scope', 'project', '--project-dir', launcherProject, '--home-dir', launcherHome]);
  const launcherRoot = path.join(launcherHome, '.rcoder');
  const appRoot = path.join(launcherRoot, 'app');
  const command = process.platform === 'win32'
    ? path.join(launcherRoot, 'bin', 'RCoder.cmd')
    : path.join(launcherHome, '.local', 'bin', 'RCoder');
  assert.ok(existsSync(command), 'Global RCoder command was not installed');
  assert.ok(existsSync(path.join(appRoot, 'launcher', 'RCoder.ps1')), 'PowerShell manager was not bundled');
  assert.ok(existsSync(path.join(appRoot, 'targets.json')), 'Target catalog was not bundled');
  assert.ok(existsSync(path.join(appRoot, 'skills', 'rcoder', 'SKILL.md')), 'Canonical skill was not bundled');

  const backupRoot = path.join(launcherRoot, 'backups');
  const before = existsSync(backupRoot) ? readdirSync(backupRoot).length : 0;
  run(['--target', 'agents', '--scope', 'project', '--project-dir', launcherProject, '--home-dir', launcherHome]);
  const after = existsSync(backupRoot) ? readdirSync(backupRoot).length : 0;
  assert.equal(after, before, 'Repeated installation must not create unnecessary launcher backups');

  const menu = spawnSync(process.execPath, [cli, '--interactive', '--home-dir', launcherHome], {
    input: '3\n0\n', encoding: 'utf8'
  });
  assert.equal(menu.status, 0, menu.stderr || 'Interactive manager failed');
  assert.match(menu.stdout, /Agent Skill Manager/);
  assert.match(menu.stdout, /Factory Droid/);
  const sharedProject = path.join(temp, 'shared-root-project');
  const sharedHome = path.join(temp, 'shared-root-home');
  mkdirSync(sharedProject, { recursive: true });
  mkdirSync(sharedHome, { recursive: true });
  const sharedSkill = path.join(sharedProject, '.agents', 'skills', 'rcoder');
  mkdirSync(sharedSkill, { recursive: true });
  writeFileSync(path.join(sharedSkill, 'pre-rcoder.txt'), 'restore through another host ID');
  const sharedArgs = ['--scope', 'project', '--project-dir', sharedProject, '--home-dir', sharedHome, '--no-launcher'];
  run(['--target', 'codex', ...sharedArgs]);
  run(['--target', 'zed', ...sharedArgs]);
  run(['--target', 'zed', ...sharedArgs, '--uninstall']);
  assert.equal(readFileSync(path.join(sharedSkill, 'pre-rcoder.txt'), 'utf8'), 'restore through another host ID');
  console.log('PASS shared Agent Skills root: cross-host backup restoration');
  console.log('PASS global RCoder command, bundled manager, launcher idempotence, and interactive menu');
  console.log(`PASS all ${targets.length * 2} Node installer target/scope combinations`);
} finally {
  rmSync(temp, { recursive: true, force: true });
}
