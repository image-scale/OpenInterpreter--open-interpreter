"""
Tests for terminal interface.
"""

import pytest
from unittest.mock import patch, MagicMock, call

from codeagent import CodeAgent
from codeagent.terminal import (
    terminal_interface,
    run_terminal,
    MessageBlock,
    CodeBlock,
    BaseBlock,
)


class TestBaseBlock:
    """Tests for BaseBlock component."""

    def test_creates_live_display(self):
        """Should create a Rich Live display."""
        block = BaseBlock()
        assert block.live is not None
        block.live.stop()

    def test_end_stops_live_display(self):
        """End should stop the live display."""
        with patch.object(BaseBlock, 'refresh'):
            block = BaseBlock()
            block.end()
            assert not block.live.is_started

    def test_refresh_raises_not_implemented(self):
        """refresh should raise NotImplementedError."""
        block = BaseBlock()
        with pytest.raises(NotImplementedError):
            block.refresh()
        block.live.stop()


class TestMessageBlock:
    """Tests for MessageBlock component."""

    def test_creates_with_empty_message(self):
        """Should start with empty message."""
        block = MessageBlock()
        assert block.message == ""
        block.live.stop()

    def test_refresh_updates_display(self):
        """refresh should update the live display."""
        block = MessageBlock()
        block.message = "Hello world"
        block.refresh()
        block.live.stop()

    def test_refresh_with_cursor(self):
        """refresh with cursor=True should add cursor."""
        block = MessageBlock()
        block.message = "Test"
        block.refresh(cursor=True)
        block.live.stop()

    def test_refresh_without_cursor(self):
        """refresh with cursor=False should not add cursor."""
        block = MessageBlock()
        block.message = "Test"
        block.refresh(cursor=False)
        block.live.stop()


class TestCodeBlock:
    """Tests for CodeBlock component."""

    def test_creates_with_empty_code(self):
        """Should start with empty code and output."""
        block = CodeBlock()
        assert block.code == ""
        assert block.output == ""
        assert block.language == ""
        block.live.stop()

    def test_has_margin_top_by_default(self):
        """Should have margin_top True by default."""
        block = CodeBlock()
        assert block.margin_top is True
        block.live.stop()

    def test_refresh_with_code(self):
        """refresh should work with code."""
        block = CodeBlock()
        block.language = "python"
        block.code = "print('hello')"
        block.refresh()
        block.live.stop()

    def test_refresh_with_output(self):
        """refresh should work with output."""
        block = CodeBlock()
        block.language = "python"
        block.code = "print('hello')"
        block.output = "hello"
        block.refresh()
        block.live.stop()

    def test_refresh_empty_does_nothing(self):
        """refresh with no code or output should do nothing."""
        block = CodeBlock()
        block.refresh()  # Should not raise
        block.live.stop()

    def test_end_calls_refresh_without_cursor(self):
        """end should call refresh with cursor=False."""
        block = CodeBlock()
        block.code = "test"
        with patch.object(block, 'refresh') as mock_refresh:
            with patch.object(block.live, 'stop'):
                block.end()
        mock_refresh.assert_called_with(cursor=False)


class TestTerminalInterface:
    """Tests for terminal_interface function."""

    def test_yields_chunks_from_agent(self):
        """Should yield chunks from agent.chat()."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "content": "Hello"},
            {"type": "message", "end": True},
        ])

        chunks = list(terminal_interface(agent, message="test"))
        assert len(chunks) == 3
        assert chunks[1]["content"] == "Hello"

    def test_handles_message_chunks(self):
        """Should handle message type chunks."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "content": "Hi"},
            {"type": "message", "end": True},
        ])

        chunks = list(terminal_interface(agent, message="hello"))
        assert len(chunks) == 3

    def test_handles_code_chunks(self):
        """Should handle code type chunks."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "code", "start": True, "format": "python"},
            {"type": "code", "content": "print(1)"},
            {"type": "console", "content": "1", "format": "output"},
            {"type": "console", "end": True},
        ])

        chunks = list(terminal_interface(agent, message="run code"))
        assert len(chunks) == 4

    def test_non_interactive_exits_after_message(self):
        """Should exit after processing when not interactive."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "content": "Done"},
            {"type": "message", "end": True},
        ])

        list(terminal_interface(agent, message="test"))
        # Should not loop - test completes


class TestTerminalConfirmation:
    """Tests for confirmation handling."""

    def test_confirmation_prompts_user(self):
        """Should prompt user for confirmation."""
        agent = MagicMock()
        agent.messages = []
        agent.chat.return_value = iter([
            {"type": "code", "start": True, "format": "python"},
            {"type": "code", "content": "print('hi')"},
            {
                "type": "confirmation",
                "content": {"format": "python", "content": "print('hi')"}
            },
        ])

        with patch('builtins.input', return_value="n"):
            chunks = list(terminal_interface(agent, message="run"))

        # Should add declined message
        assert len(agent.messages) == 1
        assert "declined" in agent.messages[0]["content"].lower()

    def test_confirmation_accepts_y(self):
        """Should continue when user enters y."""
        agent = MagicMock()
        agent.messages = []
        agent.chat.return_value = iter([
            {"type": "confirmation", "content": {"format": "python", "content": "x=1"}},
            {"type": "console", "content": "", "format": "output"},
            {"type": "console", "end": True},
        ])

        with patch('builtins.input', return_value="y"):
            chunks = list(terminal_interface(agent, message="run"))

        # Should not add declined message
        assert len(agent.messages) == 0


class TestRunTerminal:
    """Tests for run_terminal function."""

    def test_consumes_all_chunks(self):
        """Should consume all chunks from terminal_interface."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "content": "Done"},
            {"type": "message", "end": True},
        ])

        run_terminal(agent, message="test")
        agent.chat.assert_called_once()


class TestInteractiveMode:
    """Tests for interactive mode."""

    def test_reads_from_input(self):
        """Should read messages from input in interactive mode."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "content": "Hi"},
            {"type": "message", "end": True},
        ])

        with patch('builtins.input', side_effect=["hello", KeyboardInterrupt]):
            list(terminal_interface(agent))

        agent.chat.assert_called_once()

    def test_skips_empty_input(self):
        """Should skip empty input lines."""
        agent = MagicMock()
        agent.chat.return_value = iter([
            {"type": "message", "start": True},
            {"type": "message", "end": True},
        ])

        with patch('builtins.input', side_effect=["", "", "hello", KeyboardInterrupt]):
            list(terminal_interface(agent))

        agent.chat.assert_called_once()

    def test_handles_keyboard_interrupt(self):
        """Should exit gracefully on KeyboardInterrupt."""
        agent = MagicMock()

        with patch('builtins.input', side_effect=KeyboardInterrupt):
            list(terminal_interface(agent))

        # Should not raise, should complete gracefully

    def test_handles_eof_error(self):
        """Should exit gracefully on EOFError (Ctrl-D)."""
        agent = MagicMock()

        with patch('builtins.input', side_effect=EOFError):
            list(terminal_interface(agent))
