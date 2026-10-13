# CRUX v0.1.0

First public release of CRUX, a local-first terminal enhancement toolkit for Python 3.11+.

- Directory listings, bounded trees, Git status summaries, and a syntax-highlighted file viewer.
- Bash, Zsh, and PowerShell prompt integration with guarded profile edits and backups.
- Five themes, editable TOML configuration, and read-only diagnostics.
- Optional Bash/Zsh native command wrappers that preserve existing aliases and functions.
- Terminal palette controls and guarded GNOME Terminal profile recovery.
- MIT license; wheel, source distribution, and SHA-256 checksums attached.

## Install

Download the attached wheel, then run:

```sh
pipx install ./crux_terminal-0.1.0-py3-none-any.whl
pipx ensurepath
crux --version
crux install --shell bash --yes
```

Use `--shell zsh` for Zsh or `--shell powershell --profile "$PROFILE"` for PowerShell. Dependency installation needs a package index or local wheels; runtime works offline. This release does not publish to PyPI.

## Known limitations

Fish/cmd integration and PowerShell native wrappers are unsupported. Terminal palette/reset support varies by emulator. Real interactive desktop acceptance, including GNOME profile restoration, remains manual; automated tests do not establish those behaviors. Prompt timing depends on the machine and repository.
