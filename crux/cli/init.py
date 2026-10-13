from pathlib import Path
import typer
from crux.cli.main import app
from crux.cli.common import fail
from crux.core.shell import detect_shell, profile_path
from crux.integrations.manager import block, read_profile, edit_profile, START


def integration(shell, profile, yes, remove, dry_run, enhance_commands=False, keep_prompt=False):
    shell = shell or detect_shell()
    try:
        content = block(shell, enhance_commands, keep_prompt)
        path = profile or profile_path(shell)
        existing = read_profile(path)
        if remove and START not in existing:
            typer.echo('No CRUX integration found.')
            return
        typer.echo(f'{"Remove" if remove else "Install"} CRUX integration: {path}')
        if not remove:
            typer.echo('Existing prompt preserved. PATH is unchanged.' if keep_prompt else 'Replaces the prompt; crux_restore_prompt restores it in this session. Use --keep-prompt to preserve it. PATH is unchanged.')
            typer.echo('Native wrappers: opt-in; existing aliases/functions are skipped.' if enhance_commands else 'Native commands, aliases and functions are unchanged.')
        if dry_run:
            typer.echo(content if not remove else 'Only the marked CRUX block will be removed.')
            return
        if not yes:
            typer.confirm('Continue?', abort=True)
        changed = edit_profile(path, shell, remove, enhance_commands, keep_prompt)
        typer.echo('Updated. Open a new shell to apply the change.' if changed else 'No changes required.')
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command('install')
@app.command('init', hidden=True)
def initialize(keep_prompt: bool = typer.Option(False, '--keep-prompt', help='Keep the existing prompt configuration.'), enhance_commands: bool = typer.Option(False, '--enhance-commands', help='Opt in to Bash/Zsh native wrappers, skipping existing aliases/functions.'), shell: str = typer.Option(None, '--shell'), profile: Path = typer.Option(None, '--profile'), yes: bool = typer.Option(False, '--yes', '-y'), dry_run: bool = typer.Option(False, '--dry-run')):
    """Install the prompt with a profile backup; native wrappers are opt-in."""
    integration(shell, profile, yes, False, dry_run, enhance_commands, keep_prompt)


@app.command()
def uninstall(shell: str = typer.Option(None, '--shell'), profile: Path = typer.Option(None, '--profile'), yes: bool = typer.Option(False, '--yes', '-y'), dry_run: bool = typer.Option(False, '--dry-run')):
    """Remove only CRUX's marked block. Reopen the shell afterward."""
    integration(shell, profile, yes, True, dry_run)


@app.command(hidden=True)
def prompt(status: int = typer.Option(0, '--status'), shell: str = typer.Option('plain', '--shell')):
    """Render plain prompt context without loading Rich on the fast path."""
    from crux.prompt.builder import build
    value = build(status, shell=shell)
    typer.echo(value, nl=False)
