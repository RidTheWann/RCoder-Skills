#!/usr/bin/env node
import {
  appendFileSync, chmodSync, cpSync, existsSync, lstatSync, mkdirSync,
  readFileSync, readdirSync, realpathSync, renameSync, rmSync, statSync,
  writeFileSync
} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';

const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = path.join(PACKAGE_ROOT, 'skills', 'rcoder');
const HOME = os.homedir();
const VERSION = JSON.parse(readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8')).version;
const CATALOG = JSON.parse(readFileSync(path.join(PACKAGE_ROOT, 'targets.json'), 'utf8'));
const TARGETS = CATALOG.targets;
const TARGET_BY_ID = new Map(TARGETS.map((target) => [target.id, target]));
const SCOPES = new Set(['project', 'user']);
const FEATURES = [
  { id: 'rsaver', label: 'RSaver', description: 'Context pruning, budgeting, and re-anchoring for long sessions' },
  { id: 'rscan', label: 'RScan', description: 'Read-only project scan with ranked development options at session start' }
];
const FEATURE_IDS = new Set(FEATURES.map((feature) => feature.id));

function usage() {
  console.log(`RCoder ${VERSION}

Usage:
  npx -y github:RidTheWann/RCoder-Skills [options]
  RCoder

Options:
  --target <id>       Target host ID (default: agents)
  --scope <scope>     project | user (default: project)
  --project-dir <p>   Project root (default: current directory)
  --home-dir <p>      User home (default: OS home)
  --interactive       Open the terminal manager
  --list-targets      List supported agents and CLIs
  --dry-run           Preview without writing files
  --uninstall         Remove selected skill and restore the latest backup
  --no-launcher       Do not install/update the global RCoder command
  --features <csv>    Optional tools to enable: rsaver,rscan (default: both)
  --list-features     Show optional tools with short descriptions
  --help              Show this help
  --version           Show version

After installation, open a new terminal and type RCoder.`);
}

function parseArgs(args) {
  const options = {
    target: 'agents', scope: 'project', projectDir: process.cwd(),
    homeDir: HOME, dryRun: false, uninstall: false, interactive: false,
    listTargets: false, noLauncher: false, listFeatures: false,
    features: 'rsaver,rscan'
  };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') { options.help = true; continue; }
    if (arg === '--version' || arg === '-v') { options.version = true; continue; }
    if (arg === '--dry-run') { options.dryRun = true; continue; }
    if (arg === '--uninstall') { options.uninstall = true; continue; }
    if (arg === '--interactive' || arg === '-i') { options.interactive = true; continue; }
    if (arg === '--list-targets') { options.listTargets = true; continue; }
    if (arg === '--no-launcher') { options.noLauncher = true; continue; }
    if (arg === '--list-features') { options.listFeatures = true; continue; }
    if (arg === '--features') {
      if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error('Missing value for --features');
      options.features = args[++i];
      continue;
    }
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
  if (!TARGET_BY_ID.has(options.target)) throw new Error(`Unsupported target: ${options.target}. Use --list-targets.`);
  if (!SCOPES.has(options.scope)) throw new Error(`Unsupported scope: ${options.scope}`);
  parseFeatureSelection(options.features);
  return options;
}

function parseFeatureSelection(value) {
  const raw = String(value).trim().toLowerCase();
  if (raw === 'none' || raw === '') return [];
  const ids = raw.split(',').map((item) => item.trim()).filter(Boolean);
  const unknown = ids.filter((id) => !FEATURE_IDS.has(id));
  if (unknown.length) throw new Error(`Unknown optional tool: ${unknown.join(', ')}. Use --list-features.`);
  if (new Set(ids).size !== ids.length) throw new Error('Duplicate optional tool in --features.');
  return ids;
}

function featureState(value) {
  const selected = new Set(parseFeatureSelection(value));
  return { schema_version: 1, version: VERSION,
    rsaver: selected.has('rsaver'), rscan: selected.has('rscan') };
}

function showFeatures() {
  console.log('\nOptional tools:');
  FEATURES.forEach((feature, index) => {
    console.log(`  ${index + 1}. ${feature.label.padEnd(8)} ${feature.description}`);
  });
}

function writeFeatureManifest(options, target) {
  const { targetRoot } = targetPaths(target, options.scope,
    options.scope === 'project' ? options.projectDir : options.homeDir);
  const manifest = path.join(targetRoot, '.rcoder-features.json');
  if (options.uninstall) {
    if (!options.dryRun && existsSync(manifest)) rmSync(manifest, { force: true });
    return;
  }
  const state = JSON.stringify(featureState(options.features), null, 2) + '\n';
  if (options.dryRun) {
    console.log(`DRY RUN: write optional tool manifest to ${manifest}`);
    return;
  }
  if (existsSync(manifest) && readFileSync(manifest, 'utf8') === state) return;
  assertSafePath(options.scope === 'project' ? options.projectDir : options.homeDir, manifest);
  mkdirSync(targetRoot, { recursive: true });
  writeFileSync(manifest, state, 'utf8');
  console.log(`Enabled optional tools for ${target.label}: ${options.features}`);
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
    return entry.isFile() ? [next] : [];
  }).sort();
}

