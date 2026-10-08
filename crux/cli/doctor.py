import json
import sys
from dataclasses import asdict
import typer
from crux.cli.main import app
from crux.cli.common import context
from crux.core.platform import system_info
from crux.core.shell import detect_shell
from crux.core.environment import tool_version, duplicate_paths, virtual_environment


@app.command()
def doctor(ctx: typer.Context, json_output: bool = typer.Option(False, '--json'), no_color: bool = typer.Option(False, '--no-color')):
    """Inspect local platform, terminal, tools and configuration."""
    renderer, config = context(ctx, no_color)
    warnings = list(config.warnings)
    tools = {name: tool_version(name) for name in ('git', 'node', 'npm', 'docker')}
    tools['python'] = sys.version.split()[0]
    if not tools['git']:
        warnings.append('Git unavailable')
    if duplicate_paths():
        warnings.append('PATH contains duplicate entries')
    report = {'system': system_info(), 'shell': detect_shell(), 'terminal': asdict(renderer.capabilities), 'tools': tools, 'virtual_environment': virtual_environment(), 'configuration': {'path': str(config.path), 'status': 'invalid settings; defaults applied' if config.warnings else 'valid' if config.path.exists() else 'defaults'}, 'warnings': warnings}
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return
    renderer.line('CRUX Doctor', 'primary')
    for section, data in report.items():
        renderer.line(section.capitalize(), 'secondary')
        if isinstance(data, dict):
            for key, value in data.items():
                renderer.line(f'  {key}: {value if value is not None else "unavailable"}')
        elif isinstance(data, list):
            for value in data:
                renderer.line(f'  {value}', 'warning')
            if not data:
                renderer.line('  None', 'muted')
        else:
            renderer.line(f'  {data if data is not None else "none"}')
