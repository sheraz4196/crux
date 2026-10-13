# v0.2 manual acceptance

Use disposable profiles first. This checklist is not a claim that interactive or cross-platform acceptance has passed. Automated results are recorded in [V0.2_IMPLEMENTATION.md](V0.2_IMPLEMENTATION.md).

- [ ] Build/install into a clean environment; check both `crux --version` and `python -m crux --version`.
- [ ] Run public help, doctor text/JSON, config text/JSON/get/set/reset, ls/tree text/JSON, Git status in clean/dirty repositories, and multi-file view.
- [ ] Verify all five themes, `NO_COLOR`, `TERM=dumb`, and redirected output without terminal controls.
- [ ] Preview `crux install --shell SHELL --profile PATH --dry-run`; inspect the prompt replacement explanation and native-wrapper opt-in policy.
- [ ] Install into a disposable profile; confirm one-time backup, file mode, repeated install, malformed marker refusal and exact removal.
- [ ] Verify aliases/functions named git/ls/tree/cat, unrelated aliases/functions, PATH, environment, stdin, stdout, pipes and redirection before/after default install and uninstall.
- [ ] Repeat with Bash/Zsh `--enhance-commands`; confirm existing aliases/functions are skipped and exact supported TTY routes work.
- [ ] Check unsupported arguments, stdin/no operands/non-regular cat operands, command substitution, and native `command NAME` bypass with opt-in wrappers.
- [ ] Check `--keep-prompt` with an existing prompt framework and `crux_restore_prompt` in the current session. A user-owned recovery helper must remain unchanged.
- [ ] Reopen the shell after updating/removing integration, particularly when upgrading from v0.1's native wrappers.
- [ ] Check completion, history, built-ins, background jobs, job control and shell scripting.
- [ ] Check Ctrl+C, Ctrl+D, Ctrl+Z, Ctrl+L and arrow keys in real interactive terminals.
- [ ] In a disposable GNOME profile, sync theme colors; change an unrelated preference; restore colors and confirm the preference remains.
- [ ] Change a managed GNOME color after sync and confirm recovery refuses to overwrite it. Test repeated recovery and retained backups.
- [ ] Verify terminal reset controls in supported emulators, and confirm recovery disables prompt palette writes; selecting a theme reenables them.
- [ ] Record end-to-end prompt median/p95 with `python scripts/benchmark_prompt.py --samples 30`, also using `--executable` for the installed command.
- [ ] Repeat shell/UI checks on Linux/Bash, macOS/Zsh, and Windows/PowerShell. PowerShell native commands must remain untouched.

Fish/cmd integration and PowerShell native wrappers are unsupported. GNOME tests that mock subprocesses do not establish real desktop behavior. OSC reset returns emulator defaults where supported, not a captured arbitrary previous runtime palette. Recovery from a v0.1 backup without ownership state requires selective manual restoration. No colors are restored automatically on shell uninstall.
