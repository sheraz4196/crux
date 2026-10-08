from pathlib import Path
import typer
from crux.cli.main import app
from crux.cli.common import fail
from crux.core.shell import detect_shell, profile_path
from crux.integrations.manager import block, read_profile, edit_profile, START


def integration(shell, profile, yes, remove, dry_run):
    shell = shell or detect_shell()
    try:
        content = block(shell)
        path = profile or profile_path(shell)
        existing = read_profile(path)
        if (START in existing) != remove:
            typer.echo('CRUX is already installed.' if not remove else 'No CRUX integration found.')
            return
        typer.echo(f'{"Remove" if remove else "Install"} CRUX integration: {path}')
        if dry_run:
            typer.echo(content if not remove else 'Only the marked CRUX block will be removed.')
            return
        if not yes:
            typer.confirm('Continue?', abort=True)
        changed = edit_profile(path, shell, remove)
        typer.echo('Updated. Open a new shell to apply the change.' if changed else 'No changes required.')
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command('init')
def initialize(shell: str = typer.Option(None, '--shell'), profile: Path = typer.Option(None, '--profile'), yes: bool = typer.Option(False, '--yes', '-y'), dry_run: bool = typer.Option(False, '--dry-run')):
    """Preview or install optional prompt integration with a profile backup."""
    integration(shell, profile, yes, False, dry_run)


@app.command()
def uninstall(shell: str = typer.Option(None, '--shell'), profile: Path = typer.Option(None, '--profile'), yes: bool = typer.Option(False, '--yes', '-y'), dry_run: bool = typer.Option(False, '--dry-run')):
    """Remove only CRUX's marked block. Reopen the shell afterward."""
    integration(shell, profile, yes, True, dry_run)


@app.command(hidden=True)
def prompt(status: int = typer.Option(0, '--status'), shell: str = typer.Option('plain', '--shell')):
    """Render plain prompt context without loading Rich on the fast path."""
    from crux.prompt.builder import build
    value = build(status)
    if shell == 'zsh':
        value = value.replace('%', '%%')
    typer.echo(value, nl=False)
