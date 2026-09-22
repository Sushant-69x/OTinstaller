# Directory layout

The otinstaller home directory (default `~/.otinstaller/`, configurable via `OTINSTALLER_HOME`) contains:

```
~/.otinstaller/
├── tools/              # One directory per installed tool
│   ├── sherlock/
│   │   ├── venv/       # Virtual environment (pip or git tools)
│   │   └── src/        # Source code (git tools only)
│   └── theharvester/
│       ├── venv/
│       └── src/
├── logs/               # Installation logs
│   ├── install-sherlock.log
│   └── install-theharvester.log
├── state.db            # SQLite database tracking installed tools
├── accepted.json       # Notice acceptance record
└── .env                # API keys (mode 600)
```

Results are saved under `./results/` (or `OTINSTALLER_RESULTS_DIR`) by default:

```
results/
├── <tool>/
│   └── <sanitized-target>/
│       └── <timestamp>_<tool>_<sanitized-target>_<runid>.txt
│       └── <timestamp>_<tool>_<sanitized-target>_<runid>.meta.json
└── cases/
    └── <sanitized-case>/
        └── <tool>/
            └── <sanitized-target>/
                └── <timestamp>_<tool>_<sanitized-target>_<runid>.txt
                └── <timestamp>_<tool>_<sanitized-target>_<runid>.meta.json
```

## Platform support

Linux only, tested on Ubuntu 22.04/24.04, Debian 12 and Arch Linux via CI; Kali Linux checked manually before release (it is Debian-based).

## Tool installation

Each tool gets its own directory under `tools/<name>/`. The virtualenv is always created at `tools/<name>/venv/`. For git-based tools, the source is cloned to `tools/<name>/src/`.

The virtualenv is created in its final location because venv scripts embed absolute paths and break when moved.

## Install flow

1. Run `otinstaller init` to create directories, accept the notice, and create `.env`.
2. Run `otinstaller install <name>`:
   - Check notice acceptance.
   - Resolve tool name from registry.
   - Show what will be installed; prompt for confirmation (or `--yes`).
   - Create `tools/<name>/` and log file.
   - Dispatch to pip or git installer.
   - Verify entrypoint exists.
   - Read version (pip: `pip show`, git: commit hash).
   - Record in `state.db`.
   - On any failure, remove the tool directory and re-raise.
3. Run `otinstaller list --installed` to see installed tools.

## Remove flow

1. Run `otinstaller remove <name>` or `otinstaller remove --all`:
   - Resolve tools from state DB.
   - Prompt for confirmation (or `--yes`).
   - Call `safe_rmtree` on `tools/<name>/`.
   - Remove row from `state.db`.
2. `safe_rmtree` refuses to delete outside `tools/` or the `tools/` directory itself.

## Python version

Tools run on the same Python interpreter that runs otinstaller. The virtualenv is created with `python -m venv`, inheriting the current Python version.