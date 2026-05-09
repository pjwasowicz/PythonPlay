# Repository Guidelines

## Project Structure & Module Organization
This repository is a desktop Python app for DJ playback. The entry point is `milonga.py`, which boots `MilongaApp` from `milonga_app.py`. Core modules live at the repository root: `player.py` handles audio playback and DSP, `config.py` manages persisted settings, `gui_builder.py` builds the Tk UI, and `utils.py`/`lists.py` contain helpers. Static assets are stored in `icons/`, `themes/`, and `ffmpeg/`. Build outputs land in `build/` and `dist/`; treat those as generated artifacts.

## Build, Test, and Development Commands
Create or activate the local virtual environment before changes.

```bash
pip install -r requirements.txt
python milonga.py
python setup.py build
python setup.py bdist_mac
python setup_windows.py build
```

`python milonga.py` runs the app locally. `setup.py` builds the macOS app bundle with `cx_Freeze`; `setup_windows.py` builds the Windows executable. `run_milonga.sh` opens the packaged macOS app, not the source tree.

## Coding Style & Naming Conventions
Use 4-space indentation and follow the existing Python style: modules in `snake_case`, classes in `PascalCase`, functions and variables in `snake_case`, constants in `UPPER_SNAKE_CASE`. Keep imports grouped at the top and prefer small, focused helper functions over deeply nested UI logic. Preserve the current flat-module layout unless a refactor is explicitly planned.

## Testing Guidelines
There is no automated test suite in the repository yet. Verify changes with targeted manual smoke tests by launching `python milonga.py` and exercising the affected flow: playlist loading, playback controls, export, device selection, and theme changes. If you add tests, place them under a new `tests/` directory and use `test_*.py` names so a future `pytest` setup is straightforward.

## Commit & Pull Request Guidelines
Recent history uses short, direct commit messages such as `setup` and `v2`; keep new commits equally focused, but prefer clear imperative summaries like `Add hog mode fallback`. Separate unrelated fixes into different commits. Pull requests should describe the user-visible change, list manual test steps, and include screenshots for UI adjustments or packaging notes for macOS/Windows build changes.

## Configuration & Assets
Do not hardcode machine-specific paths. Settings are persisted through `config.py` in the user application-support directory, while bundled resources must remain referenced with repo-relative paths such as `icons/play.png` and `themes/tango.json`.
