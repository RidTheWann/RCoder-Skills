#!/usr/bin/env node
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, existsSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'scripts', 'rcoder.mjs');
const temp = mkdtempSync(path.join(os.tmpdir(), 'rcoder-node-installer-'));
const targets = ['claude-code', 'codex', 'cursor', 'gemini-cli', 'copilot', 'agents'];

function run(args) {
  return execFileSync(process.execPath, [cli, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

try {
  for (const target of targets) {
    for (const scope of ['project', 'user']) {
      const projectDir = path.join(temp, `${target}-${scope}-project`);
      const homeDir = path.join(temp, `${target}-${scope}-home`);
      mkdirSync(projectDir, { recursive: true });
      mkdirSync(homeDir, { recursive: true });
      const base = scope === 'project' ? projectDir : homeDir;
      const rootName = target === 'claude-code' ? '.claude'
        : ['codex', 'agents'].includes(target) ? '.agents'
          : target === 'cursor' ? '.cursor'
            : target === 'gemini-cli' ? '.gemini'
              : scope === 'user' ? '.copilot' : '.github';
      const destination = path.join(base, rootName, 'skills', 'rcoder');
      mkdirSync(destination, { recursive: true });
      writeFileSync(path.join(destination, 'previous-install.txt'), 'preserve this backup');
      const common = ['--target', target, '--scope', scope, '--project-dir', projectDir, '--home-dir', homeDir];

      run([...common, '--dry-run']);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), false, `${target}/${scope}: dry-run must not install`);
      run(common);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), true, `${target}/${scope}: install failed`);
      const backupRoot = path.join(base, rootName, '.rcoder-backups', target);
      const backups = readdirSync(backupRoot).filter((name) => name.startsWith('install-'));
      assert.equal(backups.length, 1, `${target}/${scope}: original installation was not backed up`);
      assert.equal(readFileSync(path.join(backupRoot, backups[0], 'previous-install.txt'), 'utf8'), 'preserve this backup');

      const before = readdirSync(backupRoot).length;
      run(common);
      assert.equal(readdirSync(backupRoot).length, before, `${target}/${scope}: repeated install was not idempotent`);

      run([...common, '--uninstall']);
      assert.equal(existsSync(path.join(destination, 'SKILL.md')), false, `${target}/${scope}: uninstall left RCoder installed`);
      assert.equal(readFileSync(path.join(destination, 'previous-install.txt'), 'utf8'), 'preserve this backup', `${target}/${scope}: uninstall did not restore backup`);
      console.log(`PASS ${target} / ${scope}`);
    }
  }
  console.log('PASS all 12 Node installer target/scope combinations');
} finally {
  rmSync(temp, { recursive: true, force: true });
}
