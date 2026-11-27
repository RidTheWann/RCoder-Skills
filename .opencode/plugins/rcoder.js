import { createHash, randomUUID } from 'node:crypto';
import { existsSync, readFileSync, realpathSync, statSync } from 'node:fs';
import path from 'node:path';
import { spawn, execFile, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const pluginDirectory = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(pluginDirectory, '..', '..');
const installedSkillDirectory = path.resolve(pluginDirectory, '..', 'skills', 'rcoder');
const sourceSkillDirectory = path.resolve(pluginDirectory, '..', '..', 'skills', 'rcoder');
const skillDirectory = existsSync(path.join(installedSkillDirectory, 'SKILL.md'))
  ? installedSkillDirectory : sourceSkillDirectory;
const skillFile = path.join(skillDirectory, 'SKILL.md');
const scriptDirectory = path.join(skillDirectory, 'scripts');
const rscan = path.join(scriptDirectory, 'rscan.py');
const hooksScript = path.join(scriptDirectory, 'rcoder_hooks.py');
const rsaverScript = path.join(scriptDirectory, 'rsaver.py');
const opencodeHost = path.join(scriptDirectory, 'opencode_host.py');
const pythonCandidates = process.env.RCODER_PYTHON ? [process.env.RCODER_PYTHON] : (process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python']);
const COMPRESS_THRESHOLD_CHARS = 4000;
const MAX_RAW_READ_BYTES = 25 * 1024;
const MAX_RAW_READ_LINES = 160;
const MAX_BRIDGE_OUTPUT_BYTES = 2_000_000;

function debugLog(message) {
  if (process.env.RCODER_OPENCODE_DEBUG === '1') {
    console.error(`RCoder OpenCode: ${message}`);
  }
}

async function runPython(script, args, timeout, input) {
  let lastError;
  for (const python of pythonCandidates) {
    const prefix = python === 'py' ? ['-3'] : [];
    try {
      const result = await execFileAsync(python, [...prefix, script, ...args], {
        timeout,
        maxBuffer: 4000000,
        encoding: 'utf8',
        windowsHide: true,
        ...(input === undefined ? {} : { input }),
      });
      return result.stdout;
    } catch (error) {
      lastError = error;
      if (error.code !== 'ENOENT') throw error;
    }
  }
  throw lastError || new Error('Python 3 was not found');
}

function runPythonInput(script, args, input, timeout) {
  return new Promise((resolve, reject) => {
    let child;
    try {
      const python = pythonCandidates[0];
      const prefix = python === 'py' ? ['-3'] : [];
      child = spawn(python, [...prefix, script, ...args], {
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
      });
    } catch (error) {
      reject(error);
      return;
    }

    let stdout = '';
    let stderr = '';
    let settled = false;
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (error) reject(error); else resolve(value);
    };
    const timer = setTimeout(() => {
      child.kill();
      finish(new Error(`Python bridge timed out after ${timeout} ms`));
    }, timeout);

    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      stdout += chunk;
      if (Buffer.byteLength(stdout, 'utf8') > MAX_BRIDGE_OUTPUT_BYTES) {
        child.kill();
        finish(new Error('Python bridge output exceeded the safety limit'));
      }
    });
    child.stderr.on('data', (chunk) => {
      if (stderr.length < 10000) stderr += chunk;
    });
    child.on('error', (error) => finish(error));
    child.on('close', (code) => {
      if (code === 0) {
        finish(undefined, stdout);
      } else {
        finish(new Error((stderr || `bridge exited with ${code}`).trim()));
      }
    });
    child.stdin.on('error', () => {});
    child.stdin.end(input);
  });
}

function runPythonSync(script, args, input, timeout) {
  let lastError;
  for (const python of pythonCandidates) {
    const prefix = python === 'py' ? ['-3'] : [];
    const result = spawnSync(python, [...prefix, script, ...args], {
      input,
      encoding: 'utf8',
      timeout,
      maxBuffer: 4000000,
      windowsHide: true,
    });
    if (result.error) {
      lastError = result.error;
      continue;
    }
    if (result.status !== 0) {
      throw new Error((result.stderr || `${script} exited with ${result.status}`).trim());
    }
    return result.stdout;
  }
  throw lastError || new Error('Python 3 was not found');
}

async function scanProject(directory) {
  return (await runPython(rscan, ['scan', '--root', directory, '--hook', 'opencode'], 12000)).trimEnd();
}

