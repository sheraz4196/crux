# Installing Crux

Crux needs **Python 3.11 or newer**. Install it once, connect your shell, and open a new terminal. You do not need to activate a virtual environment each time.

Crux is not published to PyPI yet. Install from this repository or a locally built wheel; do not use `pip install crux`.

## Requirements

| Requirement | Details |
| --- | --- |
| Python | Python 3.11+, including `pip` and virtual-environment (`venv`) support. Keep Python installed after installing Crux. |
| Shell | Bash or Zsh on Linux/macOS; PowerShell on Windows. Fish and Command Prompt (`cmd.exe`) integration are currently unsupported. |
| Terminal | A terminal supporting ANSI colours. Background, cursor, and palette changes require OSC 4/10/11/12 support; support varies by emulator. |
| Source code | Download or clone [the Crux repository](https://github.com/sheraz4196/crux). The install commands below run from the folder containing `pyproject.toml`. |
| Internet | Needed to download Python, installation tools, and dependencies unless you already have local packages/wheels. Crux runs offline after installation. |
| Git | Optional for installation from a downloaded ZIP; required for Git status and repository information in the prompt. |
| Fonts | A Unicode-capable font for prompt symbols. A Nerd Font is optional, useful for file icons. |

The installer downloads Crux's Python dependencies (`typer` and `rich`) automatically. Node.js, npm, and a compiler are not required for a normal installation. Install the native `tree` utility if you want Bash/Zsh `tree` commands with arguments or redirected output.

## Windows

Use PowerShell in Windows Terminal for testing. PowerShell 7 is recommended. Install Python from [Python's official Windows instructions](https://docs.python.org/3/using/windows.html), then open a fresh PowerShell window and check:

```powershell
py --version
py -m pip --version
```

The Python version must be at least 3.11. If your installation exposes `python` instead of `py`, replace `py` with `python` in the commands below.

### Install

Install [pipx](https://pipx.pypa.io/stable/how-to/install-pipx.html), which keeps Crux in its own environment:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Close and reopen Windows Terminal so the PATH change takes effect. Go to your downloaded or cloned Crux folder, replacing this example path with its actual location:

```powershell
Set-Location "$HOME\Downloads\crux"
py -m pipx install .
crux --version
crux install --shell powershell --profile "$PROFILE" --yes
```

`$PROFILE` selects the profile for the PowerShell host you are currently using. PowerShell 7, Windows PowerShell, and VS Code's PowerShell host can have different profiles. Run the integration command in each host where you want Crux. See [Microsoft's profile documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles).

Open a new PowerShell tab, then run:

```powershell
crux doctor
crux theme cobalt
git status
```

Run `git status` inside a Git repository. PowerShell integration currently provides the prompt and `git status`; its `ls` and `tree` commands retain their normal behaviour. Use `git.exe status` when you need native Git output, especially in PowerShell pipelines.

### If PowerShell blocks the profile

Check the effective policies:

```powershell
Get-ExecutionPolicy -List
```

On a personal computer, if policy prevents your local profile from loading, you can allow local scripts for your user account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

This changes your user's script policy; it does not require an administrator shell. Organisation-managed policies can override it. Follow your organisation's policy on managed machines. See [Microsoft's execution-policy documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies).

Existing PowerShell profiles must be UTF-8 for Crux to edit them. If installation reports a non-UTF-8 profile, back up that file and save it as UTF-8 in your editor before retrying.

## Linux

Check Python first:

```sh
python3 --version
python3 -m pip --version
```

On Ubuntu/Debian, install the prerequisites if missing:

```sh
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

Check that `python3` is at least 3.11; older distributions may need a newer Python installed separately. On other distributions, use their package manager for Python, pip, venv support, and Git.

From the Crux source folder, choose your shell:

```sh
# Bash
sh install.sh --shell bash

# Or Zsh
sh install.sh --shell zsh
```

Run only the command matching your shell. The script installs Crux under `${XDG_DATA_HOME:-$HOME/.local/share}/crux/venv`, creates `~/.local/bin/crux`, and connects your shell. Run it as your normal user, without `sudo`.

Open a new terminal and run:

```sh
crux doctor
crux theme cobalt
```

If you prefer pipx, install it using your distribution's instructions, then run these commands from the Crux source folder:

```sh
pipx install .
pipx ensurepath
# Open a new terminal if PATH changed, then:
crux install --shell bash --yes
# For Zsh, replace bash with zsh.
```

## macOS

Install Python 3.11+ from [python.org](https://www.python.org/downloads/macos/) or through [Homebrew](https://docs.brew.sh/Installation). If Homebrew is already installed:

```sh
brew install python
python3 --version
python3 -m pip --version
```

Install Git if you need repository features and `git --version` does not work. Crux does not require a compiler; your chosen Python or Git installation method may have its own prerequisites.

From the Crux source folder, use Zsh unless you have configured a different shell:

```sh
sh install.sh --shell zsh
# If you use Bash instead:
# sh install.sh --shell bash
```

Open a new terminal:

```sh
crux doctor
crux theme cobalt
```

For a pipx installation, use `brew install pipx`, then follow the Linux pipx steps with `--shell zsh`. Avoid installing Crux into macOS's system Python.

If a Bash login shell does not show the prompt, make sure its existing login profile (`~/.bash_profile` or `~/.profile`) sources `~/.bashrc`. You can add this once to the login profile it actually loads:

```sh
if [ -f "$HOME/.bashrc" ]; then
  . "$HOME/.bashrc"
fi
```

## Verify the installation

In a newly opened terminal:

```sh
crux --version
crux doctor
crux config
crux theme
```

Available themes are `default`, `dark`, `light`, `cobalt`, and `monochrome`. In Bash/Zsh, also try `ls`, `tree`, and `git status` inside a repository. Commands with arguments/options and redirected output normally use the native programs.

### Theme and startup behaviour

GNOME Terminal theme selection also saves colours to its **default profile**, using `gsettings` and `dconf`. This makes new windows start with the selected background and updates the scrollbar surround. The original profile is backed up once beside Crux's configuration. The scrollbar handle keeps the desktop's GTK styling.

Windows and macOS currently use runtime terminal colour sequences; Crux does **not** save Windows Terminal, Terminal.app, or iTerm2 profile settings. A background flash before the first prompt or unchanged scrollbar styling can therefore remain on those platforms. Set the emulator's saved profile colours to match your Crux theme if you want the same startup appearance. Some emulators may support only part of the runtime palette.

`NO_COLOR`, `TERM=dumb`, and `crux --no-color theme NAME` suppress runtime colour controls. `crux theme NAME --sync-profile` requests a GNOME default-profile update even when output is redirected; it is not a Windows/macOS profile installer.

## Update after changing or downloading the source

Installing from a source folder copies the package into the installation environment. Editing the source does not automatically update the installed `crux` command.

For pipx installations, run from the updated source folder:

```sh
pipx install --force .
```

On Windows you can use `py -m pipx install --force .` instead. For `install.sh` installations on Linux/macOS, rerun the script with the same shell option. If the link path already contains a regular file, the script refuses to replace it; inspect the existing installation before changing it.

If behaviour still looks outdated, check which executable your shell is using:

```powershell
# PowerShell
Get-Command crux -All
```

```sh
# Bash/Zsh
command -v crux
```

Use one installation method per machine to avoid competing copies on PATH. If `crux` is not found after pipx installation, run `pipx ensurepath` (or `py -m pipx ensurepath` on Windows) and reopen the terminal. If Linux reports missing `ensurepip`/venv support, install your distribution's venv package and retry.

## Configuration and removal

Configuration is stored at `%APPDATA%\CRUX\config.toml` on Windows and `${XDG_CONFIG_HOME:-$HOME/.config}/crux/config.toml` on Linux/macOS. `crux config` prints the actual path.

Remove the shell integration before removing the package:

```powershell
# Windows: run in the same PowerShell host used during installation
crux uninstall --shell powershell --profile "$PROFILE" --yes
py -m pipx uninstall crux-terminal
```

```sh
# Linux/macOS: use bash or zsh as appropriate
crux uninstall --shell zsh --yes
# If installed with pipx:
pipx uninstall crux-terminal
```

For `install.sh` installations, after removing integration, remove the Crux link at `~/.local/bin/crux` and its isolated environment under `${XDG_DATA_HOME:-$HOME/.local/share}/crux/venv`. Open a new terminal afterward. Profile integration is removed by deleting only Crux's marked block; your other shell settings are preserved. Configuration files and GNOME Terminal's saved colours remain, and can be restored separately from the profile backup.
