# Contributing

Use Python 3.11+ and install `python -m pip install -e '.[dev]'` in a virtual environment. Run `python -m pytest` before submitting changes. Build distributions with `python -m build`.

Keep platform behavior in `core`, data gathering separate from `render`, and command registration in `cli`. Use semantic theme roles, argument-list subprocesses with timeouts, literal rendering of external text, and safe configuration defaults. Runtime features must operate offline.

Add regression tests for bugs. Profile changes require tests for backups, idempotency, exact removal, malformed blocks, and preserved shell functionality. Use temporary profiles, never your personal configuration. Keep command wrappers narrow: preserve native options, subcommands, pipes and redirected output. Do not add telemetry or replace personal aliases.

The project has not yet selected an open-source license; obtain the owner's license decision before redistributing releases.
