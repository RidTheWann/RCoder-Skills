import { createHash } from 'node:crypto';
import { existsSync, readFileSync, realpathSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile, spawnSync } from 'node:child_process';
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
const pythonCandidates = process.env.RCODER_PYTHON ? [process.env.RCODER_PYTHON] : (process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python']);
const COMPRESS_THRESHOLD_CHARS = 4000;
const MAX_RAW_READ_BYTES = 25 * 1024;
const MAX_RAW_READ_LINES = 160;

async function runPython(script, args, timeout) {
  let lastError;
  for (const python of pythonCandidates) {
    const prefix = python === 'py' ? ['-3'] : [];
    try {
      const result = await execFileAsync(python, [...prefix, script, ...args], {
        timeout,
        maxBuffer: 4000000,
        encoding: 'utf8',
        windowsHide: true,
      });
      return result.stdout;
    } catch (error) {
      lastError = error;
      if (error.code !== 'ENOENT') throw error;
    }
  }
  throw lastError || new Error('Python 3 was not found');
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

async function guardTool(input, output) {
  if (!existsSync(hooksScript)) return;
  const payload = JSON.stringify({
    hook_event_name: 'PreToolUse',
    tool_name: input.tool || input.toolName || 'unknown',
    tool_input: output.args || {},
  });
  let raw;
  try {
    raw = runPythonSync(hooksScript, ['guard'], payload, 5000);
  } catch (error) {
    console.error('RCoder guard skipped:', error && error.message ? error.message : String(error));
    return;
  }
  if (!raw || !raw.trim()) return;
  let decision;
  try {
    decision = JSON.parse(raw).hookSpecificOutput;
  } catch {
    return;
  }
  if (decision && decision.permissionDecision === 'deny') {
    throw new Error(`RCoder Guard blocked unsafe tool execution: ${decision.permissionDecisionReason || 'denied'}`);
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

export const RCoderPlugin = async ({ directory }) => {
  const workspaceDirectory = path.resolve(directory || repoRoot);
  const editedFiles = new Set();
  let activeObjective = '';

  return {
    'experimental.chat.system.transform': async (_input, output) => {
      if (!Array.isArray(output.system) || !existsSync(skillFile)) return;
      const textOf = (item) => typeof item === 'string' ? item : (item && item.text) || '';
      if (!output.system.some((item) => textOf(item).startsWith('RCoder:'))) {
        output.system.push(`RCoder: The selected Agent Skill is at ${skillFile}. Read that exact file's routing instructions and only the relevant specialist reference. Use RCoder MCP tools when available; preserve project policy and verify changes with evidence.`);
      }
      if (output.system.some((item) => textOf(item).startsWith('RScan:'))) return;
      try {
        const summary = await scanProject(workspaceDirectory);
        if (summary && !output.system.some((item) => textOf(item).startsWith('RScan:'))) output.system.push(summary);
        const lessonsFile = path.join(workspaceDirectory, '.rcoder', 'lessons.jsonl');
        if (existsSync(lessonsFile)) {
          const count = readFileSync(lessonsFile, 'utf8').split(/\\r?\\n/).filter(Boolean).length;
          if (count > 0 && !output.system.some((item) => textOf(item).startsWith('RCoder Memory:'))) {
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
        const requested = args.filePath || args.file_path || args.path;
        if (typeof requested === 'string' && requested.trim()) {
          const candidate = path.resolve(workspaceDirectory, requested);
          const relative = path.relative(workspaceDirectory, candidate);
          if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
            throw new Error('[RCoder Guard] Read path escapes the active workspace.');
          }
          if (existsSync(candidate)) {
            const realRoot = realpathSync(workspaceDirectory);
            const realTarget = realpathSync(candidate);
            const realRelative = path.relative(realRoot, realTarget);
            if (realRelative === '..' || realRelative.startsWith(`..${path.sep}`) || path.isAbsolute(realRelative)) {
              throw new Error('[RCoder Guard] Read symlink escapes the active workspace.');
            }
            const stat = statSync(realTarget);
            if (stat.isFile() && stat.size > MAX_RAW_READ_BYTES && !args.offset && !args.limit) {
              args.limit = MAX_RAW_READ_LINES;
              output.args = args;
            }
          }
        }
      }
    },

    'tool.execute.after': async (input, output) => {
      const toolName = String(input?.tool || input?.toolName || '').toLowerCase();
      const args = input?.args || output?.args || {};
      const requested = args.filePath || args.file_path || args.path;
      if (['edit', 'write', 'multiedit', 'create'].includes(toolName) && typeof requested === 'string') {
        const absolute = path.resolve(workspaceDirectory, requested);
        const relative = path.relative(workspaceDirectory, absolute);
        if (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative)) {
          editedFiles.add(relative.split(path.sep).join('/'));
        }
      }

      if (!existsSync(rsaverScript) || typeof output?.output !== 'string') return;
      try {
        const redacted = runPythonSync(rsaverScript, ['redact', '-', '--profile', 'generic'], output.output, 8000).trimEnd();
        if (redacted.length >= COMPRESS_THRESHOLD_CHARS) {
          const packed = compactOutput(redacted);
          if (packed && packed.length < redacted.length) {
            const savedPct = Math.round((1 - packed.length / redacted.length) * 100);
            output.output = `[rcoder:rsaver saved ${savedPct}%]\\n${packed}`;
          } else {
            output.output = redacted;
          }
        } else {
          output.output = redacted;
        }
      } catch (error) {
        console.error('RCoder output redaction/compaction skipped:', error && error.message ? error.message : String(error));
      }
    },

    'experimental.session.compacting': async (_input, output) => {
      const state = {
        schema: 'rcoder-session-capsule-v1',
        workspace: path.basename(workspaceDirectory),
        objective: activeObjective || 'Not captured; recover latest user objective from the conversation.',
        modified_files: Array.from(editedFiles).sort(),
        invariant: 'Inspect the final diff and run rcoder_impact_test plus the narrowest relevant verification before claiming completion.',
      };
      let serialized = JSON.stringify(state);
      if (existsSync(rsaverScript)) {
        try {
          serialized = runPythonSync(rsaverScript, ['redact', '-', '--profile', 'generic'], serialized, 8000).trim();
        } catch (error) {
          console.error('RCoder capsule redaction skipped:', error && error.message ? error.message : String(error));
        }
      }
      const digest = createHash('sha256').update(serialized, 'utf8').digest('hex');
      const capsule = [
        '## RCoder Active Session Capsule',
        `- SHA-256: ${digest}`,
        `- Workspace: ${path.basename(workspaceDirectory)}`,
        `- State (secret-redacted JSON): ${serialized}`,
        '- Before stopping: inspect the final diff, run the narrowest relevant tests, and record verified evidence. This capsule is not proof that checks passed.',
      ].join('\\n');
      if (!Array.isArray(output.context)) output.context = [];
      output.context.push(capsule);
    },
  };
};

export default RCoderPlugin;
