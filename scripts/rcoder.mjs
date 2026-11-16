#!/usr/bin/env node
import {
  cpSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync,
  realpathSync, renameSync, rmSync, statSync
} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';

const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = path.join(PACKAGE_ROOT, 'skills', 'rcoder');
const VERSION = JSON.parse(readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8')).version;
const TARGETS = new Set(['claude-code', 'codex', 'cursor', 'gemini-cli', 'copilot', 'agents']);
const SCOPES = new Set(['project', 'user']);

function usage() {
  console.log(`RCoder ${VERSION}

Usage:
  npx -y github:RidTheWann/RCoder-Skills [options]

Options:
  --target <name>       claude-code | codex | cursor | gemini-cli | copilot | agents
  --scope <scope>       project | user (default: project)
  --project-dir <path>  Project root (default: current directory)
  --home-dir <path>     User home (default: OS home directory)
  --dry-run             Show changes without writing
  --uninstall           Remove RCoder and restore the latest backup
  --help                Show this help
  --version             Show version`);
}

function parseArgs(args) {
  const options = { target: 'agents', scope: 'project', projectDir: process.cwd(), homeDir: os.homedir(), dryRun: false, uninstall: false };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') { options.help = true; continue; }
    if (arg === '--version' || arg === '-v') { options.version = true; continue; }
    if (arg === '--dry-run') { options.dryRun = true; continue; }
    if (arg === '--uninstall') { options.uninstall = true; continue; }
    if (['--target', '--scope', '--project-dir', '--home-dir'].includes(arg)) {
      if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error(`Missing value for ${arg}`);
      const value = args[++i];
      if (arg === '--target') options.target = value;
      if (arg === '--scope') options.scope = value;
      if (arg === '--project-dir') options.projectDir = value;
      if (arg === '--home-dir') options.homeDir = value;
      continue;
    }
    throw new Error(`Unknown option: ${arg}`);
  }
  if (!TARGETS.has(options.target)) throw new Error(`Unsupported target: ${options.target}`);
  if (!SCOPES.has(options.scope)) throw new Error(`Unsupported scope: ${options.scope}`);
  return options;
}

function assertSafePath(base, targetPath) {
  const relative = path.relative(base, targetPath);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`Refusing to write outside the selected scope: ${targetPath}`);
  }
  let current = base;
  for (const segment of relative.split(path.sep).filter(Boolean)) {
    current = path.join(current, segment);
    if (existsSync(current) && lstatSync(current).isSymbolicLink()) {
      throw new Error(`Refusing to follow a symbolic link inside the installation path: ${current}`);
    }
  }
}

function listFiles(root, relative = '') {
  const current = path.join(root, relative);
  return readdirSync(current, { withFileTypes: true }).flatMap((entry) => {
    const next = path.join(relative, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Symbolic links are not allowed in the skill source: ${next}`);
    if (entry.isDirectory()) return listFiles(root, next);
    if (entry.isFile()) return [next];
    return [];
  }).sort();
}

function sameTree(left, right) {
  if (!existsSync(left) || !existsSync(right) || !statSync(left).isDirectory() || !statSync(right).isDirectory()) return false;
  const a = listFiles(left);
  const b = listFiles(right);
  if (a.length !== b.length || a.some((item, index) => item !== b[index])) return false;
  return a.every((item) => readFileSync(path.join(left, item)).equals(readFileSync(path.join(right, item))));
}

function backupEntries(backupRoot) {
  if (!existsSync(backupRoot)) return [];
  return readdirSync(backupRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('install-'))
    .map((entry) => path.join(backupRoot, entry.name))
    .sort();
}

function install(options) {
  if (!existsSync(path.join(SOURCE, 'SKILL.md'))) throw new Error(`The bundled skill is missing: ${SOURCE}`);
  const baseInput = options.scope === 'project' ? options.projectDir : options.homeDir;
  if (!existsSync(baseInput) || !statSync(baseInput).isDirectory()) throw new Error(`The selected ${options.scope} directory does not exist: ${baseInput}`);
  const base = realpathSync(baseInput);
  const rootName = {
    'claude-code': '.claude', codex: '.agents', agents: '.agents', cursor: '.cursor',
    'gemini-cli': '.gemini', copilot: options.scope === 'user' ? '.copilot' : '.github'
  }[options.target];
  const targetRoot = path.join(base, rootName);
  const skillsRoot = path.join(targetRoot, 'skills');
  const destination = path.join(skillsRoot, 'rcoder');
  const backupRoot = path.join(targetRoot, '.rcoder-backups', options.target);
  assertSafePath(base, destination);
  assertSafePath(base, backupRoot);

  if (options.uninstall) {
    console.log(`Uninstall target: ${destination}`);
    if (options.dryRun) { console.log(`DRY RUN: preserve the active folder and restore the latest backup from ${backupRoot}, if present.`); return; }
    if (existsSync(destination)) {
      mkdirSync(backupRoot, { recursive: true });
      renameSync(destination, path.join(backupRoot, `uninstalled-${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`));
    } else {
      console.log('No active RCoder installation was found.');
    }
    const backups = backupEntries(backupRoot);
    if (backups.length > 0) {
      mkdirSync(skillsRoot, { recursive: true });
      renameSync(backups.at(-1), destination);
      console.log(`Restored previous installation: ${destination}`);
    }
    return;
  }

  if (sameTree(SOURCE, destination)) {
    console.log(`RCoder ${VERSION} is already current at ${destination}`);
    return;
  }
  console.log(`Install target: ${destination}`);
  if (options.dryRun) {
    if (existsSync(destination)) console.log(`DRY RUN: back up the existing folder under ${backupRoot}`);
    console.log(`DRY RUN: copy the bundled skill into ${destination}`);
    return;
  }

  mkdirSync(skillsRoot, { recursive: true });
  mkdirSync(backupRoot, { recursive: true });
  const stamp = `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`;
  const stage = path.join(skillsRoot, `.rcoder-stage-${stamp}`);
  let savedBackup = null;
  try {
    cpSync(SOURCE, stage, { recursive: true, errorOnExist: true, force: false });
    if (existsSync(destination)) {
      savedBackup = path.join(backupRoot, `install-${stamp}`);
      renameSync(destination, savedBackup);
      console.log(`Backed up previous installation: ${savedBackup}`);
    }
    renameSync(stage, destination);
    console.log(`Installed RCoder ${VERSION} for ${options.target} (${options.scope}): ${destination}`);
  } catch (error) {
    if (existsSync(stage)) rmSync(stage, { recursive: true, force: true });
    if (savedBackup && existsSync(savedBackup) && !existsSync(destination)) renameSync(savedBackup, destination);
    throw error;
  }
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) { usage(); process.exit(0); }
  if (options.version) { console.log(VERSION); process.exit(0); }
  install(options);
} catch (error) {
  console.error(`RCoder installer error: ${error.message}`);
  process.exitCode = 1;
}
