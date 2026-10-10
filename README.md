# CRUX

Make the terminal yours. Crux is a local-first terminal enhancement toolkit for Python 3.11+.

## Install without activation

From this checkout on Linux/macOS with Bash or Zsh:

```sh
./install.sh --shell bash
# Zsh: ./install.sh --shell zsh
```

The installer creates an isolated environment under `${XDG_DATA_HOME:-~/.local/share}/crux`, links `crux` into `~/.local/bin`, and installs a backed-up shell profile block. Open a new terminal afterward. No virtual environment activation or per-session setup is needed. Python's `venv` support must be installed; dependency installation needs a package index or local wheels. Crux runs offline after installation.

Alternatively, use pipx (including on Windows):

```sh
pipx install .
pipx ensurepath
# Open a new terminal if pipx changed PATH.
crux install --shell bash --yes
# Zsh: crux install --shell zsh --yes
# PowerShell: crux install --shell powershell --profile "$PROFILE" --yes
```

The distribution is `crux-terminal`; it is not yet published to PyPI. Installing a Python wheel alone does not modify shell profiles; use `crux install` to connect your shell.

## Everyday commands

```sh
git status
ls
tree
```

In an integrated Bash/Zsh shell, these exact commands render Crux's branch/change summary, directory listing, and bounded tree. PowerShell currently supports `git status` and the prompt. Other Git commands and commands with arguments/options use the original executable. Pipes and redirected output use native commands in Bash/Zsh, preserving machine-readable behavior. PowerShell supports console redirection detection; its internal pipelines have different semantics and are not automatically detected. Use `git.exe` for native Git in PowerShell pipelines.

Use `command git status`, `command ls`, or `command tree` in Bash/Zsh to explicitly bypass Crux. Native `tree` must be installed for tree calls with arguments or redirected output. Git must be installed for Git support. The integration clears aliases named `git`, `ls`, and `tree` in the running shell so these functions take precedence. Unrelated aliases remain intact, and the original alias definitions in your profile are preserved.

## Crux operations

```sh
crux --version
crux doctor
crux doctor --json
crux theme                    # current and available themes
crux theme light              # default, light, monochrome
crux config
crux config --json
crux install --shell bash --dry-run
crux uninstall --shell bash --yes
crux --help
```

`crux` is reserved for Crux management. The rendering helpers are private commands used by the integration. `crux init` remains a hidden compatibility alias for `crux install`.

Profile installation offers confirmation unless `--yes` is provided. It creates `<profile>.crux-backup` once, preserves unrelated configuration, and refuses symlinked profiles, malformed markers, and non-UTF-8 text. Open a new shell after installation/removal. Bash login profiles must source `.bashrc`; Zsh uses `$ZDOTDIR/.zshrc` when configured. Fish and cmd integration are currently unsupported.

Removal deletes only Crux's marked profile block. To remove the package too, use `pipx uninstall crux-terminal` for pipx installs. For `install.sh` installs, remove `~/.local/bin/crux` and the isolated `crux/venv` directory after removing integration.

## Configuration

Crux reads `$XDG_CONFIG_HOME/crux/config.toml` or `~/.config/crux/config.toml` on Linux/macOS, and `%APPDATA%\CRUX\config.toml` on Windows. `crux config` shows the effective values and path. No file is required. `crux theme NAME` saves the selected theme while retaining unrelated TOML settings and comments.

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

Invalid settings warn and fall back to defaults. Animations are reserved. `NO_COLOR` disables color; redirected output has no color escapes. Filenames are rendered literally and control characters escaped. Trees never descend through symlinks. Prompt Git reads have a 30 ms timeout; process startup adds overhead. The prompt uses a compact two-line frame with colored directory, Git, environment, and exit-status segments. Theme changes apply to the next prompt and command output; `monochrome` and `NO_COLOR` disable prompt colors. Themes style Crux output rather than changing the terminal emulator background. Crux collects no telemetry.

## Development

```sh
python -m pip install -e '.[dev]'
python -m pytest
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ACCEPTANCE.md](ACCEPTANCE.md). Tests use temporary profiles; they do not edit your personal shell configuration.
