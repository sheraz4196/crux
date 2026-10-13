# Contributing

Use Python 3.11+ and install `python -m pip install -e '.[dev]'` in a virtual environment. Run `python -m pytest` before submitting changes. Build distributions with `python -m build`.

Keep platform behavior in `core`, data gathering separate from `render`, and command registration in `cli`. Use semantic theme roles, argument-list subprocesses with timeouts, literal rendering of external text, and safe configuration defaults. Runtime features must operate offline.

Add regression tests for bugs. Profile changes require tests for backups, idempotency, exact removal, malformed blocks, and preserved shell functionality. Use temporary profiles, never your personal configuration. Keep command wrappers narrow: preserve native options, subcommands, pipes and redirected output. Do not add telemetry. Native wrappers are opt-in and must skip existing aliases/functions. Never delete aliases, override user functions, or modify PATH from the integration block. Preserve original prompt state and offer --keep-prompt. Test with Bash alias expansion enabled and real terminal output.

The project has not yet selected an open-source license; obtain the owner's license decision before redistributing releases.

Run `python scripts/benchmark_prompt.py --samples 30` for end-to-end prompt measurements. Do not assert a universal 50 ms wall-clock limit. Verify built wheels with `python scripts/verify_wheel.py dist/FILE.whl`; its runtime smoke tests block Python network connections and run outside the checkout. No lint/type-check command is currently configured.
