# v0.1 manual acceptance

Run these checks in a disposable shell profile first, then optionally in your own environment. Automated tests do not establish keyboard behavior or cross-platform performance.

- [ ] Install from this checkout and run `crux --version` and `crux --help`.
- [ ] Run `crux doctor`, `crux ls`, `crux tree`, and `crux config`.
- [ ] Run `crux git status` inside a clean and modified repository.
- [ ] Redirect a listing and verify it has no color escape sequences.
- [ ] Preview `crux init --dry-run`, then install for your supported shell.
- [ ] Reopen the shell and check prompt, aliases, functions, PATH and environment variables.
- [ ] Verify commands, shell built-ins, history, completion and background jobs.
- [ ] Verify Ctrl+C, Ctrl+D, Ctrl+Z, Ctrl+L and arrow keys.
- [ ] Verify pipes, redirection, command substitution and ordinary Git commands.
- [ ] Measure prompt responsiveness in small and large repositories.
- [ ] Run init again and verify no duplicate block.
- [ ] Run `crux uninstall`, reopen, and verify original shell behavior.
- [ ] Repeat on Linux/Bash, macOS/Zsh, and Windows/PowerShell.

cmd and Fish profile integration are deferred. Full Node version detection is available in doctor; the prompt uses a project indicator to avoid a subprocess. The package is not published and a license choice remains with the project owner.
