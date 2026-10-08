# CRUX

Make the terminal yours.

CRUX v0.1 is an offline, local-first terminal enhancement toolkit for Python 3.11+. It works inside your existing terminal and shell. It does not replace either, intercept commands, change PATH, or collect telemetry.

## Install

From this checkout:

```sh
python3 -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
crux --version
```

The distribution is named `crux-terminal`; the executable is `crux`. This checkout is not published to PyPI. Dependency installation needs a package index or locally supplied wheels; installed CRUX operates offline.

## Commands

```sh
crux doctor                 # system, shell, terminal, tools and config
crux doctor --json
crux ls [path]              # directories first, sizes, symlink labels
crux ls -a -l --no-color
crux tree [path] --depth 2  # default depth 3, maximum 1000 entries
crux tree --max-entries 200
crux git status [path]      # branch, ahead/behind, index/worktree changes
crux config
crux config --json
crux --help
```

`--no-color` works globally and on display commands. `NO_COLOR` also disables colors. Redirected output contains no color escapes. Text is rendered literally, including filenames containing Rich markup; control characters are escaped. ASCII terminals use text icons and tree branches. Trees never descend through symlinks. Operational errors exit with status 1; configuration problems warn on stderr and use defaults.

## Configuration

No configuration file is required. CRUX reads `$XDG_CONFIG_HOME/crux/config.toml` or `~/.config/crux/config.toml` on Linux/macOS, and `%APPDATA%\CRUX\config.toml` on Windows. `crux config` shows the effective values and path. v0.1 inspects configuration; edit TOML yourself to customize it.

```toml
[general]
theme = "default"
icons = true
animations = false

[prompt]
enabled = true
show_git = true
show_python = true
show_node = true

[ls]
show_icons = true
show_sizes = true

[git]
enabled = true
```

Only the default semantic theme is implemented. Animations are reserved and inactive in v0.1. Invalid individual values fall back to defaults without overwriting your file. The prompt shows directory, Git state, active virtual environment, Node project presence, and previous exit status. It avoids invoking Node at every prompt. Git prompt reads have a 30 ms timeout and degrade to a directory prompt if unavailable. Local Python 3.14 measurements put complete prompt process startup at roughly 78–81 ms, above the ideal 50 ms goal; in-process rendering is under 50 ms. Large-repository and other-platform measurements remain pending. `enabled = false` uses a minimal prompt; uninstall integration to restore your original prompt.

## Optional shell integration

Bash and Zsh support automatic profile location. PowerShell requires the actual profile path explicitly; this handles different PowerShell editions and hosts without guessing.

```sh
crux init --shell bash --dry-run
crux init --shell bash
# Zsh: crux init --shell zsh
# PowerShell:
# crux init --shell powershell --profile "$PROFILE" --dry-run
# crux init --shell powershell --profile "$PROFILE"
```

Review the preview before installation. Installation asks for confirmation; `--yes` is available for scripts. CRUX appends one marked block and creates `<profile>.crux-backup` once, preserves unrelated configuration, and refuses malformed markers, symlinks and non-UTF-8 profiles. Existing prompt hooks are retained. Keep `crux` available in your normal shell environment; a project virtual environment must be activated for its executable to be available. If it is unavailable when a shell starts, the block does nothing.

Open a new shell after installation. Bash's `.bashrc` must already be sourced by your login profile when using login shells. Detection uses environment hints and can be overridden with `--shell`. Fish and cmd automatic integration are deliberately unsupported in v0.1; normal commands work in those shells.

```sh
crux uninstall --shell bash --dry-run
crux uninstall --shell bash
# PowerShell: crux uninstall --shell powershell --profile "$PROFILE"
```

Removal deletes only the marked block and never restores a stale backup over subsequent edits. Open a new shell afterward to restore its original prompt. To remove the Python package, run `python -m pip uninstall crux-terminal` after removing integration.

## Development and verification

```sh
python -m pip install -e '.[dev]'
python -m pytest
python -m build
```

Tests isolate configuration, create temporary Git repositories and profiles, and check CLI output, errors, terminal fallbacks, prompt context and shell preservation. CI runs Linux, macOS and Windows on Python 3.11 and 3.14. Real Bash tests run where Bash is available; Zsh/PowerShell tests run where those executables are available. Interactive keyboard behavior still needs manual acceptance on each target shell.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ACCEPTANCE.md](ACCEPTANCE.md). Future releases can add themes and Fish support without changing the data/presentation separation.
