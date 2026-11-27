import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, '.opencode', 'plugins', 'rcoder.js');
const testModule = path.join(root, '.opencode', 'plugins', `.rcoder-v2-test-${process.pid}.mjs`);
const workspace = mkdtempSync(path.join(os.tmpdir(), 'rcoder-opencode-v2-'));
const python = process.env.RCODER_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const sessionID = 'opencode-session-001';

function makeEventFeed() {
  const buffer = [];
  let notify;
  let closed = false;
  return {
    push(event) {
      buffer.push(event);
      if (notify) {
        const resolve = notify;
        notify = undefined;
        resolve();
      }
    },
    close() {
      closed = true;
      if (notify) {
        const resolve = notify;
        notify = undefined;
        resolve();
      }
    },
    async *[Symbol.asyncIterator]() {
      while (!closed) {
        if (buffer.length) {
          yield buffer.shift();
          continue;
        }
        await new Promise((resolve) => { notify = resolve; });
      }
    },
  };
}

function makeContext(directory, feed) {
  const hooks = { context: [], prompt: [], compaction: [], toolBefore: [], toolAfter: [] };
  const registration = { dispose: async () => {} };
  const ctx = {
    app: { version: '2.4.2' },
    location: { directory },
    session: {
      hook: async (name, callback) => {
        assert.ok(hooks[name], `unexpected session hook ${name}`);
        hooks[name].push(callback);
        return registration;
      },
    },
    tool: {
      hook: async (name, callback) => {
        if (name === 'execute.before') hooks.toolBefore.push(callback);
        else if (name === 'execute.after') hooks.toolAfter.push(callback);
        else throw new Error(`unexpected tool hook ${name}`);
        return registration;
      },
    },
    event: { subscribe: () => feed },
  };
  return { ctx, hooks };
}

function runPython(args, input) {
  return spawnSync(python, args, {
    input,
    encoding: 'utf8',
    timeout: 20000,
    windowsHide: true,
  });
}

function seedContextItem() {
  const result = runPython(
    [
      path.join(root, 'scripts', 'context-fabric.py'),
      '--root', workspace,
      'put',
      '--session', sessionID,
      '--kind', 'objective',
      '--title', 'OpenCode V2 objective',
      '--source', 'test-fixture',
      '--file', '-',
    ],
    'Hydrate the exact OpenCode model request and preserve its source provenance.',
  );
  assert.equal(result.status, 0, result.stderr);
}

function exportTranscript(promptID) {
  const result = runPython([
    path.join(root, 'scripts', 'context-fabric.py'),
    '--root', workspace,
    'export',
    '--session', sessionID,
    '--prompt', promptID,
  ]);
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

async function waitForAcknowledgement(promptID, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const exported = exportTranscript(promptID);
    if (exported.acknowledged) return exported;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error('RFC response was not acknowledged before the timeout');
}

async function waitForMessageCount(promptID, count, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const exported = exportTranscript(promptID);
    if (exported.messages.length >= count) return exported;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`RFC transcript did not reach ${count} message(s) before the timeout`);
}