function sameTree(left, right) {
  if (!existsSync(left) || !existsSync(right) ||
      !statSync(left).isDirectory() || !statSync(right).isDirectory()) return false;
  const a = listFiles(left);
  const b = listFiles(right);
  if (a.length !== b.length || a.some((item, index) => item !== b[index])) return false;
  return a.every((item) => readFileSync(path.join(left, item)).equals(readFileSync(path.join(right, item))));
}

function sameLauncherApp(appRoot) {
  if (!existsSync(appRoot) || !statSync(appRoot).isDirectory()) return false;
  const files = [
    ['scripts/rcoder.mjs', 'scripts/rcoder.mjs'],
    ['targets.json', 'targets.json'],
    ['package.json', 'package.json'],
    ['launcher/RCoder.ps1', 'launcher/RCoder.ps1']
  ];
  for (const [source, installed] of files) {
    const from = path.join(PACKAGE_ROOT, source);
    const to = path.join(appRoot, installed);
    if (!existsSync(from) || !existsSync(to) || !readFileSync(from).equals(readFileSync(to))) return false;
  }
  return sameTree(SOURCE, path.join(appRoot, 'skills', 'rcoder'));
}

function backupEntries(backupRoot, prefix = 'install-') {
  if (!existsSync(backupRoot)) return [];
  return readdirSync(backupRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith(prefix))
    .map((entry) => path.join(backupRoot, entry.name))
    .sort();
}

function targetPaths(target, scope, base) {
  const root = scope === 'project' ? target.project_root : target.user_root;
  const targetRoot = path.join(base, ...root.split('/'));
  return {
    targetRoot,
    destination: path.join(targetRoot, 'skills', 'rcoder'),
    backupRoot: path.join(targetRoot, '.rcoder-backups', 'rcoder'),
    legacyBackupRoot: path.join(targetRoot, '.rcoder-backups', target.id)
  };
}

