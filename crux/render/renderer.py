from rich.console import Console
from rich.text import Text
from rich.theme import Theme
from crux.core.terminal import detect
from crux.render.theme import ROLES


from crux.core.text import safe_text


class Renderer:
    def __init__(self, no_color=False):
        self.capabilities = detect(no_color=no_color)
        self.console = Console(theme=Theme(ROLES), no_color=not self.capabilities.color, force_terminal=self.capabilities.color, highlight=False)

    def line(self, value="", role="file"):
        self.console.print(Text(safe_text(value), style=role), soft_wrap=True)

    def icon(self, directory, enabled=True):
        if not enabled:
            return ""
        if self.capabilities.unicode:
            return "📁 " if directory else "📄 "
        return "[DIR] " if directory else "[FILE] "
