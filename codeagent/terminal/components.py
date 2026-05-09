"""
Terminal display components using Rich library.
"""

from rich.console import Console
from rich.live import Live
from rich.box import MINIMAL
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Group


class BaseBlock:
    """A visual block on the terminal."""

    def __init__(self):
        self.live = Live(
            auto_refresh=False,
            console=Console(),
            vertical_overflow="visible",
        )
        self.live.start()

    def end(self):
        """Stop the live display."""
        self.refresh(cursor=False)
        self.live.stop()

    def refresh(self, cursor=True):
        """Refresh the display. Subclasses must implement."""
        raise NotImplementedError


class MessageBlock(BaseBlock):
    """Display assistant messages with markdown rendering."""

    def __init__(self):
        super().__init__()
        self.message = ""

    def refresh(self, cursor=True):
        content = self.message
        if cursor:
            content += "●"

        markdown = Markdown(content.strip())
        panel = Panel(markdown, box=MINIMAL)
        self.live.update(panel)
        self.live.refresh()


class CodeBlock(BaseBlock):
    """Display code with syntax highlighting and output."""

    def __init__(self):
        super().__init__()
        self.language = ""
        self.code = ""
        self.output = ""
        self.margin_top = True

    def end(self):
        self.refresh(cursor=False)
        super().end()

    def refresh(self, cursor=True):
        if not self.code and not self.output:
            return

        code = self.code
        if cursor:
            code += "●"

        syntax = Syntax(
            code.strip(),
            self.language or "text",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
        code_panel = Panel(syntax, box=MINIMAL, style="on #272722")

        if self.output and self.output != "None":
            output_panel = Panel(self.output, box=MINIMAL, style="#FFFFFF on #3b3b37")
        else:
            output_panel = ""

        group_items = [code_panel, output_panel]
        if self.margin_top:
            group_items = [""] + group_items
        group = Group(*group_items)

        self.live.update(group)
        self.live.refresh()
