import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const pluginDirectory = path.dirname(fileURLToPath(import.meta.url));
const skillDirectory = path.resolve(pluginDirectory, '..', 'skills', 'rcoder');
const skillFile = path.join(skillDirectory, 'SKILL.md');
const rscan = path.join(skillDirectory, 'scripts', 'rscan.py');
const pythonCandidates = process.env.RCODER_PYTHON ? [process.env.RCODER_PYTHON] : (process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python']);

async function scanProject(directory) {
  let lastError;
  for (const python of pythonCandidates) {
    const prefix = python === 'py' ? ['-3'] : [];
    try {
      const result = await execFileAsync(python, [...prefix, rscan, 'scan', '--root', directory, '--hook', 'opencode'],
        { timeout: 12000, maxBuffer: 2000000, encoding: 'utf8', windowsHide: true });
      return result.stdout.trimEnd();
    } catch (error) {
      lastError = error;
      if (error.code !== 'ENOENT') throw error;
    }
  }
  throw lastError || new Error('Python 3 was not found');
}

export const RCoderPlugin = async ({ directory }) => ({
  'experimental.chat.system.transform': async (_input, output) => {
    if (!Array.isArray(output.system) || !existsSync(skillFile)) return;
    const textOf = (item) => typeof item === 'string' ? item : (item && item.text) || '';
    if (!output.system.some((item) => textOf(item).startsWith('RCoder:'))) {
      output.system.push('RCoder: The project includes the RCoder Agent Skill at .opencode/skills/rcoder/SKILL.md. Read its routing instructions and only the relevant specialist reference. Use RCoder MCP tools when available; preserve project policy and verify changes with evidence.');
    }
    if (output.system.some((item) => textOf(item).startsWith('RScan:'))) return;
    try {
      const summary = await scanProject(directory);
      if (summary && !output.system.some((item) => textOf(item).startsWith('RScan:'))) output.system.push(summary);
    } catch (error) {
      console.error('RCoder RScan skipped:', error && error.message ? error.message : String(error));
    }
  }
});