try {
  writeFileSync(testModule, readFileSync(source, 'utf8'), 'utf8');
  const { setupV2 } = await import(pathToFileURL(testModule).href);

  seedContextItem();
  const feed = makeEventFeed();
  const { ctx, hooks } = makeContext(workspace, feed);
  const cleanup = await setupV2(ctx);
  assert.equal(typeof cleanup, 'function');
  assert.equal(hooks.context.length, 1);
  assert.equal(hooks.compaction.length, 1);
  assert.equal(hooks.toolBefore.length, 1);
  assert.equal(hooks.toolAfter.length, 1);

  const system = [];
  await hooks.context[0]({
    sessionID,
    agent: 'build',
    model: { providerID: 'opencode', id: 'test-model' },
    system,
    messages: [],
    tools: {},
    options: {},
  });
  const serializedSystem = system.map((item) => item.text || '').join('\n');
  assert.match(serializedSystem, /RCoder: The selected Agent Skill is at/);
  assert.match(serializedSystem, /RScan:/);
  assert.match(serializedSystem, /# Context Fabric/);
  assert.match(serializedSystem, /OpenCode V2 objective/);
  const promptID = serializedSystem.match(/prompt_id: ([A-Za-z0-9._:-]+)/)?.[1];
  assert.ok(promptID, 'RFC payload must expose the request identity');
  const token = serializedSystem.match(/<!-- RFC-ACK: ([^ ]+) -->/)?.[1];
  assert.ok(token, 'RFC payload must contain a delivery canary');
  assert.equal((serializedSystem.match(/<!-- RFC-ACK: /g) || []).length, 1);

  // Step boundaries are the capture unit. A tool continuation can prepare the
  // next delivery before the previous step's text event arrives.
  feed.push({ type: 'session.step.started', data: { sessionID, assistantMessageID: 'assistant-1' } });

  const system2 = [];
  await hooks.context[0]({
    sessionID,
    agent: 'build',
    model: { providerID: 'opencode', id: 'test-model' },
    system: system2,
    messages: [],
    tools: {},
    options: {},
  });
  const serialized2 = system2.map((item) => item.text || '').join('\n');
  const promptID2 = serialized2.match(/prompt_id: ([A-Za-z0-9._:-]+)/)?.[1];
  const token2 = serialized2.match(/<!-- RFC-ACK: ([^ ]+) -->/)?.[1];
  assert.ok(promptID2 && token2);
  assert.notEqual(promptID2, promptID);

  feed.push({
    type: 'session.text.ended',
    data: { sessionID, assistantMessageID: 'assistant-1', ordinal: 0, text: `Done.\n<!-- RFC-ACK: ${token} -->` },
  });
  feed.push({ type: 'session.step.ended', data: { sessionID, assistantMessageID: 'assistant-1', finish: 'tool-calls' } });
  const exported = await waitForAcknowledgement(promptID);
  assert.equal(exported.acknowledged, true);
  assert.equal(exported.messages.length, 1);
  assert.ok(!JSON.stringify(exported).includes(token), 'exported transcript must not contain the raw canary');

  // The late step-1 text must not be attributed to the newer delivery.
  const notYet = exportTranscript(promptID2);
  assert.equal(notYet.messages.length, 0);
  assert.equal(notYet.acknowledged, false);

  // The second model request's step is attributed to the second delivery.
  feed.push({ type: 'session.step.started', data: { sessionID, assistantMessageID: 'assistant-2' } });
  feed.push({
    type: 'session.text.ended',
    data: { sessionID, assistantMessageID: 'assistant-2', ordinal: 0, text: `Again.\n<!-- RFC-ACK: ${token2} -->` },
  });
  feed.push({ type: 'session.step.ended', data: { sessionID, assistantMessageID: 'assistant-2', finish: 'stop' } });
  const second = await waitForAcknowledgement(promptID2);
  assert.equal(second.messages.length, 1);
  assert.ok(!JSON.stringify(second).includes(token2));

  // Repeated completion/stop events must neither duplicate nor delete a canary.
  for (let index = 0; index < 2; index += 1) {
    feed.push({ type: 'session.execution.succeeded', data: { sessionID } });
  }
  await new Promise((resolve) => setTimeout(resolve, 300));
  feed.push({ type: 'session.step.started', data: { sessionID, assistantMessageID: 'assistant-3' } });
  feed.push({
    type: 'session.text.ended',
    data: { sessionID, assistantMessageID: 'assistant-3', ordinal: 0, text: `Third.\n<!-- RFC-ACK: ${token2} -->` },
  });
  feed.push({ type: 'session.step.ended', data: { sessionID, assistantMessageID: 'assistant-3', finish: 'stop' } });
  const repeated = await waitForMessageCount(promptID2, 2);
  assert.ok(!JSON.stringify(repeated).includes(token2));
  assert.equal(exportTranscript(promptID).messages.length, 1);

  // Guard, workspace confinement, bounded reads, and output redaction.
  writeFileSync(path.join(workspace, '.env'), 'TOKEN=must-not-be-read\n');
  await assert.rejects(
    hooks.toolBefore[0]({ tool: 'read', input: { filePath: '.env' } }),
    /RCoder Guard blocked/,
  );
  await assert.rejects(
    hooks.toolBefore[0]({ tool: 'read', input: { filePath: '../outside.txt' } }),
    /escapes the active workspace/,
  );
  writeFileSync(path.join(workspace, 'large.txt'), 'line\n'.repeat(9000), 'utf8');
  const bounded = { tool: 'read', input: { filePath: 'large.txt' } };
  await hooks.toolBefore[0](bounded);
  assert.equal(bounded.input.limit, 160, 'large reads must be bounded');

  mkdirSync(path.join(workspace, 'src'));
  const edited = {
    tool: 'edit',
    input: { filePath: 'src/parser.js' },
    status: 'completed',
    result: { content: 'api_key=ABCDEFGHIJKLMNOPQRSTUVWX' },
  };
  await hooks.toolAfter[0](edited);
  assert.doesNotMatch(edited.result.content, /ABCDEFGHIJKLMNOPQRSTUVWX/);

  const compaction = {
    system: [],
    messages: [],
    options: {},
  };
  await hooks.compaction[0](compaction);
  const capsule = compaction.system.map((item) => item.text || '').join('\n');
  assert.match(capsule, /## RCoder Active Session Capsule/);
  assert.match(capsule, /src\/parser\.js/);
  assert.match(capsule, /SHA-256: [a-f0-9]{64}/);
  assert.doesNotMatch(capsule, /ABCDEFGHIJKLMNOPQRSTUVWX/);

  feed.push({ type: 'session.deleted', data: { sessionID } });
  const canaryDir = path.join(workspace, '.rcoder', 'private', 'rfc-canaries');
  const cleanupDeadline = Date.now() + 8000;
  while (readdirSync(canaryDir).length > 0 && Date.now() < cleanupDeadline) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.equal(readdirSync(canaryDir).length, 0, 'session deletion must remove private canary state');

  cleanup();
  feed.close();
  console.log('OpenCode V2 plugin: RFC hydration, canary capture, guard, redaction and capsule passed');
} finally {
  rmSync(testModule, { force: true });
  rmSync(workspace, { recursive: true, force: true });
}
