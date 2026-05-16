# PitWall

PitWall is a Python application for Formula 1 telemetry analysis, race-session exploration, prediction experiments, and desktop visualization.

The project focuses on local analysis workflows built around FastF1, live timing captures, race reports, and custom GUI modules. Public releases of this repository intentionally exclude raw telemetry caches, live timing dumps, team radio audio, generated reports, packaged executables, private tunnel configuration, and local workspace databases.

## Features

- Historical race and session analysis
- Lap time, sector, speed, throttle, brake, RPM, gear, and DRS visualization
- Driver comparison tools
- Track, pit stop, tire strategy, traffic, and incident analysis modules
- Desktop GUI based on PyQt5
- Optional FastAPI service modules for local data access
- Prediction and model experimentation utilities

## Repository Policy

This repository contains source code and documentation only.

The following content is deliberately not tracked:

- FastF1 HTTP caches and pickled telemetry files
- Live timing raw recordings and generated JSON exports
- Team radio audio and parsed stream dumps
- Cloudflare tunnel credentials and local networking configuration
- Virtual environments and build environments
- Packaged executables, build folders, and release archives
- Generated reports, PDFs, profiling outputs, and local workspace databases

If you need those assets for local work, generate or download them outside Git using your own credentials and data access rights.

## Requirements

- Python 3.13.x
- Windows is the primary development target
- FastF1-compatible data access
- Optional: PyQt5 desktop runtime

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development tools:

```powershell
pip install -r requirements-dev.txt
```

## Running

Desktop GUI:

```powershell
$env:F1T_RUNTIME_MODE = "local"
python f1t_gui_main.py
```

Alternative modular entry point:

```powershell
python f1_analysis_modular_main.py
```

The GUI release path is local-first. It must not require a separately running REST API server for the validated historical and live timing workflows. Some analysis modules generate or read local cache/data folders; those outputs are ignored by Git and must not be committed.

## Release Verification

The current release gate uses real 2026 Miami race data because it has complete local historical replay coverage in this workspace:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:F1T_RUNTIME_MODE = "local"
$env:PYTHONIOENCODING = "utf-8"

venv_build\Scripts\python.exe tools\run_direct_gui_validation.py `
  --year 2026 --race Miami --session R `
  --report logs\direct_gui_validation_2026_miami_release.json `
  --screenshot logs\direct_gui_validation_2026_miami_release.png

venv_build\Scripts\python.exe tools\run_live_timing_data_validation.py `
  --year 2026 --race Miami --session R `
  --report logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix.json `
  --screenshot logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix.png `
  --screenshot-dir logs\live_timing_data_validation_2026_miami_strict_numeric_after_fix
```

Expected validated coverage:

- Historical/direct GUI modules: 10/10
- Live timing modules: 28/28 with strict numeric or semantic data evidence
- Generated screenshots and JSON reports stay under `logs/` and are ignored by Git

## Data And Legal Notes

PitWall is an unofficial project and is not associated with Formula 1, FIA, FastF1, or any race team.

Users are responsible for complying with the terms of the data sources they use. Do not commit or redistribute proprietary, licensed, credentialed, or personally sensitive data through this repository.

## Security

Never commit:

- API keys, tunnel credentials, certificates, tokens, or `.env` files
- Local absolute credential paths
- Private hostnames or infrastructure configuration
- Raw downloaded media that you do not have rights to redistribute

If a credential was previously committed, rotate it immediately and remove it from Git history before publishing.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
