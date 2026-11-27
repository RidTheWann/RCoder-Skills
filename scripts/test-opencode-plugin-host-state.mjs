import assert from 'node:assert/strict';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pluginDir = path.join(root, '.opencode', 'plugins');
const source = path.join(pluginDir, 'rcoder.js');
const moduleCopy = path.join(pluginDir, `.rcoder-host-state-test-${process.pid}.mjs`);
const workspace = mkdtempSync(path.join(os.tmpdir(), 'rcoder-host-state-'));
const logDir = path.join(workspace, 'bridge-log');
mkdirSync(logDir);

const fakePython = path.join(workspace, 'fake-python.sh');
writeFileSync(
  fakePython,
  [
    '#!/bin/sh',
    `printf '%s\\n' "$*" > "${logDir}/args-$$.txt"`,
    `cat > "${logDir}/stdin-$$.txt"`,
    "printf '{}\\n'",
    '',
  ].join('\n'),
  { mode: 0o755 },
);
chmodSync(fakePython, 0o755);

const savedEnv = {
  RCODER_PYTHON: process.env.RCODER_PYTHON,
  RCODER_RUNTIME_DISABLE: process.env.RCODER_RUNTIME_DISABLE,
  RCODER_RFC_DISABLE: process.env.RCODER_RFC_DISABLE,
};
process.env.RCODER_PYTHON = fakePython;
delete process.env.RCODER_RUNTIME_DISABLE;
delete process.env.RCODER_RFC_DISABLE;

function payloadsFor(command) {
  const result = [];
  for (const name of readdirSync(logDir).filter((item) => item.startsWith('args-'))) {
    const args = readFileSync(path.join(logDir, name), 'utf8').trim();
    if (!args.includes(command)) continue;
    const stdinPath = path.join(logDir, name.replace(/^args-/, 'stdin-'));
    try {
      result.push(JSON.parse(readFileSync(stdinPath, 'utf8')));
    } catch {
      // A non-JSON call is not a host payload.
    }
  }
  return result;
}

function clearLog() {
  for (const name of readdirSync(logDir)) {
    rmSync(path.join(logDir, name), { force: true });
  }
}

function makeCtx(options, directory) {
  const hooks = [];
  return {
    ctx: {
      app: { version: '2.4.2' },
      location: { directory },
      options,
      session: {
        hook: async (name, callback) => {
          hooks.push({ name, callback });
          return { dispose() {} };
        },
      },
      tool: { hook: async () => ({ dispose() {} }) },
      event: { subscribe: () => ({ async *[Symbol.asyncIterator]() {} }) },
    },
    hooks,
  };
}

let plugin;
try {
  writeFileSync(moduleCopy, readFileSync(source, 'utf8'), 'utf8');
  plugin = await import(pathToFileURL(moduleCopy).href);
} finally {
  rmSync(moduleCopy, { force: true });
}

const realConsoleError = console.error;
console.error = (...args) => {
  if (String(args[0]).startsWith('RCoder RScan skipped')) return;
  realConsoleError(...args);
};

const { createHostState, setupOptions, hostPayload, normalizeDirectory } = plugin.hostStateContract;

// Missing hostOptions: canonical state always supplies normalized defaults.
const missing = createHostState(workspace, undefined);
assert.deepEqual(missing.hostOptions, {
  runtimeDisabled: false,
  rfcDisabled: false,
  runtimePath: '',
});
assert.equal(missing.directory, workspace);
const legacyState = { directory: workspace };
const legacyPayload = hostPayload(legacyState, { session_id: 's1' });
assert.equal(legacyPayload.cwd, workspace);
assert.equal('runtime_disabled' in legacyPayload, false);
assert.equal('rfc_disabled' in legacyPayload, false);
assert.equal('runtime_path' in legacyPayload, false);

// Default host options, including explicit false values that override env.
process.env.RCODER_RUNTIME_DISABLE = '1';
process.env.RCODER_RFC_DISABLE = '1';
assert.deepEqual(setupOptions(undefined), {
  runtimeDisabled: true,
  rfcDisabled: true,
  runtimePath: '',
});
assert.deepEqual(setupOptions({ runtimeDisabled: false, rfcDisabled: false }), {
  runtimeDisabled: false,
  rfcDisabled: false,
  runtimePath: '',
});
delete process.env.RCODER_RUNTIME_DISABLE;
delete process.env.RCODER_RFC_DISABLE;
assert.deepEqual(setupOptions({}), {
  runtimeDisabled: false,
  rfcDisabled: false,
  runtimePath: '',
});

