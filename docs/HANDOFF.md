# RCoder handoff / serah-terima

## English

### Delivered
`skills/rcoder/` is the canonical portable Agent Skill. It contains the router, twelve core experts, read-only stack detection, templates, and optional OpenAI UI metadata. The repository adds POSIX/PowerShell installers, Claude and Codex plugin adapters, 24 trigger prompts, 10 behavioral scenarios, static validation, CI, and reproducible ZIP build scripts. GitHub target: https://github.com/RidTheWann/RCoder-Skills. Remote publication is now **VERIFIED** through the GitHub connector: multiple commits exist on `main`; read the remote tree before treating every path as published.

### Fastest install
```sh
bash scripts/install.sh --target agents --scope project
bash scripts/install.sh --target agents --scope user
```
Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Target agents -Scope project
```

### Native target commands (POSIX, project scope)
```sh
bash scripts/install.sh --target claude-code --scope project
bash scripts/install.sh --target codex --scope project
bash scripts/install.sh --target cursor --scope project
bash scripts/install.sh --target gemini-cli --scope project
bash scripts/install.sh --target copilot --scope project
bash scripts/install.sh --target agents --scope project
```
Replace scope with `user` for home install. Installer has `--dry-run`, `--uninstall`, and explicit path overrides. It backs up existing RCoder before replacement; uninstall preserves active files and restores the latest pre-install backup when available. Identical install is a no-op.

### Claude plugin commands
```sh
claude plugin validate . --strict
claude --plugin-dir .
claude plugin marketplace add https://github.com/RidTheWann/RCoder-Skills
claude plugin install rcoder@rcoder-skills
claude plugin list
```
Marketplace flow is documented but native CLI installation remains NOT VERIFIED. Native `.claude/skills` install is the fallback.

### Codex adapter and packages
Codex native discovery uses `.agents/skills/` or `~/.agents/skills/`; `agents/openai.yaml` supplies optional UI metadata. `.codex-plugin/plugin.json` is a compatibility adapter only. Run `python3 scripts/package` to create:
- `dist/rcoder-v1.0.0.skill.zip`
- `dist/rcoder-v1.0.0.claude-plugin.zip`
- `dist/rcoder-v1.0.0.codex-plugin.zip`
- `dist/rcoder-v1.0.0-source.zip`
- `dist/SHA256SUMS`

### Extend and maintain
Copy `skills/rcoder/assets/templates/expert-module-template.md` to `skills/rcoder/references/`, keep modules ≤300 lines, add a router signal and evaluation case, then run:
```sh
python3 scripts/validate-all
bash scripts/test-installers.sh
python3 scripts/package
```
When a host changes its path/manifest, update both installer scripts, target tests, README, installation matrix, research log, and decisions. Synchronize SemVer across `CHANGELOG.md`, plugin manifests, and `scripts/package`.

### Gate status
| Gate | Status | Meaning |
|---|---|---|
| G1 | VERIFIED (static) | Custom stdlib validator; `skills-ref` not installed. |
| G2 | VERIFIED (dataset only) | 24 prompts / 12 positive / 12 negative; live model trigger not verified. |
| G3 | VERIFIED (scenario design) | 10 objective scenarios; live with/without-skill comparison not verified. |
| G4 | VERIFIED (POSIX simulation) | 12 target/scope combinations in Linux; PowerShell and native discovery not verified. |
| G5 | VERIFIED (static) | Selected secret/risky-command checks and MIT; not a complete security audit. |
| G6 | VERIFIED (static) | Bilingual docs, quick start, target install, extension/maintenance steps. |
| G7 | VERIFIED (static) | Local source tree passed links, JSON, line limits, and required docs; remote path coverage still being read back. |

### Limitations
Build environment: Linux x86-64, Python 3.13, Node 22, Git 2.47; no PowerShell, `skills-ref`, Claude/Codex/Cursor/Gemini/Copilot CLI, or model runtime. Stack detection is heuristic. See `docs/RESEARCH-TODO.md`.

## Bahasa Indonesia

RCoder adalah skill engineering portabel dengan router inti, 12 modul ahli, stack detector read-only, enam template, installer shell/PowerShell, adapter Claude/Codex, 24 prompt pemicu, 10 skenario perilaku, validator statis, CI, dan skrip paket ZIP. Repo tujuan: https://github.com/RidTheWann/RCoder-Skills. Commit sudah masuk ke `main` melalui konektor GitHub; daftar path lengkap perlu dicek ulang dari tree remote.

**Instalasi tercepat:** dari root repo jalankan `bash scripts/install.sh --target agents --scope project`. Untuk instalasi personal gunakan `--scope user`. Target lain: `claude-code`, `codex`, `cursor`, `gemini-cli`, dan `copilot`.

**Status gerbang:** G1 VERIFIED statis; G2 dataset saja; G3 desain/rubrik skenario; G4 POSIX 12 kombinasi; G5 scan terbatas + lisensi MIT; G6–G7 pemeriksaan statis lokal. Belum diverifikasi live: `skills-ref`, PowerShell runtime, discovery enam aplikasi, Claude marketplace install, Codex plugin runtime, import ZIP UI, dan ablation model dengan/tanpa RCoder.

**Penting:** publikasi remote sudah dimulai dan commit dapat dibaca di GitHub, tetapi jangan menyebut seluruh source terunggah sebelum tree `main` dan daftar file yang diperlukan selesai diverifikasi.
