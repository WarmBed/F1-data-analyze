# Release Checklist

This checklist defines the minimum gate before publishing PitWall as a public repository.

## Required State

- License is MIT.
- Default runtime is local-first for validated GUI workflows.
- No Cloudflare tunnel credentials, certificates, private hostnames, FastF1 cache databases, live timing dumps, packaged executables, or generated JSON reports are tracked.
- No real API keys are present in source or Git history.
- Generated screenshots, cache files, logs, virtual environments, and build outputs remain ignored.

## Verified Commands

Use PowerShell from the repository root:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:F1T_RUNTIME_MODE = "local"
$env:PYTHONIOENCODING = "utf-8"

venv_build\Scripts\python.exe tools\run_gui_coverage_matrix.py `
  --year 2026 --race Miami --session R `
  --scope non-live --timeout 4 `
  --report logs\gui_coverage_non_live_2026_miami_release.json

venv_build\Scripts\python.exe tools\run_direct_gui_validation.py `
  --year 2026 --race Miami --session R `
  --report logs\direct_gui_validation_2026_miami_release.json `
  --screenshot logs\direct_gui_validation_2026_miami_release.png

venv_build\Scripts\python.exe tools\run_live_timing_data_validation.py `
  --year 2026 --race Miami --session R `
  --report logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix.json `
  --screenshot logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix.png `
  --screenshot-dir logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix

venv_build\Scripts\python.exe tools\run_gui_coverage_matrix.py `
  --year 2026 --race Miami --session R `
  --scope matrix `
  --report logs\gui_coverage_matrix_2026_miami_release.json
```

Current verified target:

- Historical non-live function tree: 42/42 modules load real 2026 Miami race data.
- Historical/direct GUI smoke: 10/10 modules load real 2026 Miami race data.
- Live timing: 28/28 modules load 2026 Miami race replay data with numeric or semantic evidence.
- Combined matrix: 70/70 function-tree leaves have e2e evidence.

## Evidence Files

These files are generated locally and must not be committed:

- `logs/direct_gui_validation_2026_miami_release.json`
- `logs/direct_gui_validation_2026_miami_release.png`
- `logs/gui_coverage_non_live_2026_miami_release.json`
- `logs/gui_coverage_matrix_2026_miami_release.json`
- `logs/live_timing_data_validation_2026_miami_strict_numeric_after_fix.json`
- `logs/live_timing_data_validation_2026_miami_strict_numeric_after_fix.png`
- `logs/live_timing_data_validation_2026_miami_strict_numeric_after_fix/`

## Security Scans

Run before publishing:

```powershell
git ls-files | rg -i "(^|/)(cloudflared|cache|f1_analysis_cache|fastf1_cache|data/live_timing_cache|logs|json)/|\.(pem|key|crt|sqlite|db|pkl|ff1pkl|exe|dll)$|cert\.pem|fastf1_http_cache"

git rev-list --all --objects | rg -i "cloudflared|cert\.pem|fastf1_http_cache|\.sqlite|\.pkl|\.ff1pkl|\.exe|\.pem|\.key"

rg -n "AIza|github_pat_|ghp_|glpat-|xox[baprs]-|BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY" -S `
  --glob '!venv_build/**' --glob '!cache/**' --glob '!f1_analysis_cache/**' `
  --glob '!fastf1_cache/**' --glob '!logs/**' --glob '!json/**' `
  --glob '!data/live_timing_cache/**' .
```

Any previously exposed credential must be rotated with the provider even after Git history cleanup.

## Known Release Caveats

- `docs/OLD/` contains historical design notes with placeholder API-key examples. They are not real credentials, but public secret scanners may still flag them.
- Some legacy GUI/demo modules still contain API-only comments or optional local API client code. Validated release workflows run in local mode without starting an API server.
- `data/live_timing_cache/` is required for local replay validation but is intentionally ignored and must be regenerated locally.
