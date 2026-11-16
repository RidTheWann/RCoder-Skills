# RCoder — portable engineering skill

**RCoder** is a model-agnostic Agent Skill for software engineering agents. It routes work to focused expert modules, uses a read-only stack detector, and ships offline installers, static evaluations, and plugin adapters.

## English: quick start (60 seconds)

Clone/download this repository, then run one command from its root:

```sh
bash scripts/install.sh --target agents --scope project
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Target agents -Scope project
```

Reload/start your coding agent and ask:

> Trace the failing API test, identify the root cause, add a regression test, make the smallest correct fix, run the relevant checks, and report exact evidence.

### One-command installation by target

Run from the repository root. Replace `project` with `user` for a home-directory install. PowerShell commands use the common prefix `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1` followed by the listed parameters.

| Target | POSIX command | PowerShell parameters |
|---|---|---|
| Claude Code | `bash scripts/install.sh --target claude-code --scope project` | `-Target claude-code -Scope project` |
| Codex | `bash scripts/install.sh --target codex --scope project` | `-Target codex -Scope project` |
| Cursor | `bash scripts/install.sh --target cursor --scope project` | `-Target cursor -Scope project` |
| Gemini CLI | `bash scripts/install.sh --target gemini-cli --scope project` | `-Target gemini-cli -Scope project` |
| GitHub Copilot | `bash scripts/install.sh --target copilot --scope project` | `-Target copilot -Scope project` |
| Agent Skills alias | `bash scripts/install.sh --target agents --scope project` | `-Target agents -Scope project` |

The installer supports `--dry-run` / `-DryRun`, `--uninstall` / `-Uninstall`, and explicit `--project-dir` / `-ProjectDir` or `--home-dir` / `-HomeDir`. It copies the bundled skill only; it does not install product CLIs, modify tool settings, or use the network. Windows PowerShell installer simulations are included in the GitHub Actions Windows job.

### Native entry points

- **Claude Code:** install to `.claude/skills/rcoder`; this repo also includes `.claude-plugin/plugin.json` and a marketplace manifest. Validate with `claude plugin validate . --strict`; add it with `claude plugin marketplace add RidTheWann/RCoder-Skills`, then install with `claude plugin install rcoder@rcoder-skills`. Load locally with `claude --plugin-dir .`.
- **Codex:** install to `.agents/skills/rcoder`; `agents/openai.yaml` is optional UI metadata. The root `plugin.json` is the portable Agent Plugins manifest; `.codex-plugin/plugin.json` remains a compatibility fallback for older Codex packaging.
- **Cursor:** install to `.cursor/skills/rcoder`; Cursor also discovers `.agents/skills/`.
- **Gemini CLI:** install to `.gemini/skills/rcoder`; `.agents/skills/` is also a documented alias.
- **Copilot:** install to `.github/skills/rcoder`; the user-level path is `~/.copilot/skills/`.
- **Other Agent Skills clients:** install to `.agents/skills/rcoder` or `~/.agents/skills/rcoder`.

### Example prompts

**English**
- “Audit this Rust workspace for correctness and security risks. Fix only confirmed defects and run the relevant checks.”
- “Compare two API migration designs, record an ADR, and implement the first safe slice.”

**Bahasa Indonesia**
- “Perbaiki bug ini berdasarkan reproduksi dan bukti. Tambahkan regression test, jalankan test terkait, lalu laporkan hasil aktual.”
- “Audit tampilan pengaturan dari sisi alur, state kosong/loading/error/sukses, responsivitas, dan WCAG 2.2 AA.”

### Extend and maintain

Copy `skills/rcoder/assets/templates/expert-module-template.md` into `skills/rcoder/references/`, write domain-specific decision rules and verification steps, keep it ≤300 lines, and add a routing signal to `skills/rcoder/SKILL.md`. Project-only expertise belongs in `.rcoder/`. Recheck `docs/research-log.md` and official tool docs when a product changes its discovery path or manifest. Record changes in `docs/DECISIONS.md`; synchronize SemVer across manifests and `CHANGELOG.md`.

### Development checks

```sh
python3 scripts/validate-all
bash scripts/test-installers.sh
python3 scripts/package
```

All development scripts use the Python standard library or native shell utilities. The installer itself has no external runtime dependency.

## Bahasa Indonesia

RCoder adalah *project skill* portabel dan model-agnostic untuk agen engineering. Satu router inti memilih modul ahli sesuai pekerjaan: coding, arsitektur, UI/UX, debugging, QA, keamanan, performa, DevOps, data/API, review, dan dokumentasi. Referensi dimuat seperlunya agar konteks tetap efisien.

### Mulai cepat

Dari root repo jalankan:

```sh
bash scripts/install.sh --target agents --scope project
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Target agents -Scope project
```

Untuk instalasi personal, gunakan `--scope user`. Installer mendukung dry-run, backup sebelum penggantian, instalasi idempoten, dan uninstall yang memulihkan backup sebelumnya bila tersedia.

### Batas verifikasi

Lingkungan build tersedia Linux x86-64, Python 3.13, Node 22, dan Git 2.47. PowerShell lokal serta CLI/runtime produk tidak terpasang, tetapi simulasi installer POSIX dan PowerShell berjalan pada runner Linux/Windows GitHub Actions. `skills-ref` dan aktivasi model live masih belum diverifikasi langsung. Status setiap gerbang ada di `docs/HANDOFF.md`.
