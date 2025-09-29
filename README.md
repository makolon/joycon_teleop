## Joy-Con Teleoperation (macOS)

A small utility that reads input from Nintendo Joy-Cons via HIDAPI on macOS and streams normalized stick/buttons over UDP. Managed with `uv` for zero-fuss Python environments.

### Features
- Read both left and right Joy-Cons
- Normalize analog stick axes to [-1, 1]
- Send inputs as JSON via UDP to a configurable host/port

### Requirements
- macOS (Apple Silicon or Intel)
- Homebrew
- HIDAPI (`brew install hidapi`)
- Python 3.11+ (managed automatically by `uv`)

### Setup
1) Install HIDAPI via Homebrew:

```bash
brew install hidapi
```

2) (Optional, if you don't have it) Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You do not need to manually create a virtual environment; `uv` will manage it for you.

### Run
On macOS, ensure the HIDAPI dynamic library is discoverable at runtime and run the script via `uv`:

```bash
DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix hidapi)/lib" uv run python teleop.py
```

Notes:
- Pair your Joy-Cons to macOS via Bluetooth beforehand.
- If needed, adjust `DEST_HOST` and `DEST_PORT` in `teleop.py`.
- Stop with Ctrl-C.

### Troubleshooting
- dyld: Library not loaded / hidapi issues: Verify HIDAPI is installed and the `DYLD_FALLBACK_LIBRARY_PATH` is set exactly as above.
- Permission prompts: If macOS blocks HID access, grant permissions in System Settings (e.g., Input Monitoring / Accessibility) and reconnect the controllers.

### Project Metadata
Project configuration and dependencies are defined in `pyproject.toml`; `uv` uses this file directly.


