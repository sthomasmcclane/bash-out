# BashOut: A Forward-only Writing App

BashOut is a minimalist writing tool designed to help you focus on writing by providing a clean interface and tracking your word count. It comes in two flavors, both designed to work seamlessly across platforms:

1. [CLI Version](docs/bash-version.md): A lightweight Bash script that runs in any Unix-like terminal (macOS, Linux)
2. [GUI Version](docs/gui-version.md): A cross-platform PyQt5-based desktop application (macOS, Windows, Linux)

## Quick Starts

### Terminal Version
```bash
chmod +x bashout.sh
./bashout.sh
```

### GUI Version
```bash
pip install PyQt5
python3 bashout_gui.py
```

## Shared Configuration File

Both the CLI and GUI versions support a shared configuration file: `~/.bashoutrc` (in your home directory).
- The config file uses simple `key: value` pairs (see `docs/bashoutrc.example` for a template and documentation).
- If you use both CLI and GUI, be aware that changes made in the GUI may overwrite manual edits or comments in this file.
- **Windows users:** Use WSL or Cygwin and place the config file in your Unix home directory (e.g., `/home/YourName/.bashoutrc`).

## Philosophy

BashOut is designed to help you focus on writing by:
- Providing a clean, distraction-free interface
- Tracking your word count
- Encouraging forward-only writing
- Automatically saving your work

## License

This project is licensed under the terms of the LICENSE file included in this repository. 