function textOfSystemPart(item) {
  return typeof item === 'string' ? item : (item && item.text) || '';
}

function appendSystemText(system, prefix, text) {
  if (!Array.isArray(system) || typeof text !== 'string' || !text.trim()) return false;
  if (system.some((item) => textOfSystemPart(item).startsWith(prefix))) return false;
  system.push({ type: 'text', text });
  return true;
}

function guardPayload(toolName, toolInput) {
  return JSON.stringify({
    hook_event_name: 'PreToolUse',
    tool_name: toolName || 'unknown',
    tool_input: toolInput || {},
  });
}

function deniedGuardReason(raw) {
  if (!raw || !raw.trim()) return undefined;
  try {
    const decision = JSON.parse(raw).hookSpecificOutput;
    if (decision && decision.permissionDecision === 'deny') {
      return `RCoder Guard blocked unsafe tool execution: ${decision.permissionDecisionReason || 'denied'}`;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

async function guardTool(input, output) {
  if (!existsSync(hooksScript)) return;
  const payload = guardPayload(input.tool || input.toolName, output.args || {});
  let raw;
  try {
    raw = runPythonSync(hooksScript, ['guard'], payload, 5000);
  } catch (error) {
    console.error('RCoder guard skipped:', error && error.message ? error.message : String(error));
    return;
  }
  const reason = deniedGuardReason(raw);
  if (reason) throw new Error(reason);
}

function guardToolV2(event) {
  if (!existsSync(hooksScript)) return;
  let raw;
  try {
    raw = runPythonSync(hooksScript, ['guard'], guardPayload(event.tool, event.input), 5000);
  } catch (error) {
    console.error('RCoder guard skipped:', error && error.message ? error.message : String(error));
    return;
  }
  const reason = deniedGuardReason(raw);
  if (reason) throw new Error(reason);
}

function boundRead(args, workspaceDirectory) {
  if (!args || typeof args !== 'object') return;
  const requested = args.filePath || args.file_path || args.path;
  if (typeof requested !== 'string' || !requested.trim()) return;
  const candidate = path.resolve(workspaceDirectory, requested);
  const relative = path.relative(workspaceDirectory, candidate);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error('[RCoder Guard] Read path escapes the active workspace.');
  }
  if (!existsSync(candidate)) return;
  const realRoot = realpathSync(workspaceDirectory);
  const realTarget = realpathSync(candidate);
  const realRelative = path.relative(realRoot, realTarget);
  if (realRelative === '..' || realRelative.startsWith(`..${path.sep}`) || path.isAbsolute(realRelative)) {
    throw new Error('[RCoder Guard] Read symlink escapes the active workspace.');
  }
  const stat = statSync(realTarget);
  if (stat.isFile() && stat.size > MAX_RAW_READ_BYTES && !args.offset && !args.limit) {
    args.limit = MAX_RAW_READ_LINES;
  }
}

function compactOutput(text) {
  const redacted = runPythonSync(rsaverScript, ['redact', '-', '--profile', 'generic'], text, 8000).trimEnd();
  return runPythonSync(
    rsaverScript,
    ['compact', '-', '--max-lines', '120', '--head', '8', '--tail', '8', '--profile', 'generic'],
    redacted,
    8000,
  ).trimEnd();
}

function redactText(text) {
  if (!existsSync(rsaverScript) || typeof text !== 'string') return text;
  return runPythonSync(rsaverScript, ['redact', '-', '--profile', 'generic'], text, 8000).trimEnd();
}

function optimizationDisabled(workspaceDirectory) {
  if (process.env.RCODER_OPENCODE_NO_OPTIMIZE === '1') return true;
  if (typeof workspaceDirectory !== 'string' || !workspaceDirectory) return false;
  return existsSync(path.join(workspaceDirectory, '.rcoder', 'opencode-no-optimize'));
}

function optimizeText(text, workspaceDirectory) {
  if (optimizationDisabled(workspaceDirectory)) return text;
  const redacted = redactText(text);
  if (redacted.length < COMPRESS_THRESHOLD_CHARS) return redacted;
  const packed = compactOutput(redacted);
  if (packed && packed.length < redacted.length) {
    const savedPct = Math.round((1 - packed.length / redacted.length) * 100);
    return `[rcoder:rsaver saved ${savedPct}%]\n${packed}`;
  }
  return redacted;
}

function recordEditedFile(editedFiles, workspaceDirectory, toolName, args) {
  if (!['edit', 'write', 'multiedit', 'create'].includes(String(toolName).toLowerCase())) return;
  const requested = args && (args.filePath || args.file_path || args.path);
  if (typeof requested !== 'string') return;
  const absolute = path.resolve(workspaceDirectory, requested);
  const relative = path.relative(workspaceDirectory, absolute);
  if (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative)) {
    editedFiles.add(relative.split(path.sep).join('/'));
  }
}

function sessionCapsule(workspaceDirectory, activeObjective, editedFiles) {
  const state = {
    schema: 'rcoder-session-capsule-v1',
    workspace: path.basename(workspaceDirectory),
    objective: activeObjective || 'Not captured; recover latest user objective from the conversation.',
    modified_files: Array.from(editedFiles).sort(),
    invariant: 'Inspect the final diff and run rcoder_impact_test plus the narrowest relevant verification before claiming completion.',
  };
  let serialized = JSON.stringify(state);
  try {
    serialized = redactText(serialized);
  } catch (error) {
    console.error('RCoder capsule redaction skipped:', error && error.message ? error.message : String(error));
  }
  const digest = createHash('sha256').update(serialized, 'utf8').digest('hex');
  return [
    '## RCoder Active Session Capsule',
    `- SHA-256: ${digest}`,
    `- Workspace: ${path.basename(workspaceDirectory)}`,
    `- State (secret-redacted JSON): ${serialized}`,
    '- Before stopping: inspect the final diff, run the narrowest relevant tests, and record verified evidence. This capsule is not proof that checks passed.',
  ].join('\n');
}

function newRequestId() {
  return `oc-${Date.now().toString(36)}-${randomUUID().replaceAll('-', '')}`;
}

function optionFlag(options, key, envName) {
  if (Object.prototype.hasOwnProperty.call(options, key)) {
    return options[key] === true || options[key] === 1 || options[key] === '1' || options[key] === 'true';
  }
  return process.env[envName] === '1';
}

function readWorkspaceOptions(directory) {
  if (typeof directory !== 'string' || !directory.trim()) return {};
  for (const candidate of [
    path.join(directory, '.rcoder', 'opencode.json'),
    path.join(directory, '.opencode', 'rcoder.json'),
  ]) {
    if (!existsSync(candidate)) continue;
    try {
      const parsed = JSON.parse(readFileSync(candidate, 'utf8'));
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
    } catch (error) {
      debugLog(`workspace RCoder options skipped: ${error && error.message ? error.message : String(error)}`);
    }
  }
  return {};
}

function setupOptions(options, directory) {
  const values = {
    ...readWorkspaceOptions(directory),
    ...(options && typeof options === 'object' && !Array.isArray(options) ? options : {}),
  };
  const flag = (normalizedKey, hostKey, envName) => {
    if (Object.prototype.hasOwnProperty.call(values, normalizedKey)) {
      return values[normalizedKey] === true;
    }
    return optionFlag(values, hostKey, envName);
  };
  const runtimePath = values.runtimePath || values.runtime_path;
  return {
    runtimeDisabled: flag('runtimeDisabled', 'runtime_disabled', 'RCODER_RUNTIME_DISABLE'),
    rfcDisabled: flag('rfcDisabled', 'rfc_disabled', 'RCODER_RFC_DISABLE'),
    runtimePath: typeof runtimePath === 'string' && runtimePath.trim() && path.isAbsolute(runtimePath.trim())
      ? path.resolve(runtimePath.trim())
      : '',
  };
}

function normalizeDirectory(raw) {
  if (typeof raw === 'string' && raw.trim()) {
    try {
      return path.resolve(raw.trim());
    } catch {
      return repoRoot;
    }
  }
  return repoRoot;
}

/** The single canonical state shape shared by V2 hooks and host payloads. */
function createHostState(rawDirectory, options) {
  const directory = normalizeDirectory(rawDirectory);
  return {
    directory,
    hostOptions: setupOptions(options, directory),
    activeObjective: '',
    editedFiles: new Set(),
    assistantText: new Map(),
    managedSessions: new Set(),
    latestPrompt: new Map(),
    stepPrompt: new Map(),
    lastScan: null,
  };
}

function hostPayload(state, extra) {
  const current = state && typeof state === 'object' ? state : {};
  const options = setupOptions(current.hostOptions, current.directory);
  return {
    ...(extra && typeof extra === 'object' ? extra : {}),
    cwd: normalizeDirectory(current.directory),
    ...(options.runtimeDisabled ? { runtime_disabled: true } : {}),
    ...(options.rfcDisabled ? { rfc_disabled: true } : {}),
    ...(options.runtimePath ? { runtime_path: options.runtimePath } : {}),
  };
}

async function runOpencodeHost(command, payload, timeout) {
  if (!existsSync(opencodeHost)) return {};
  try {
    const raw = await runPythonInput(opencodeHost, [command], JSON.stringify(payload), timeout);
    if (!raw || !raw.trim()) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (error) {
    debugLog(`${command} bridge skipped: ${error && error.message ? error.message : String(error)}`);
    return {};
  }
}

async function injectV2Context(event, state) {
  const system = event && event.system;
  if (!Array.isArray(system) || !existsSync(skillFile)) return;

  appendSystemText(
    system,
    'RCoder:',
    `RCoder: The selected Agent Skill is at ${skillFile}. Read that exact file's routing instructions and only the relevant specialist reference. Use RCoder MCP tools when available; preserve project policy and verify changes with evidence.`,
  );

  const sessionID = typeof event.sessionID === 'string' ? event.sessionID : '';
  const jobs = [];
  const cachedScan = state.lastScan && Date.now() - state.lastScan.at < 60_000;
  jobs.push(
    (cachedScan
      ? Promise.resolve(state.lastScan.summary)
      : scanProject(state.directory).then((summary) => {
          state.lastScan = { at: Date.now(), summary };
          return summary;
        })
    )
      .then((summary) => {
        appendSystemText(system, 'RScan:', summary);
      })
      .catch((error) => {
        console.error('RCoder RScan skipped:', error && error.message ? error.message : String(error));
      }),
  );

  if (sessionID) {
    jobs.push(
      runOpencodeHost('context', hostPayload(state, {
        session_id: sessionID,
        request_id: newRequestId(),
      }), 9000).then((payload) => {
        if (payload.runtime && typeof payload.runtime.text === 'string') {
          appendSystemText(system, 'RCoder Runtime', payload.runtime.text);
        }
        if (payload.rfc && typeof payload.rfc.text === 'string') {
          appendSystemText(system, '# Context Fabric', payload.rfc.text);
          if (typeof payload.rfc.prompt_id === 'string') {
            state.managedSessions.add(sessionID);
            state.latestPrompt.set(sessionID, payload.rfc.prompt_id);
          }
        }
      }),
    );
  }

  await Promise.all(jobs);

  try {
    const lessonsFile = path.join(state.directory, '.rcoder', 'lessons.jsonl');
    if (existsSync(lessonsFile)) {
      const count = readFileSync(lessonsFile, 'utf8').split(/\r?\n/).filter(Boolean).length;
      if (count > 0) {
        appendSystemText(system, 'RCoder Memory:', `RCoder Memory: ${count} verified episodic lesson(s) available via rcoder_recall.`);
      }
    }
  } catch (error) {
    console.error('RCoder memory summary skipped:', error && error.message ? error.message : String(error));
  }
}

function bufferAssistantText(state, data) {
  if (!data || typeof data !== 'object') return;
  const sessionID = data.sessionID;
  const messageID = data.assistantMessageID;
  const text = data.text;
  const ordinal = data.ordinal;
  if (typeof sessionID !== 'string' || typeof messageID !== 'string' || typeof text !== 'string') return;
  if (!Number.isInteger(ordinal)) return;
  if (!state.managedSessions.has(sessionID)) return;
  let messages = state.assistantText.get(sessionID);
  if (!messages) {
    messages = new Map();
    state.assistantText.set(sessionID, messages);
  }
  let parts = messages.get(messageID);
  if (!parts) {
    parts = new Map();
    messages.set(messageID, parts);
    while (messages.size > 32) messages.delete(messages.keys().next().value);
  }
  parts.set(ordinal, text);
}

function takeAssistantText(state, sessionID, messageID) {
  const messages = state.assistantText.get(sessionID);
  if (!messages) return '';
  const parts = messages.get(messageID);
  messages.delete(messageID);
  if (messages.size === 0) state.assistantText.delete(sessionID);
  if (!parts) return '';
  return Array.from(parts.entries())
    .sort((left, right) => left[0] - right[0])
    .map((entry) => entry[1])
    .join('\n')
    .trim();
}

async function recordAssistantText(state, sessionID, messageID, promptID) {
  const text = takeAssistantText(state, sessionID, messageID);
  if (!text) return;
  const payload = hostPayload(state, {
    session_id: sessionID,
    response: text,
  });
  if (typeof promptID === 'string') payload.request_id = promptID;
  const result = await runOpencodeHost('response', payload, 9000);
  if (result.recorded) {
    debugLog(`assistant response recorded; acknowledged=${result.acknowledged === true}`);
  } else if (result.ambiguous) {
    debugLog('assistant response was not attributed: ambiguous delivery canary');
  }
}

async function flushStep(state, sessionID, messageID) {
  const mapped = state.stepPrompt.get(messageID);
  const promptID = (mapped && mapped.sessionID === sessionID ? mapped.promptID : undefined)
    || state.latestPrompt.get(sessionID);
  state.stepPrompt.delete(messageID);
  await recordAssistantText(state, sessionID, messageID, promptID);
}

async function flushSession(state, sessionID) {
  const messages = state.assistantText.get(sessionID);
  if (messages) {
    for (const messageID of Array.from(messages.keys())) {
      await flushStep(state, sessionID, messageID);
    }
  }
  for (const [messageID, mapped] of state.stepPrompt) {
    if (mapped.sessionID === sessionID) state.stepPrompt.delete(messageID);
  }
}

async function consumeV2Events(ctx, state, signal) {
  if (!ctx || !ctx.event || typeof ctx.event.subscribe !== 'function') return;
  const types = [
    'session.step.started',
    'session.step.ended',
    'session.step.failed',
    'session.text.ended',
    'session.execution.succeeded',
    'session.execution.failed',
    'session.execution.interrupted',
    'session.idle',
    'session.deleted',
  ];
  try {
    for await (const event of ctx.event.subscribe({ types, signal })) {
      if (!event || typeof event !== 'object') continue;
      const data = event.data || {};
      const sessionID = data.sessionID;
      if (typeof sessionID !== 'string') continue;
      if (event.type === 'session.deleted') {
        if (!state.managedSessions.delete(sessionID)) continue;
        state.assistantText.delete(sessionID);
        state.latestPrompt.delete(sessionID);
        for (const [messageID, mapped] of state.stepPrompt) {
          if (mapped.sessionID === sessionID) state.stepPrompt.delete(messageID);
        }
        void runOpencodeHost('cleanup', hostPayload(state, { session_id: sessionID }), 5000);
        continue;
      }
      if (!state.managedSessions.has(sessionID)) continue;
      if (event.type === 'session.text.ended') {
        bufferAssistantText(state, data);
      } else if (event.type === 'session.step.started') {
        const promptID = state.latestPrompt.get(sessionID);
        if (typeof data.assistantMessageID === 'string' && typeof promptID === 'string') {
          state.stepPrompt.set(data.assistantMessageID, { sessionID, promptID });
        }
      } else if (event.type === 'session.step.ended' || event.type === 'session.step.failed') {
        if (typeof data.assistantMessageID === 'string') {
          await flushStep(state, sessionID, data.assistantMessageID);
        }
      } else {
        await flushSession(state, sessionID);
      }
    }
  } catch (error) {
    if (!signal || !signal.aborted) {
      debugLog(`event stream stopped: ${error && error.message ? error.message : String(error)}`);
    }
  }
}

export async function setupV2(ctx) {
  const state = createHostState(
    ctx && ctx.location && ctx.location.directory,
    ctx && ctx.options,
  );
  const directory = state.directory;
  debugLog(`setup ${ctx && ctx.app ? ctx.app.version : 'unknown'} for ${directory}`);

  await ctx.session.hook('context', async (event) => {
    await injectV2Context(event, state);
  });

  await ctx.tool.hook('execute.before', async (event) => {
    guardToolV2(event);
    const toolName = String((event && event.tool) || '').toLowerCase();
    const input = event && event.input;
    if (toolName === 'rcoder_preflight' && input && typeof input.task === 'string' && input.task.trim()) {
      state.activeObjective = input.task.trim().slice(0, 4000);
    }
    if (toolName === 'read') {
      boundRead(input, directory);
    }
  });

  await ctx.tool.hook('execute.after', async (event) => {
    if (!event || event.status !== 'completed' || !event.result || typeof event.result !== 'object') {
      recordEditedFile(state.editedFiles, directory, event && event.tool, event && event.input);
      return;
    }
    recordEditedFile(state.editedFiles, directory, event.tool, event.input);
    try {
      if (typeof event.result.output === 'string') {
        event.result.output = optimizeText(event.result.output, directory);
      }
      if (typeof event.result.content === 'string') {
        event.result.content = optimizeText(event.result.content, directory);
      } else if (Array.isArray(event.result.content)) {
        event.result.content = event.result.content.map((item) => {
          if (item && item.type === 'text' && typeof item.text === 'string') {
            return { ...item, text: optimizeText(item.text, directory) };
          }
          return item;
        });
      }
    } catch (error) {
      console.error('RCoder output redaction/compaction skipped:', error && error.message ? error.message : String(error));
    }
  });

  await ctx.session.hook('compaction', async (event) => {
    if (!event || !Array.isArray(event.system)) return;
    appendSystemText(event.system, '## RCoder Active Session Capsule', sessionCapsule(directory, state.activeObjective, state.editedFiles));
  });

  const controller = new AbortController();
  void consumeV2Events(ctx, state, controller.signal);
  return () => controller.abort();
}

export const RCoderPlugin = async ({ directory }) => {
  const workspaceDirectory = normalizeDirectory(directory);
  const editedFiles = new Set();
  let activeObjective = '';

  return {
    'experimental.chat.system.transform': async (_input, output) => {
      if (!Array.isArray(output.system) || !existsSync(skillFile)) return;
      if (!output.system.some((item) => textOfSystemPart(item).startsWith('RCoder:'))) {
        output.system.push(`RCoder: The selected Agent Skill is at ${skillFile}. Read that exact file's routing instructions and only the relevant specialist reference. Use RCoder MCP tools when available; preserve project policy and verify changes with evidence.`);
      }
      if (output.system.some((item) => textOfSystemPart(item).startsWith('RScan:'))) return;
      try {
        const summary = await scanProject(workspaceDirectory);
        if (summary && !output.system.some((item) => textOfSystemPart(item).startsWith('RScan:'))) output.system.push(summary);
        const lessonsFile = path.join(workspaceDirectory, '.rcoder', 'lessons.jsonl');
        if (existsSync(lessonsFile)) {
          const count = readFileSync(lessonsFile, 'utf8').split(/\r?\n/).filter(Boolean).length;
          if (count > 0 && !output.system.some((item) => textOfSystemPart(item).startsWith('RCoder Memory:'))) {
            output.system.push(`RCoder Memory: ${count} verified episodic lesson(s) available via rcoder_recall.`);
          }
        }
      } catch (error) {
        console.error('RCoder RScan skipped:', error && error.message ? error.message : String(error));
      }
    },

    'tool.execute.before': async (input, output) => {
      await guardTool(input, output);
      const toolName = String(input?.tool || input?.toolName || '').toLowerCase();
      const args = output?.args || input?.args || {};

      if (toolName === 'rcoder_preflight' && typeof args.task === 'string' && args.task.trim()) {
        activeObjective = args.task.trim().slice(0, 4000);
      }

      if (toolName === 'read') {
        boundRead(args, workspaceDirectory);
        output.args = args;
      }
    },

    'tool.execute.after': async (input, output) => {
      const toolName = String(input?.tool || input?.toolName || '').toLowerCase();
      const args = input?.args || output?.args || {};
      recordEditedFile(editedFiles, workspaceDirectory, toolName, args);

      if (!existsSync(rsaverScript) || typeof output?.output !== 'string') return;
      try {
        output.output = optimizeText(output.output, workspaceDirectory);
      } catch (error) {
        console.error('RCoder output redaction/compaction skipped:', error && error.message ? error.message : String(error));
      }
    },

    'experimental.session.compacting': async (_input, output) => {
      const capsule = sessionCapsule(workspaceDirectory, activeObjective, editedFiles);
      if (!Array.isArray(output.context)) output.context = [];
      output.context.push(capsule);
    },
  };
};

/** Exposed for deterministic host-state regression tests; not used by OpenCode. */
export const hostStateContract = Object.freeze({
  createHostState,
  setupOptions,
  hostPayload,
  normalizeDirectory,
});

const v2Plugin = {
  id: 'rcoder',
  setup: setupV2,
};

export default {
  ...v2Plugin,
  async server(options) {
    return RCoderPlugin(options);
  },
};
