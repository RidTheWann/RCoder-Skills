import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, '.opencode', 'plugins', 'rcoder.js');
const testModule = path.join(root, '.opencode', 'plugins', `.rcoder-lifecycle-test-${process.pid}.mjs`);
const workspace = mkdtempSync(path.join(os.tmpdir(), 'rcoder-opencode-'));
try {
  writeFileSync(testModule, readFileSync(source, 'utf8'), 'utf8');
  const { RCoderPlugin } = await import(pathToFileURL(testModule).href);
  const hooks = await RCoderPlugin({ directory: workspace });

  await hooks['tool.execute.before'](
    { tool: 'rcoder_preflight' },
    { args: { task: 'Harden the parser and verify regression tests' } },
  );
  writeFileSync(path.join(workspace, 'large.txt'), 'line\n'.repeat(9000), 'utf8');
  const readOutput = { args: { filePath: 'large.txt' } };
  await hooks['tool.execute.before']({ tool: 'read' }, readOutput);
  assert.equal(readOutput.args.limit, 160, 'large reads must be bounded');

  mkdirSync(path.join(workspace, 'src'));
  const afterOutput = { output: 'api_key=ABCDEFGHIJKLMNOPQRSTUVWX' };
  await hooks['tool.execute.after'](
    { tool: 'edit', args: { filePath: 'src/parser.js' } },
    afterOutput,
  );
  assert.doesNotMatch(afterOutput.output, /ABCDEFGHIJKLMNOPQRSTUVWX/);
  const compacting = { context: [] };
  await hooks['experimental.session.compacting']({}, compacting);
  const capsule = compacting.context.join('\n');
  assert.match(capsule, /Harden the parser and verify regression tests/);
  assert.match(capsule, /src\/parser\.js/);
  assert.match(capsule, /SHA-256: [a-f0-9]{64}/);
  assert.doesNotMatch(capsule, /ABCDEFGHIJKLMNOPQRSTUVWX/);
  console.log('OpenCode lifecycle middleware: guard, ledger, redaction and capsule passed');
} finally {
  rmSync(testModule, { force: true });
  rmSync(workspace, { recursive: true, force: true });
}
