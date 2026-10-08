import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'prompt' and '--help' not in sys.argv:
        import argparse
        from crux.prompt.builder import build
        parser = argparse.ArgumentParser()
        parser.add_argument('--status', type=int, default=0)
        parser.add_argument('--shell', default='plain')
        args = parser.parse_args(sys.argv[2:])
        value = build(args.status)
        if args.shell == 'zsh':
            value = value.replace('%', '%%')
        sys.stdout.write(value)
        return
    from crux.cli.main import main as cli_main
    cli_main()
