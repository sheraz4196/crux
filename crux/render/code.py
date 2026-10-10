# THIS SHOWS THE FILES BEST POSSIBLE WAY IN THE TEMINAL, WHEN USER USES THE CAT COMMAND 

"""Theme-aware syntax colours for the file viewer."""
from pygments.style import Style
from pygments.token import Token, Comment, Keyword, Name, String, Number, Operator, Generic, Error
from rich.syntax import PygmentsSyntaxTheme
from crux.render.theme import TERMINAL_THEMES


def syntax_theme(name):
    palette = TERMINAL_THEMES.get(name, TERMINAL_THEMES['default'])
    colors = palette['ansi']
    foreground = palette['foreground']
    styles = {
        Token: foreground, Comment: colors[4], Keyword: colors[3],
        Name.Function: colors[3], Name.Class: colors[5], Name.Builtin: colors[6],
        Name.Tag: colors[6], Name.Attribute: colors[3], String: colors[2],
        Number: colors[1], Operator: colors[5], Generic.Heading: 'bold ' + colors[3],
        Generic.Subheading: 'bold ' + colors[6], Generic.Emph: 'italic',
        Generic.Strong: 'bold', Generic.Inserted: colors[2], Generic.Deleted: colors[1],
        Error: colors[1],
    }
    if name == 'cobalt':
        styles.update({Keyword: '#ff9d00', String: '#a5ff90', Name.Class: '#ff68b8'})
    if name == 'monochrome':
        styles = {token: foreground for token in styles}
        styles[Keyword] = 'bold ' + foreground
        styles[Generic.Heading] = 'bold ' + foreground
    theme = type('CruxCodeStyle', (Style,), {'background_color': palette['background'], 'styles': styles})
    return PygmentsSyntaxTheme(theme)
