# RScan: automatic project reconnaissance and option offering

## Activate when
A skill has just been installed, a session starts in a new or unfamiliar repository, the user asks "what should I work on?", or no specialist has been selected yet. Do not activate for a single-file task with a known edit point, or as a substitute for verification.

## Mission and expertise
Produce a bounded, read-only map of the project and offer a short ranked menu of development options with concrete first commands and specialist references. Own the evidence ledger for those options; do not claim that a host invoked RScan automatically unless the hook output was observed.

## Mental model
An IDE launch does not by itself run a skill file. Automatic scanning requires a host session-start feature. RScan separates the portable scan engine from host adapters: `scan` is deterministic and read-only, while `hooks install` is an explicit, backed-up configuration change. Offered options are hypotheses from evidence, not decisions made on the user's behalf.

## Prerequisites and reconnaissance
1. Determine the host and whether it has a documented session-start hook. See `docs/RSCAN-HOOKS.md` for the evidence table.
2. If auto-scan is desired on a supported host, run `rscan hooks preview`, then `rscan hooks install --host <id> --scope project|user`.
3. Confirm the scan output appears in the first session; if not, invoke `rscan scan` manually.
4. Treat scan findings as bounded evidence: the path sample may be truncated.

## Procedure
1. Run `python3 <skill-dir>/scripts/rscan.py scan --root <project-root> --format json` for machine-readable output, or `--format text` for a menu.
2. Review risk signals and stacks; open only the key files needed to confirm the top option.
3. Present the ranked options with their IDs and first commands. Ask the user which option to pursue when the choice is consequential; otherwise choose the smallest sufficient one.
4. Load only the specialists listed for the chosen option.
5. Feed the chosen context into `rsaver gate` when the task will be multi-step or tool-heavy.
6. Record the scan root, sampled path count, truncation status, and selected option in the working ledger.

## Decision tree
- Supported host with verified session hook → install the hook once; let the scan result enter context at startup.
- Unsupported or unverified host → invoke the scan manually at session start; do not generate an untested adapter.
- Clean tree, CI, and build metadata → offer release or incremental improvement, not a rewrite.
- Uncommitted changes → finish and verify the current change first.
- Manifest without lockfile → dependency provenance review before feature work.
- Missing README/agent instructions and no CI → onboarding and quality gates outrank feature work.
- Binary artifacts present → authorized reverse-engineering workflow with provenance.
- Security-sensitive paths present → defensive security review, never offensive action.

## Tool strategy
The canonical CLI is `<skill-dir>/scripts/rscan.py` (bundled with the installed skill; prefer the `rcoder_scan` MCP tool when available); `scripts/rscan.py` is a repository-root wrapper. It uses only the Python standard library and Git when available. `scan` supports `text`, `json`, `markdown`, and host payload modes. `hooks` supports `preview` and `install` for Claude Code and Gemini CLI only.

## Advanced techniques
- **Hook idempotence:** the installer detects an existing RScan command and leaves settings untouched on repeat runs.
- **Backup discipline:** every settings change creates a timestamped backup before replacement.
- **Bounded evidence:** the scan samples paths, records truncation, and reads text only for line counts.
- **Option ranking:** options carry a priority score and the risk IDs that triggered them, so the user can audit why an option was offered.
- **Gate handoff:** option commands and specialists can be converted into an RSaver envelope for input/cache/output budgeting.

## Failure modes
- **Assuming auto-run from file installation alone** → no menu appears → install a verified hook or invoke manually.
- **Generated adapter for an unverified host** → broken configuration → restrict installers to evidenced hosts.
- **Unbounded scan** → context blowup → keep `--max-paths` bounded and record truncation.
- **Treating an option as a decision** → unwanted work → present ranked options and confirm consequential choices.
- **Hook installed in an untrusted project** → arbitrary code execution risk → install only where the project is trusted.

## Quality checklist
- [ ] Scan is read-only, bounded, and reports truncation.
- [ ] Stacks, quality entry points, and risk signals are evidenced by sampled paths.
- [ ] Offered options include first commands and specialist references.
- [ ] Hook installation is explicit, backed up, idempotent, and limited to verified hosts.
- [ ] No automatic invocation is claimed without observed hook output.

## Anti-patterns
Auto-generating hooks for every host; reading whole repositories into context; presenting options without evidence; modifying host settings without a backup; treating a missing menu as proof the project is empty.

## Verification
Run `python3 scripts/test-rscan.py`, which checks bounded scanning, risk signals, option ranking, both hook payload formats, preview, idempotent installation, and preservation of existing hooks. After installing a hook on a real host, confirm the menu appears in a fresh session and record the host version.

## Output format
Scan root · sampled paths and truncation · stacks · quality entry points · risk signals with severity · ranked options with IDs/commands/specialists · hook status · residual uncertainty.
