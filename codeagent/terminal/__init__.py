"""
Terminal interface package for CodeAgent.
"""

from .terminal_interface import terminal_interface, run_terminal
from .components import MessageBlock, CodeBlock, BaseBlock

__all__ = [
    "terminal_interface",
    "run_terminal",
    "MessageBlock",
    "CodeBlock",
    "BaseBlock",
]
