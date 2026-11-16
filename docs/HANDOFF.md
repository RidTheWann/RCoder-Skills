# RCoder handoff / serah-terima

## English

### Delivered
`skills/rcoder/` is the canonical portable Agent Skill. It contains the router, twelve core engineering experts plus a domain-extension guide, read-only stack detection, six authoring templates, and optional OpenAI UI metadata. The repository includes POSIX/PowerShell installers, Claude and Codex plugin adapters, 24 trigger prompts, 10 behavioral scenarios, static validation, Linux/Windows CI, and a reproducible ZIP builder.

**GitHub publication: VERIFIED.** The GitHub connector created and read back the source files on `main`. The verified tree contains 59 files, including all 13 reference modules, six templates, ten scenario files, installers, tests, docs, manifests, and CI. See commit history: https://github.com/RidTheWann/RCoder-Skills/commits/main.

Generated ZIP files and `SHA256SUMS` are build artifacts and are intentionally not tracked in Git; generate them locally with `python3 scripts/package`. They were built and checksum-verified in the original Linux workspace.

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
Codex native discovery uses `.agents/skills/` or `~/.agents/skills/`; `agents/openai.yaml` supplies optional UI metadata. `.codex-plugin/plugin.json` is a compatibility adapter, not proof of native plugin support. Run `python3 scripts/package` to create:
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
| G1 | VERIFIED (static) | Custom stdlib validator passed 226 local checks; official `skills-ref` not installed. |
| G2 | VERIFIED (dataset only) | 24 prompts / 12 positive / 12 negative; live model trigger not verified. |
| G3 | VERIFIED (scenario design) | 10 objective scenarios with separate files; live with/without-skill comparison not verified. |
| G4 | VERIFIED (POSIX simulation) | 12 target/scope combinations in Linux; PowerShell and native discovery not verified. |
| G5 | VERIFIED (static scope) | Selected secret/risky-command checks and MIT; not a complete security audit. |
| G6 | VERIFIED (static) | Bilingual docs, quick start, target install, extension/maintenance steps. |
| G7 | VERIFIED (local static + remote tree) | 226 checks locally; GitHub readback confirms 59 expected source files. |

### Limitations
Build environment: Linux x86-64, Python 3.13, Node 22, Git 2.47; no PowerShell, `skills-ref`, Claude/Codex/Cursor/Gemini/Copilot CLI, or model runtime. GitHub Actions workflow has been committed, but a completed remote runner result must be checked in the Actions tab. Stack detection is heuristic. See `docs/RESEARCH-TODO.md`.

## Bahasa Indonesia

RCoder adalah skill engineering portabel dengan router inti, 12 modul ahli utama + panduan ekstensi domain, stack detector read-only, enam template, installer shell/PowerShell, adapter Claude/Codex, 24 prompt pemicu, 10 skenario perilaku, validator statis, CI Linux/Windows, dan pembuat paket ZIP.

**Publikasi GitHub: VERIFIED.** File source berhasil ditulis dan dibaca ulang dari branch `main`. Tree remote berisi 59 file: seluruh 13 modul referensi, enam template, sepuluh skenario, installer, test harness, dokumentasi, manifest, serta workflow CI. [Lihat repository](https://github.com/RidTheWann/RCoder-Skills).

**Instalasi tercepat:** dari root repo jalankan `bash scripts/install.sh --target agents --scope project`. Untuk instalasi personal gunakan `--scope user`. Target lain: `claude-code`, `codex`, `cursor`, `gemini-cli`, dan `copilot`.

**Status gerbang:** G1 VERIFIED statis (226 pemeriksaan lokal); G2 dataset saja; G3 desain/rubrik skenario; G4 POSIX 12 kombinasi; G5 scan terbatas + lisensi MIT; G6–G7 dokumentasi dan konsistensi lokal plus readback 59 file remote. Belum diverifikasi live: `skills-ref`, PowerShell runtime, discovery enam aplikasi, Claude marketplace install, Codex plugin runtime, import ZIP UI, ablation model dengan/tanpa RCoder, dan hasil workflow runner GitHub.

**Paket ZIP:** arsip ZIP dan checksum dibuat secara lokal oleh `python3 scripts/package`, diverifikasi checksum-nya, dan tidak dimasukkan ke Git agar repo tetap berisi source. Jalankan perintah tersebut setelah clone untuk membangunnya kembali.
