# Release preparation

The maintainer selected **v0.1.0** for the first release and the **MIT license**. This release includes the v0.2 implementation plan. Package and runtime versions remain 0.1.0.

The tag-triggered release workflow runs tests, builds and verifies packages, and publishes wheel, source distribution and SHA-256 checksums to GitHub Releases. PyPI publication is not configured. See [RELEASE_NOTES.md](RELEASE_NOTES.md).

Before authorizing a release:

1. Choose a license and add its text/metadata; this is a maintainer decision.
2. Review v0.2 behavior and platform/manual acceptance in `V0.2_IMPLEMENTATION.md` and `ACCEPTANCE.md`.
3. Decide the release version, then update `pyproject.toml`, `crux/__init__.py`, and release-specific test expectations together.
4. Run `python -m pytest -q -rs`, `python -m build`, and `python scripts/verify_wheel.py dist/FILE.whl` against newly built artifacts.
5. Inspect wheel/sdist contents, run the sdist tests, verify installed executable/module entry points and offline runtime, and check the actual cross-platform CI results.
6. Test `install.sh` using a temporary HOME/data directory and local wheels. Verify one-time backups, executable linking and refusal to overwrite unrelated files. Integration must not modify PATH; document any existing PATH setup needed.
7. Review dependencies, README/installation/help consistency and remaining manual acceptance. Verify GNOME restoration in a disposable profile on a real desktop.
8. Publish/tag only after explicit authorization; build success is not publication.

CI currently targets Ubuntu/macOS/Windows and Python 3.11/3.14. Unsupported shells must not be advertised. There is no configured lint/type-check command. Runtime network access, telemetry, remote execution and theme downloads are outside the product scope.