function installTarget(options, target) {
  if (!existsSync(path.join(SOURCE, 'SKILL.md'))) throw new Error(`Bundled skill missing: ${SOURCE}`);
  const baseInput = options.scope === 'project' ? options.projectDir : options.homeDir;
  if (!existsSync(baseInput) || !statSync(baseInput).isDirectory()) {
    throw new Error(`Selected ${options.scope} directory does not exist: ${baseInput}`);
  }
  const base = realpathSync(baseInput);
  const { destination, backupRoot, legacyBackupRoot } = targetPaths(target, options.scope, base);
  assertSafePath(base, destination);
  assertSafePath(base, backupRoot);
  assertSafePath(base, legacyBackupRoot);
  const stamp = `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`;

  if (options.uninstall) {
    console.log(`Uninstall target: ${target.label} -> ${destination}`);
    if (options.dryRun) {
      console.log(`DRY RUN: move active skill to backup and restore the newest previous backup from ${backupRoot}`);
      return;
    }
    if (existsSync(destination)) {
      mkdirSync(backupRoot, { recursive: true });
      renameSync(destination, path.join(backupRoot, `uninstalled-${stamp}`));
    } else {
      console.log('No active RCoder installation was found.');
    }
    let backups = backupEntries(backupRoot);
    if (backups.length === 0) backups = backupEntries(legacyBackupRoot);
    if (backups.length > 0) {
      mkdirSync(path.dirname(destination), { recursive: true });
      renameSync(backups.at(-1), destination);
      console.log(`Restored previous installation: ${destination}`);
    }
    return;
  }

  if (sameTree(SOURCE, destination)) {
    console.log(`RCoder ${VERSION} is already current for ${target.label} at ${destination}`);
    return;
  }
  console.log(`Install target: ${target.label} (${options.scope}) -> ${destination}`);
  if (options.dryRun) {
    if (existsSync(destination)) console.log(`DRY RUN: back up the existing folder under ${backupRoot}`);
    console.log(`DRY RUN: copy the bundled skill into ${destination}`);
    return;
  }

  mkdirSync(path.dirname(destination), { recursive: true });
  mkdirSync(backupRoot, { recursive: true });
  const stage = path.join(path.dirname(destination), `.rcoder-stage-${stamp}`);
  let savedBackup = null;
  try {
    cpSync(SOURCE, stage, { recursive: true, errorOnExist: true, force: false });
    if (existsSync(destination)) {
      savedBackup = path.join(backupRoot, `install-${stamp}`);
      renameSync(destination, savedBackup);
      console.log(`Backed up previous installation: ${savedBackup}`);
    }
    renameSync(stage, destination);
    console.log(`Installed RCoder ${VERSION} for ${target.label}: ${destination}`);
  } catch (error) {
    if (existsSync(stage)) rmSync(stage, { recursive: true, force: true });
    if (savedBackup && existsSync(savedBackup) && !existsSync(destination)) renameSync(savedBackup, destination);
    throw error;
  }
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

function psLiteral(value) {
  return `'${String(value).replaceAll("'", "''")}'`;
}

function registerWindowsPath(binRoot) {
  const escaped = psLiteral(binRoot);
  const command = `$entry=${escaped}; $current=[Environment]::GetEnvironmentVariable('Path','User'); $items=@(); if($current){$items=@($current -split ';' | Where-Object { $_ })}; $present=$false; foreach($item in $items){if([String]::Equals($item.TrimEnd([char]92),$entry.TrimEnd([char]92),[StringComparison]::OrdinalIgnoreCase)){$present=$true}}; if(-not $present){$items += $entry; [Environment]::SetEnvironmentVariable('Path',($items -join ';'),'User')}`;
  const result = spawnSync('powershell.exe', ['-NoProfile', '-Command', command], { encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) {
    console.warn(`Could not update the user PATH automatically: ${result.stderr || result.error || 'PowerShell failed'}`);
    console.warn(`Add this directory to your user PATH: ${binRoot}`);
  }
}

function registerPosixPath(homeDir, binRoot) {
  const marker = '# RCoder launcher PATH';
  const quoted = shellQuote(binRoot);
  const pattern = 'case ":$PATH:" in *":' + binRoot + ':"*) ;; *) export PATH=' + quoted + ':"$PATH" ;; esac';
  const line = ['', marker, pattern, ''].join('\n');
  const profiles = ['.profile', '.bash_profile', '.bashrc', '.zshrc'];
  let updatedProfile = false;
  for (const profile of profiles) {
    const file = path.join(homeDir, profile);
    if (!existsSync(file)) continue;
    if (lstatSync(file).isSymbolicLink() || !lstatSync(file).isFile()) {
      console.warn('Skipped non-regular shell profile: ' + file);
      continue;
    }
    const current = readFileSync(file, 'utf8');
    if (!current.includes(marker)) appendFileSync(file, line, 'utf8');
    updatedProfile = true;
  }
  if (!updatedProfile) {
    appendFileSync(path.join(homeDir, '.profile'), line, 'utf8');
  }
  const fishConfig = path.join(homeDir, '.config', 'fish', 'config.fish');
  if (existsSync(path.dirname(fishConfig)) &&
      (!existsSync(fishConfig) || !lstatSync(fishConfig).isSymbolicLink())) {
    const current = existsSync(fishConfig) ? readFileSync(fishConfig, 'utf8') : '';
    const fishQuoted = "'" + binRoot.replaceAll('\\', '\\\\').replaceAll("'", "\\'") + "'";
    const fishLine = ['', marker, 'fish_add_path -m ' + fishQuoted, ''].join('\n');
    if (!current.includes(marker)) appendFileSync(fishConfig, fishLine, 'utf8');
  }
}
function installLauncher(homeDir) {
  const launcherRoot = path.join(homeDir, '.rcoder');
  const appRoot = path.join(launcherRoot, 'app');
  const backupRoot = path.join(launcherRoot, 'backups');
  const stage = path.join(launcherRoot, `.app-stage-${Date.now()}-${randomUUID().slice(0, 8)}`);
  assertSafePath(homeDir, launcherRoot);
  assertSafePath(homeDir, appRoot);
  assertSafePath(homeDir, backupRoot);
  const required = [
    path.join(PACKAGE_ROOT, 'scripts', 'rcoder.mjs'),
    path.join(PACKAGE_ROOT, 'targets.json'),
    path.join(PACKAGE_ROOT, 'package.json'),
    path.join(PACKAGE_ROOT, 'launcher', 'RCoder.ps1'),
    path.join(SOURCE, 'SKILL.md')
  ];
  for (const file of required) if (!existsSync(file)) throw new Error(`Launcher source missing: ${file}`);

  mkdirSync(launcherRoot, { recursive: true });
  if (!sameLauncherApp(appRoot)) {
    mkdirSync(stage, { recursive: true });
    let savedBackup = null;
    try {
      mkdirSync(path.join(stage, 'scripts'), { recursive: true });
      mkdirSync(path.join(stage, 'launcher'), { recursive: true });
      mkdirSync(path.join(stage, 'skills'), { recursive: true });
      cpSync(path.join(PACKAGE_ROOT, 'scripts', 'rcoder.mjs'), path.join(stage, 'scripts', 'rcoder.mjs'));
      cpSync(path.join(PACKAGE_ROOT, 'targets.json'), path.join(stage, 'targets.json'));
      cpSync(path.join(PACKAGE_ROOT, 'package.json'), path.join(stage, 'package.json'));
      cpSync(path.join(PACKAGE_ROOT, 'launcher', 'RCoder.ps1'), path.join(stage, 'launcher', 'RCoder.ps1'));
      cpSync(SOURCE, path.join(stage, 'skills', 'rcoder'), { recursive: true });
      mkdirSync(backupRoot, { recursive: true });
      if (existsSync(appRoot)) {
        savedBackup = path.join(backupRoot, `app-${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`);
        renameSync(appRoot, savedBackup);
      }
      renameSync(stage, appRoot);
    } catch (error) {
      if (existsSync(stage)) rmSync(stage, { recursive: true, force: true });
      if (savedBackup && existsSync(savedBackup) && !existsSync(appRoot)) renameSync(savedBackup, appRoot);
      throw error;
    }
  }

  const binRoot = process.platform === 'win32'
    ? path.join(launcherRoot, 'bin')
    : path.join(homeDir, '.local', 'bin');
  mkdirSync(binRoot, { recursive: true });
  if (process.platform === 'win32') {
    const cmdPath = path.join(binRoot, 'RCoder.cmd');
    const manager = path.join(appRoot, 'launcher', 'RCoder.ps1').replaceAll('%', '%%');
    const cmd = ['@echo off', 'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + manager + '" %*', ''].join('\r\n');
    writeFileSync(cmdPath, cmd, 'utf8');
    registerWindowsPath(binRoot);
    console.log(`Installed the global RCoder command: ${cmdPath}`);
  } else {
    const managerCli = path.join(appRoot, 'scripts', 'rcoder.mjs');
    const commandPath = path.join(binRoot, 'RCoder');
    const wrapper = ['#!/bin/sh', 'set -eu', 'exec node ' + shellQuote(managerCli) + ' --interactive "$@"', ''].join('\n');
    writeFileSync(commandPath, wrapper, { encoding: 'utf8', mode: 0o755 });
    chmodSync(commandPath, 0o755);
    registerPosixPath(homeDir, binRoot);
    console.log(`Installed the global RCoder command: ${commandPath}`);
  }
}

async function ask(rl, prompt, fallback = '') {
  const answer = (await rl.question(prompt)).trim();
  return answer || fallback;
}

function showTargets() {
  console.log('\nSupported Agentic AI and CLI hosts:');
  TARGETS.forEach((target, index) => {
    console.log(`${String(index + 1).padStart(2, ' ')}. ${target.label.padEnd(31)} ${target.id}`);
  });
}

async function runInteractive(options) {
  const rl = createInterface({ input: stdin, output: stdout });
  try {
    while (true) {
      console.log(`\nRCoder ${VERSION} — Agent Skill Manager\n`);
      console.log('  1. Install / Update RCoder');
      console.log('  2. Uninstall RCoder');
      console.log('  3. Show supported agents');
      console.log('  0. Exit');
      const action = await ask(rl, '\nChoose an action: ', '0');
      if (action === '0') return;
      if (action === '3') { showTargets(); continue; }
      if (!['1', '2'].includes(action)) throw new Error('Invalid action selection.');

      showTargets();
      const selection = await ask(rl, '\nSelect one or more targets (for example 1,7,10; A = all): ');
      let selected;
      if (selection.toLowerCase() === 'a' || selection.toLowerCase() === 'all') selected = TARGETS;
      else {
        const indices = selection.split(',').map((value) => Number(value.trim()));
        if (indices.some((value) => !Number.isInteger(value) || value < 1 || value > TARGETS.length)) {
          throw new Error('Invalid target selection.');
        }
        selected = [...new Set(indices)].map((index) => TARGETS[index - 1]);
      }
      console.log('\n  1. Project — current project only');
      console.log('  2. User — available across projects');
      const scopeChoice = await ask(rl, '\nChoose installation scope: ', '1');
      if (!['1', '2'].includes(scopeChoice)) throw new Error('Invalid scope selection.');
      const scope = scopeChoice === '1' ? 'project' : 'user';
      if (action === '1') {
        showFeatures();
        console.log('\n  1. Both tools (default)');
        console.log('  2. RSaver only');
        console.log('  3. RScan only');
        console.log('  4. Neither');
        const featureChoice = await ask(rl, '\nEnable optional tools: ', '1');
        if (!['1', '2', '3', '4'].includes(featureChoice)) throw new Error('Invalid optional tool selection.');
        options.features = { 1: 'rsaver,rscan', 2: 'rsaver', 3: 'rscan', 4: 'none' }[featureChoice];
      }
      if (action === '2') {
        const confirmation = await ask(rl, '\nConfirm uninstall and backup the current RCoder folder? (y/N): ', 'n');
        if (!['y', 'yes'].includes(confirmation.toLowerCase())) {
          console.log('Uninstall cancelled.');
          continue;
        }
      }
      const projectDir = scope === 'project'
        ? await ask(rl, `Project directory [${process.cwd()}]: `, process.cwd())
        : options.homeDir;
      const base = scope === 'project' ? path.resolve(projectDir) : path.resolve(options.homeDir);
      if (!existsSync(base) || !statSync(base).isDirectory()) throw new Error(`Selected directory does not exist: ${base}`);

      const seen = new Set();
      for (const target of selected) {
        const destination = path.resolve(targetPaths(target, scope, base).destination);
        const key = process.platform === 'win32' ? destination.toLowerCase() : destination;
        if (seen.has(key)) {
          console.log(`Skipped duplicate discovery root for ${target.label}.`);
          continue;
        }
        seen.add(key);
        const targetOptions = { ...options, scope, projectDir: base, uninstall: action === '2', dryRun: false };
        installTarget(targetOptions, target);
        writeFeatureManifest(targetOptions, target);
      }
      console.log('\nOperation completed. Start a new agent session to refresh its skills.');
    }
  } finally {
    rl.close();
  }
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) { usage(); process.exit(0); }
  if (options.version) { console.log(VERSION); process.exit(0); }
  if (options.listTargets) { showTargets(); process.exit(0); }
  if (options.listFeatures) { showFeatures(); process.exit(0); }
  if (options.interactive) {
    await runInteractive(options);
  } else {
    const target = TARGET_BY_ID.get(options.target);
    installTarget(options, target);
    writeFeatureManifest(options, target);
    if (!options.noLauncher && !options.dryRun && !options.uninstall) installLauncher(options.homeDir);
  }
} catch (error) {
  console.error(`RCoder installer error: ${error.message}`);
  process.exitCode = 1;
}