// Workspace config is a deterministic source when OpenCode sanitizes env and
// does not forward configured plugin options to local plugins.
const configWorkspace = path.join(workspace, 'configured');
mkdirSync(path.join(configWorkspace, '.rcoder'), { recursive: true });
writeFileSync(
  path.join(configWorkspace, '.rcoder', 'opencode.json'),
  JSON.stringify({ runtime_disabled: true, runtime_path: 'relative/binary', rfc_disabled: true }),
);
assert.deepEqual(createHostState(configWorkspace, undefined).hostOptions, {
  runtimeDisabled: true,
  rfcDisabled: true,
  runtimePath: '',
});
assert.deepEqual(createHostState(configWorkspace, { runtimeDisabled: false }).hostOptions, {
  runtimeDisabled: false,
  rfcDisabled: true,
  runtimePath: '',
});

const absoluteRuntimePath = path.resolve(workspace, 'fake-runtime', 'rcoder-runtime');

// Disable flags and runtime paths survive into the actual context payload.
const scenarios = [
  {
    name: 'runtime disabled',
    options: { runtime_disabled: true },
    expected: { runtime_disabled: true },
    absent: ['rfc_disabled', 'runtime_path'],
  },
  {
    name: 'RFC disabled',
    options: { rfc_disabled: true },
    expected: { rfc_disabled: true },
    absent: ['runtime_disabled', 'runtime_path'],
  },
  {
    name: 'both disabled',
    options: { runtime_disabled: true, rfc_disabled: 'true' },
    expected: { runtime_disabled: true, rfc_disabled: true },
    absent: ['runtime_path'],
  },
  {
    name: 'valid absolute runtime path',
    options: { runtime_path: absoluteRuntimePath },
    expected: { runtime_path: absoluteRuntimePath },
    absent: ['runtime_disabled', 'rfc_disabled'],
  },
  {
    name: 'invalid relative runtime path',
    options: { runtime_path: 'bin/rcoder-runtime' },
    expected: {},
    absent: ['runtime_disabled', 'rfc_disabled', 'runtime_path'],
  },
];

for (const scenario of scenarios) {
  clearLog();
  const { ctx, hooks } = makeCtx(scenario.options, workspace);
  const cleanup = await plugin.setupV2(ctx);
  assert.equal(typeof cleanup, 'function');
  const contextHook = hooks.find((hook) => hook.name === 'context');
  assert.ok(contextHook, `${scenario.name}: context hook registered`);
  await contextHook.callback({
    sessionID: 'ses-host-state',
    agent: 'build',
    model: {},
    system: [],
    messages: [],
    tools: {},
    options: {},
  });
  const contextPayloads = payloadsFor('context');
  assert.equal(contextPayloads.length, 1, `${scenario.name}: one context bridge call`);
  const payload = contextPayloads[0];
  assert.equal(payload.cwd, workspace);
  for (const [key, value] of Object.entries(scenario.expected)) {
    assert.equal(payload[key], value, `${scenario.name}: ${key}`);
  }
  for (const key of scenario.absent) {
    assert.equal(key in payload, false, `${scenario.name}: ${key} must be absent`);
  }
  cleanup();
}

// Missing or invalid workspace directories fall back to the plugin repository.
for (const directory of [undefined, null, '', 42, {}]) {
  const state = createHostState(directory, {});
  assert.equal(state.directory, root, `invalid workspace ${String(directory)}`);
  const payload = hostPayload(state, { session_id: 's1' });
  assert.equal(payload.cwd, root);
}
assert.equal(normalizeDirectory('   '), root);

// V1/V2 compatibility: both exports keep their documented shapes.
assert.equal(plugin.default.id, 'rcoder');
assert.equal(typeof plugin.default.setup, 'function');
assert.equal(typeof plugin.default.server, 'function');
const v1 = await plugin.default.server({ directory: workspace });
for (const hook of [
  'experimental.chat.system.transform',
  'tool.execute.before',
  'tool.execute.after',
  'experimental.session.compacting',
]) {
  assert.equal(typeof v1[hook], 'function', `V1 hook ${hook}`);
}
clearLog();
const noOptions = makeCtx(undefined, workspace);
const noOptionsCleanup = await plugin.setupV2(noOptions.ctx);
const noOptionsContext = noOptions.hooks.find((hook) => hook.name === 'context');
await noOptionsContext.callback({
  sessionID: 'ses-no-options',
  agent: 'build',
  model: {},
  system: [],
  messages: [],
  tools: {},
  options: {},
});
const noOptionsPayload = payloadsFor('context')[0];
assert.ok(noOptionsPayload, 'context hook must run without hostOptions');
assert.equal('runtime_disabled' in noOptionsPayload, false);
assert.equal('rfc_disabled' in noOptionsPayload, false);
assert.equal('runtime_path' in noOptionsPayload, false);
noOptionsCleanup();

console.log('OpenCode plugin host-state contract: all regression cases passed');

// Sanity check that the canonical plugin source still parses as ESM.
const syntax = spawnSync(process.execPath, ['--check', source], { encoding: 'utf8' });
assert.equal(syntax.status, 0, syntax.stderr);

console.error = realConsoleError;
rmSync(workspace, { recursive: true, force: true });
for (const [key, value] of Object.entries(savedEnv)) {
  if (value === undefined) delete process.env[key];
  else process.env[key] = value;
}
