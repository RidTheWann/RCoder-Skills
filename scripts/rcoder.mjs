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
  --mcp <mode>        MCP server setup after install: none (default) | show (print config) | install (set up automatically)
  --help              Show this help
  --version           Show version
  doctor [--json]     Check runtime, manifest parity, shared contract, and MCP files
  integration <action> <host>  Manage OpenCode, Gemini CLI, Codex, and Claude Code adapters
  skill <new|lint|package>      Author, validate, and package Agent Skills

After installation, open a new terminal and type RCoder.`);
}

function parseArgs(args) {
  if (args[0] === 'doctor') {
    const unknown = args.slice(1).filter((item) => item !== '--json');
    if (unknown.length) throw new Error(`Unknown doctor option: ${unknown.join(' ')}`);
    return { command: 'doctor', json: args.includes('--json') };
  }
  if (args[0] === 'skill') {
    return { command: 'skill', args: args.slice(1) };
  }
  if (args[0] === 'integration') {
    const action = args[1] || 'instructions';
    const host = args[2] || 'claude-code';
    if (!['install', 'update', 'uninstall', 'verify', 'instructions'].includes(action)) {
      throw new Error('integration action must be install, update, uninstall, verify, or instructions');
    }
    if (!['opencode', 'gemini-cli', 'codex', 'claude-code'].includes(host)) {
      throw new Error('integration host must be opencode, gemini-cli, codex, or claude-code');
    }
    const options = { command: 'integration', action, host, scope: 'project', root: process.cwd(), homeDir: HOME, dryRun: false };
    for (let i = 3; i < args.length; i += 1) {
      const arg = args[i];
      if (arg === '--dry-run') { options.dryRun = true; continue; }
      if (['--scope', '--root', '--home-dir'].includes(arg)) {
        if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error(`Missing value for ${arg}`);
        const value = args[++i];
        if (arg === '--scope') options.scope = value;
        if (arg === '--root') options.root = value;
        if (arg === '--home-dir') options.homeDir = value;
        continue;
      }
      throw new Error(`Unknown integration option: ${arg}`);
    }
    if (!SCOPES.has(options.scope)) throw new Error('Integration scope must be project or user');
    return options;
  }
  const options = {
    target: 'agents', scope: 'project', projectDir: process.cwd(),
    homeDir: HOME, dryRun: false, uninstall: false, interactive: false,
    listTargets: false, noLauncher: false, listFeatures: false,
    features: 'rsaver,rscan', mcp: 'none'
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
    if (arg === '--mcp') {
      if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error('Missing value for --mcp');
      options.mcp = args[++i];
      continue;
    }
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
  if (!['none', 'show', 'install'].includes(options.mcp)) throw new Error('--mcp must be none, show, or install');
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
  console.log('\nOptional tools (what they do):');
  FEATURES.forEach((feature) => {
    console.log(`  - ${feature.label.padEnd(8)} ${feature.description}`);
  });
}

function doctorReport() {
  const checks = [];
  const add = (id, status, detail) => checks.push({ id, status, detail });
  const readJson = (relative) => JSON.parse(readFileSync(path.join(PACKAGE_ROOT, relative), 'utf8'));
  const versionFiles = [
    ['package.json', (value) => value.version],
    ['plugin.json', (value) => value.version],
    ['.claude-plugin/plugin.json', (value) => value.version],
    ['.codex-plugin/plugin.json', (value) => value.version],
    ['gemini-extension.json', (value) => value.version],
    ['.claude-plugin/marketplace.json', (value) => value.plugins?.[0]?.version]
  ];
  const versions = {};
  for (const [relative, select] of versionFiles) {
    try { versions[relative] = select(readJson(relative)); }
    catch (error) { versions[relative] = null; add(`manifest:${relative}`, 'FAIL', error.message); }
  }
  try {
    const skill = readFileSync(path.join(SOURCE, 'SKILL.md'), 'utf8');
    const metadataStart = skill.indexOf("\nmetadata:");
    const metadata = metadataStart >= 0 ? skill.slice(metadataStart, skill.indexOf("\n---", metadataStart)) : "";
    const match = metadata.match(/^\s+version:\s*["\x27]?([^"\x27\n]+)["\x27]?\s*$/m);
    versions['skills/rcoder/SKILL.md'] = match?.[1]?.trim() || null;
    if (!versions['skills/rcoder/SKILL.md']) add('skill:metadata-version', 'FAIL', 'SKILL.md metadata version is missing');
  } catch (error) { add('skill:metadata-version', 'FAIL', error.message); }
  try {
    const builder = readFileSync(path.join(PACKAGE_ROOT, 'scripts', 'package'), 'utf8');
    versions['scripts/package'] = builder.match(/^\s*VERSION\s*=\s*['"]([^'"]+)['"]\s*$/m)?.[1] || null;
    if (!versions['scripts/package']) add('package-builder:version', 'FAIL', 'Package builder VERSION is missing');
  } catch (error) { add('package-builder:version', 'FAIL', error.message); }
  let contract = null;
  try {
    contract = readJson('skills/rcoder/contracts/rcoder-v2.json');
    versions['contract'] = contract.product?.version || null;
    add('contract:loaded', 'PASS', `contract ${contract.contract_id || 'unknown'} loaded`);
  } catch (error) { add('contract:loaded', 'FAIL', error.message); }
  const distinct = [...new Set(Object.values(versions).filter(Boolean))];
  const parity = distinct.length === 1 && Object.values(versions).every(Boolean);
  add('version-parity', parity ? 'PASS' : 'FAIL', parity ? `all ${Object.keys(versions).length} version declarations match ${distinct[0]}` : JSON.stringify(versions));
  const required = [
    'skills/rcoder/scripts/rcoder_mcp.py', 'skills/rcoder/scripts/rcoder_mcp_modern.py',
    'skills/rcoder/scripts/rcoder_mcp_http.py', 'skills/rcoder/scripts/rscan.py',
    'skills/rcoder/scripts/rsaver.py', 'skills/rcoder/scripts/rcoder_mcp_setup.py',
    'skills/rcoder/scripts/skill_authoring.py',
    'skills/rcoder/contracts/rcoder-v2.json', 'skills/rcoder/scripts/rcoder_contract.py',
    'launcher/rcoder-mcp.mjs', '.opencode/plugins/rcoder.js', 'gemini-extension.json',
    'GEMINI.md', '.mcp.json', 'mcp.json', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json',
    '.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json',
    'skills/rcoder/references/mcp-transport-engineering.md'
  ];
  for (const relative of required) {
    const present = existsSync(path.join(PACKAGE_ROOT, relative));
    add(`file:${relative}`, present ? 'PASS' : 'FAIL', present ? 'present' : 'missing');
  }
  const python = findPython();
  add('python3', python ? 'PASS' : 'WARN', python ? `usable interpreter: ${python.exe}` : 'Python 3 not found; optional helpers and MCP server cannot run');
  const [nodeMajor, nodeMinor] = process.versions.node.split('.').map(Number);
  const nodeSupported = nodeMajor > 18 || (nodeMajor === 18 && nodeMinor >= 18);
  add('node', nodeSupported ? 'PASS' : 'FAIL', `Node.js ${process.versions.node} (minimum 18.18.0)`);
  if (contract) {
    add('mcp:protocol', contract.mcp?.modern_protocol === '2026-07-28' ? 'PASS' : 'FAIL', contract.mcp?.modern_protocol || 'missing');
    add('mcp:stdio', contract.mcp?.transports?.stdio?.enabled === true ? 'PASS' : 'FAIL', 'stdio transport declaration');
    add('mcp:streamable-http', contract.mcp?.transports?.streamable_http?.enabled === true ? 'PASS' : 'FAIL', 'Streamable HTTP transport declaration');
  }
  const ok = checks.every((item) => item.status !== 'FAIL');
  return { tool: 'RCoder doctor', version: VERSION, ok, checks };
}

function runDoctor(jsonMode) {
  const report = doctorReport();
  if (jsonMode) console.log(JSON.stringify(report, null, 2));
  else {
    console.log(`RCoder doctor — ${report.version}`);
    for (const item of report.checks) console.log(`${item.status.padEnd(4)} ${item.id}: ${item.detail}`);
    console.log(`\n${report.ok ? 'Environment checks passed.' : 'Environment checks found failures.'}`);
  }
  return report.ok ? 0 : 1;
}


function integrationCommand(executable, args) {
  const result = spawnSync(executable, args, { encoding: 'utf8', stdio: 'inherit', windowsHide: true });
  if (result.error?.code === 'ENOENT') {
    console.error(`Required host CLI not found: ${executable}. Install the host CLI, then run the command shown below.`);
    return 127;
  }
  if (result.error) {
    console.error(`Could not start ${executable}: ${result.error.message}`);
    return 1;
  }
  return result.status ?? 1;
}

function printCommand(executable, args) {
  console.log([executable, ...args].map((value) => /\\s/.test(value) ? JSON.stringify(value) : value).join(' '));
}

function runIntegration(options) {
  const { action, host, scope, root, homeDir, dryRun } = options;
  if (host === 'opencode') {
    const projectRoot = path.resolve(root);
    const destination = scope === 'project'
      ? path.join(projectRoot, '.opencode', 'plugins', 'rcoder.js')
      : path.join(path.resolve(homeDir), '.config', 'opencode', 'plugins', 'rcoder.js');
    const source = path.join(PACKAGE_ROOT, '.opencode', 'plugins', 'rcoder.js');
    if (!existsSync(source)) throw new Error('Bundled OpenCode adapter is missing from this RCoder package');
    if (action === 'instructions') {
      console.log('OpenCode V1 adapter: rcoder integration install opencode --scope project|user');
      return 0;
    }
    if (action === 'verify') {
      const exists = existsSync(destination) && statSync(destination).isFile();
      const content = exists ? readFileSync(destination, 'utf8') : '';
      const adapterValid = content.includes('export const RCoderPlugin') && content.includes('RCoder:');
      const skillPath = scope === 'project'
        ? path.join(projectRoot, '.opencode', 'skills', 'rcoder', 'SKILL.md')
        : path.join(path.resolve(homeDir), '.config', 'opencode', 'skills', 'rcoder', 'SKILL.md');
      const skillValid = existsSync(skillPath) && statSync(skillPath).isFile();
      console.log(`OpenCode adapter: ${adapterValid ? 'PRESENT' : 'MISSING'} — ${destination}`);
      console.log(`RCoder skill: ${skillValid ? 'PRESENT' : 'NOT FOUND'} — ${skillPath}`);
      return adapterValid && skillValid ? 0 : 1;
    }
    if (action === 'uninstall') {
      const target = TARGET_BY_ID.get('opencode');
      const base = scope === 'project' ? projectRoot : path.resolve(homeDir);
      const skillDestination = targetPaths(target, scope, base).destination;
      if (!dryRun && existsSync(destination)) {
        const content = readFileSync(destination, 'utf8');
        if (!content.includes('export const RCoderPlugin')) {
          throw new Error(`Refusing to remove a file that is not a recognized RCoder adapter: ${destination}`);
        }
        rmSync(destination);
      }
      if (!dryRun) {
        installTarget({ scope, projectDir: projectRoot, homeDir: path.resolve(homeDir), uninstall: true, dryRun: false }, target);
        writeFeatureManifest({ scope, projectDir: projectRoot, homeDir: path.resolve(homeDir), uninstall: true, dryRun: false }, target);
      } else {
        console.log(`DRY RUN: would remove adapter ${destination} and uninstall skill ${skillDestination}`);
      }
      console.log('Existing host MCP configuration is left untouched; remove its rcoder server entry separately when desired.');
      return 0;
    }
    const target = TARGET_BY_ID.get('opencode');
    const installOptions = { scope, projectDir: projectRoot, homeDir: path.resolve(homeDir), uninstall: false, dryRun, features: 'rsaver,rscan' };
    installTarget(installOptions, target);
    writeFeatureManifest(installOptions, target);
    if (dryRun) { console.log(`DRY RUN: would install OpenCode V1 adapter to ${destination}`); return 0; }
    mkdirSync(path.dirname(destination), { recursive: true });
    if (existsSync(destination)) {
      const existing = readFileSync(destination, 'utf8');
      const sourceText = readFileSync(source, 'utf8');
      if (existing === sourceText) {
        console.log(`OpenCode adapter already current: ${destination}`);
        return 0;
      }
      const backup = `${destination}.rcoder-backup-${Date.now()}`;
      cpSync(destination, backup);
      console.log(`Backed up existing plugin: ${backup}`);
    }
    cpSync(source, destination);
    console.log(`Installed OpenCode V1 adapter: ${destination}`);
    console.log('MCP settings are not changed by this adapter install. Run RCoder MCP setup separately when tool access is required.');
    console.log('Start a new OpenCode session. Native plugin loading still needs to be verified in that host.');
    return 0;
  }

  if (host === 'gemini-cli') {
    const executable = process.env.RCODER_GEMINI_BIN || 'gemini';
    const commands = {
      install: ['extensions', 'install', 'https://github.com/RidTheWann/RCoder-Skills'],
      update: ['extensions', 'update', 'rcoder'],
      uninstall: ['extensions', 'uninstall', 'rcoder'],
      verify: ['--list-extensions']
    };
    if (action === 'instructions') {
      console.log('Install: gemini extensions install https://github.com/RidTheWann/RCoder-Skills');
      console.log('Update:  gemini extensions update rcoder');
      console.log('Remove:  gemini extensions uninstall rcoder');
      console.log('Verify:  gemini --list-extensions');
      return 0;
    }
    const args = commands[action];
    if (dryRun) { console.log('DRY RUN:'); printCommand(executable, args); return 0; }
    const code = integrationCommand(executable, args);
    if (code === 0 && action !== 'uninstall') {
      console.log('Restart Gemini CLI. Extension installation does not by itself prove native model invocation.');
    }
    return code;
  }

  if (host === 'codex') {
    const executable = process.env.RCODER_CODEX_BIN || 'codex';
    const commands = {
      install: ['plugin', 'marketplace', 'add', 'RidTheWann/RCoder-Skills'],
      update: ['plugin', 'marketplace', 'upgrade', 'rcoder-skills'],
      uninstall: ['plugin', 'marketplace', 'remove', 'rcoder-skills'],
      verify: ['plugin', 'marketplace', 'list']
    };
    if (action === 'instructions') {
      console.log('Add marketplace: codex plugin marketplace add RidTheWann/RCoder-Skills');
      console.log('Then open Codex and use /plugins to install the rcoder plugin from rcoder-skills.');
      console.log('The marketplace being present does not itself prove plugin installation or activation.');
      return 0;
    }
    const args = commands[action];
    if (dryRun) { console.log('DRY RUN:'); printCommand(executable, args); return 0; }
    const code = integrationCommand(executable, args);
    if (code === 0 && action === 'install') {
      console.log('Marketplace source added. Open Codex, run /plugins, select rcoder from rcoder-skills, then choose Install.');
    }
    if (code === 0 && action === 'verify') {
      console.log('Marketplace source list read. Confirm rcoder is installed and active in /plugins separately.');
    }
    return code;
  }

  if (host === 'claude-code') {
    if (action === 'uninstall') {
      console.log('Remove RCoder from Claude Code with /plugin and the installed-plugins interface; no local plugin files are deleted by this command.');
      return 0;
    }
    console.log('Run these commands inside a Claude Code session:');
    console.log('/plugin marketplace add RidTheWann/RCoder-Skills');
    console.log('/plugin install rcoder@rcoder-skills');
    if (action === 'verify') console.log('Start a new session and verify the rcoder MCP tools and namespaced commands are available.');
    if (action === 'update') console.log('Use /plugin marketplace update rcoder-skills, then update the installed rcoder plugin.');
    return 0;
  }
  throw new Error(`Unsupported integration host: ${host}`);
}


function runSkillCommand(arguments_) {
  const python = findPython();
  if (!python) {
    console.error('RCoder skill toolkit requires Python 3. Install Python 3 or set it on PATH.');
    return 127;
  }
  const script = path.join(SOURCE, 'scripts', 'skill_authoring.py');
  if (!existsSync(script)) throw new Error(`Bundled skill authoring toolkit is missing: ${script}`);
  const result = spawnSync(python.exe, [...python.pre, script, ...arguments_], {
    cwd: process.cwd(), stdio: 'inherit', windowsHide: true
  });
  if (result.error) {
    console.error(`Could not start skill toolkit: ${result.error.message}`);
    return 1;
  }
  return result.status ?? 1;
}

function findPython() {
  // A candidate must actually run: the Microsoft Store "python.exe" stub is on PATH but cannot execute scripts.
  for (const [exe, pre] of [['python3', []], ['python', []], ['py', ['-3']]]) {
    const probe = spawnSync(exe, [...pre, '-c', 'import sys; print(sys.version_info[0])'],
      { encoding: 'utf8', timeout: 15000 });
    if (!probe.error && probe.status === 0 && probe.stdout.trim() === '3') return { exe, pre };
  }
  return null;
}

function runMcpSetup(mode, target, scope, base) {
  if (mode === 'none') return;
  const scriptsDir = path.join(targetPaths(target, scope, base).destination, 'scripts');
  const helper = path.join(scriptsDir, 'rcoder_mcp_setup.py');
  if (!existsSync(helper)) {
    console.log(`MCP setup skipped for ${target.label}: install or update RCoder there first.`);
    return;
  }
  const python = findPython();
  if (!python) {
    console.log('\nMCP setup skipped: Python 3 was not found (the MCP server is a Python script).');
    console.log('Install Python 3 from https://www.python.org/downloads/ and run RCoder again, then choose "Set up MCP server".');
    return;
  }
  console.log('');
  const done = spawnSync(python.exe, [...python.pre, helper, mode === 'install' ? 'apply' : 'show',
    '--host', target.id, '--scope', scope, '--base', base,
    '--server', path.join(scriptsDir, 'rcoder_mcp_modern.py')], { stdio: 'inherit' });
  if (done.status !== 0) console.log(`Warning: MCP setup reported a problem (exit code ${done.status}).`);
}

function showMcpMenu() {
  console.log('\nMCP server (optional): lets your agent call RCoder tools such as RScan and RSaver.');
  console.log('  1. Show me the exact config to paste (default, changes nothing)');
  console.log('  2. Set it up automatically (safe merge, backup, then self-test)');
  console.log('  3. Skip for now');
}

async function askMcpMode(rl, allowSkip = true) {
  showMcpMenu();
  const choice = await ask(rl, '\nMCP server: ', '1');
  if (!['1', '2', '3'].includes(choice)) throw new Error('Invalid MCP selection.');
  return choice === '2' ? 'install' : choice === '1' ? 'show' : 'none';
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
    ['scripts/package', 'scripts/package'],
    ['launcher/RCoder.ps1', 'launcher/RCoder.ps1'],
    ['launcher/McpSetup.ps1', 'launcher/McpSetup.ps1'],
    ['launcher/rcoder-mcp.mjs', 'launcher/rcoder-mcp.mjs'],
    ['plugin.json', 'plugin.json'],
    ['.mcp.json', '.mcp.json'],
    ['mcp.json', 'mcp.json'],
    ['.claude-plugin/plugin.json', '.claude-plugin/plugin.json'],
    ['.claude-plugin/marketplace.json', '.claude-plugin/marketplace.json'],
    ['.codex-plugin/plugin.json', '.codex-plugin/plugin.json'],
    ['.agents/plugins/marketplace.json', '.agents/plugins/marketplace.json'],
    ['.opencode/plugins/rcoder.js', '.opencode/plugins/rcoder.js'],
    ['gemini-extension.json', 'gemini-extension.json'],
    ['GEMINI.md', 'GEMINI.md']
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
    path.join(PACKAGE_ROOT, 'scripts', 'package'),
    path.join(PACKAGE_ROOT, 'launcher', 'RCoder.ps1'),
    path.join(PACKAGE_ROOT, 'launcher', 'McpSetup.ps1'),
    path.join(PACKAGE_ROOT, 'launcher', 'rcoder-mcp.mjs'),
    path.join(PACKAGE_ROOT, 'plugin.json'),
    path.join(PACKAGE_ROOT, '.mcp.json'),
    path.join(PACKAGE_ROOT, 'mcp.json'),
    path.join(PACKAGE_ROOT, '.claude-plugin', 'plugin.json'),
    path.join(PACKAGE_ROOT, '.claude-plugin', 'marketplace.json'),
    path.join(PACKAGE_ROOT, '.codex-plugin', 'plugin.json'),
    path.join(PACKAGE_ROOT, '.agents', 'plugins', 'marketplace.json'),
    path.join(PACKAGE_ROOT, '.opencode', 'plugins', 'rcoder.js'),
    path.join(PACKAGE_ROOT, 'gemini-extension.json'),
    path.join(PACKAGE_ROOT, 'GEMINI.md'),
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
      mkdirSync(path.join(stage, '.claude-plugin'), { recursive: true });
      mkdirSync(path.join(stage, '.codex-plugin'), { recursive: true });
      mkdirSync(path.join(stage, '.agents', 'plugins'), { recursive: true });
      mkdirSync(path.join(stage, '.opencode', 'plugins'), { recursive: true });
      cpSync(path.join(PACKAGE_ROOT, 'scripts', 'rcoder.mjs'), path.join(stage, 'scripts', 'rcoder.mjs'));
      cpSync(path.join(PACKAGE_ROOT, 'targets.json'), path.join(stage, 'targets.json'));
      cpSync(path.join(PACKAGE_ROOT, 'package.json'), path.join(stage, 'package.json'));
      cpSync(path.join(PACKAGE_ROOT, 'scripts', 'package'), path.join(stage, 'scripts', 'package'));
      cpSync(path.join(PACKAGE_ROOT, 'launcher', 'RCoder.ps1'), path.join(stage, 'launcher', 'RCoder.ps1'));
      cpSync(path.join(PACKAGE_ROOT, 'launcher', 'McpSetup.ps1'), path.join(stage, 'launcher', 'McpSetup.ps1'));
      for (const relative of [
        'launcher/rcoder-mcp.mjs', 'plugin.json', '.mcp.json', 'mcp.json',
        '.claude-plugin/plugin.json', '.claude-plugin/marketplace.json',
        '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json',
        '.opencode/plugins/rcoder.js', 'gemini-extension.json', 'GEMINI.md'
      ]) {
        cpSync(path.join(PACKAGE_ROOT, relative), path.join(stage, relative));
      }
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
    const managerCli = path.join(appRoot, 'scripts', 'rcoder.mjs');
    const cmd = ['@echo off',
      'if "%~1"=="skill" goto nodecli', 'if "%~1"=="integration" goto nodecli', 'if "%~1"=="doctor" goto nodecli',
      'where powershell.exe >nul 2>nul', 'if not errorlevel 1 goto winps',
      'where pwsh.exe >nul 2>nul', 'if not errorlevel 1 goto pwsh7', 'echo PowerShell was not found on PATH.', 'exit /b 1',
      ':nodecli', 'node "' + managerCli + '" %*', 'exit /b %ERRORLEVEL%',
      ':winps', 'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + manager + '" %*', 'goto :eof',
      ':pwsh7', 'pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + manager + '" %*', ''].join('\r\n');
    writeFileSync(cmdPath, cmd, 'utf8');
    registerWindowsPath(binRoot);
    console.log(`Installed the global RCoder command: ${cmdPath}`);
  } else {
    const managerCli = path.join(appRoot, 'scripts', 'rcoder.mjs');
    const commandPath = path.join(binRoot, 'RCoder');
    const wrapper = ['#!/bin/sh', 'set -eu',
      'manager=' + shellQuote(managerCli),
      'if [ "$#" -eq 0 ]; then exec node "$manager" --interactive; fi',
      'exec node "$manager" "$@"', ''].join('\n');
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
      console.log('  4. Set up MCP server (no reinstall needed)');
      console.log('  0. Exit');
      const action = await ask(rl, '\nChoose an action: ', '0');
      if (action === '0') return;
      if (action === '3') { showTargets(); continue; }
      if (!['1', '2', '4'].includes(action)) throw new Error('Invalid action selection.');

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
        console.log('\nChoose which to enable:');
        console.log('  1. Both tools (default)');
        console.log('  2. RSaver only');
        console.log('  3. RScan only');
        console.log('  4. Neither');
        const featureChoice = await ask(rl, '\nEnable optional tools: ', '1');
        if (!['1', '2', '3', '4'].includes(featureChoice)) throw new Error('Invalid optional tool selection.');
        options.features = { 1: 'rsaver,rscan', 2: 'rsaver', 3: 'rscan', 4: 'none' }[featureChoice];
        options.mcp = await askMcpMode(rl);
      }
      if (action === '4') {
        console.log('\nThis configures the MCP server for hosts where RCoder is already installed.');
        options.mcp = await askMcpMode(rl);
        if (options.mcp === 'none') { console.log('MCP setup skipped.'); continue; }
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
        if (action === '4') { runMcpSetup(options.mcp, target, scope, base); continue; }
        const targetOptions = { ...options, scope, projectDir: base, uninstall: action === '2', dryRun: false };
        installTarget(targetOptions, target);
        writeFeatureManifest(targetOptions, target);
        if (action === '1') runMcpSetup(options.mcp, target, scope, base);
      }
      console.log('\nOperation completed. Start a new agent session to refresh its skills.');
    }
  } finally {
    rl.close();
  }
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.command === 'doctor') {
    process.exitCode = runDoctor(options.json);
  } else if (options.command === 'integration') {
    process.exitCode = runIntegration(options);
  } else if (options.command === 'skill') {
    process.exitCode = runSkillCommand(options.args);
  } else if (options.help) {
    usage();
  } else if (options.version) {
    console.log(VERSION);
  } else if (options.listTargets) {
    showTargets();
  } else if (options.listFeatures) {
    showFeatures();
  } else if (options.interactive) {
    await runInteractive(options);
  } else {
    const target = TARGET_BY_ID.get(options.target);
    installTarget(options, target);
    writeFeatureManifest(options, target);
    if (!options.noLauncher && !options.dryRun && !options.uninstall) installLauncher(options.homeDir);
    const mcpBase = options.scope === 'project' ? path.resolve(options.projectDir) : path.resolve(options.homeDir);
    if (options.dryRun && options.mcp !== 'none') console.log(`DRY RUN: MCP mode '${options.mcp}' would run after the skill is installed.`);
    else if (!options.uninstall) runMcpSetup(options.mcp, target, options.scope, mcpBase);
    if (!options.uninstall && !options.dryRun && options.mcp === 'none') {
      console.log('Optional MCP server: type RCoder and choose "Set up MCP server", or re-run with --mcp show or --mcp install.');
    }
  }
} catch (error) {
  console.error(`RCoder installer error: ${error.message}`);
  process.exitCode = 1;
}
