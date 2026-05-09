"""
Tests for the respond loop.
"""

import pytest
from unittest.mock import MagicMock, patch

from codeagent import CodeAgent
from codeagent.respond import (
    respond,
    truncate_output,
    get_executor_for_language,
)


class TestTruncateOutput:
    """Tests for output truncation."""

    def test_short_output_not_truncated(self):
        """Short output is returned as-is."""
        result = truncate_output("hello", 100)
        assert result == "hello"

    def test_long_output_truncated(self):
        """Long output is truncated with indicator."""
        output = "x" * 200
        result = truncate_output(output, 100)
        assert len(result) < len(output)
        assert "[output truncated]" in result

    def test_truncated_has_start_and_end(self):
        """Truncated output contains start and end of original."""
        output = "START" + "x" * 200 + "END"
        result = truncate_output(output, 100)
        assert result.startswith("START")
        assert result.endswith("END")


class TestGetExecutorForLanguage:
    """Tests for executor selection."""

    def test_python_executor(self):
        """Gets Python executor for python language."""
        executors = {}
        executor = get_executor_for_language("python", executors)
        assert executor is not None
        assert "python" in executors
        executor.terminate()

    def test_python_alias_py(self):
        """Gets Python executor for 'py' alias."""
        executors = {}
        executor = get_executor_for_language("py", executors)
        assert executor is not None
        executor.terminate()

    def test_shell_executor(self):
        """Gets Shell executor for shell language."""
        executors = {}
        executor = get_executor_for_language("shell", executors)
        assert executor is not None
        assert "shell" in executors
        executor.terminate()

    def test_shell_alias_bash(self):
        """Gets Shell executor for 'bash' alias."""
        executors = {}
        executor = get_executor_for_language("bash", executors)
        assert executor is not None
        executor.terminate()

    def test_unknown_language_returns_none(self):
        """Unknown language returns None."""
        executors = {}
        executor = get_executor_for_language("unknown", executors)
        assert executor is None

    def test_reuses_existing_executor(self):
        """Reuses existing executor for same language."""
        executors = {}
        executor1 = get_executor_for_language("python", executors)
        executor2 = get_executor_for_language("python", executors)
        assert executor1 is executor2
        executor1.terminate()


class TestRespondLoop:
    """Tests for the respond loop."""

    def test_yields_message_chunks(self):
        """respond yields message chunks from LLM."""
        agent = CodeAgent()
        agent.messages = [{"role": "user", "type": "message", "content": "Hi"}]

        agent.llm.run = MagicMock(return_value=iter([
            {"type": "message", "content": "Hello!"}
        ]))

        chunks = list(respond(agent))

        assert len(chunks) == 1
        assert chunks[0]["role"] == "assistant"
        assert chunks[0]["type"] == "message"
        assert chunks[0]["content"] == "Hello!"

    def test_adds_message_to_history(self):
        """respond adds assistant message to history."""
        agent = CodeAgent()
        agent.messages = [{"role": "user", "type": "message", "content": "Hi"}]

        agent.llm.run = MagicMock(return_value=iter([
            {"type": "message", "content": "Hello!"}
        ]))

        list(respond(agent))

        assert len(agent.messages) == 2
        assert agent.messages[1]["role"] == "assistant"
        assert agent.messages[1]["content"] == "Hello!"

    def test_yields_code_chunks(self):
        """respond yields code chunks from LLM."""
        agent = CodeAgent(auto_run=True)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "python", "content": "print('hi')"}]),
            iter([{"type": "message", "content": "Done"}])
        ])

        chunks = list(respond(agent))

        code_chunks = [c for c in chunks if c.get("type") == "code"]
        assert len(code_chunks) > 0
        assert code_chunks[0]["format"] == "python"

    def test_executes_code_and_yields_output(self):
        """respond executes code and yields output chunks."""
        agent = CodeAgent(auto_run=True)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "python", "content": "print('hello')"}]),
            iter([{"type": "message", "content": "Done"}])
        ])

        chunks = list(respond(agent))

        console_chunks = [c for c in chunks if c.get("type") == "console"]
        assert len(console_chunks) > 0
        combined = "".join(c.get("content", "") for c in console_chunks)
        assert "hello" in combined

    def test_yields_confirmation_when_not_auto_run(self):
        """respond yields confirmation chunk when auto_run is False."""
        agent = CodeAgent(auto_run=False)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "python", "content": "x = 1"}]),
            iter([{"type": "message", "content": "Done"}])
        ])

        chunks = list(respond(agent))

        confirmation_chunks = [c for c in chunks if c.get("type") == "confirmation"]
        assert len(confirmation_chunks) == 1

    def test_adds_output_to_messages(self):
        """respond adds execution output to message history."""
        agent = CodeAgent(auto_run=True)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "python", "content": "print('output')"}]),
            iter([{"type": "message", "content": "Done"}])
        ])

        list(respond(agent))

        computer_msgs = [m for m in agent.messages if m["role"] == "computer"]
        assert len(computer_msgs) > 0
        combined = "".join(m.get("content", "") for m in computer_msgs)
        assert "output" in combined

    def test_truncates_long_output(self):
        """respond truncates long output in messages."""
        agent = CodeAgent(auto_run=True, max_output=100)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        long_output_code = "print('x' * 500)"
        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "python", "content": long_output_code}]),
            iter([{"type": "message", "content": "Done"}])
        ])

        list(respond(agent))

        computer_msgs = [m for m in agent.messages if m["role"] == "computer"]
        for msg in computer_msgs:
            assert len(msg.get("content", "")) <= 200

    def test_handles_unsupported_language(self):
        """respond handles unsupported language gracefully."""
        agent = CodeAgent(auto_run=True)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        agent.llm.run = MagicMock(side_effect=[
            iter([{"type": "code", "format": "cobol", "content": "DISPLAY 'HI'"}]),
            iter([{"type": "message", "content": "OK"}])
        ])

        chunks = list(respond(agent))

        console_chunks = [c for c in chunks if c.get("type") == "console"]
        combined = "".join(c.get("content", "") for c in console_chunks)
        assert "not supported" in combined.lower()

    def test_loops_until_no_code(self):
        """respond continues loop until LLM responds without code."""
        agent = CodeAgent(auto_run=True)
        agent.messages = [{"role": "user", "type": "message", "content": "Run code"}]

        call_count = [0]
        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return iter([{"type": "code", "format": "python", "content": "x = 1"}])
            elif call_count[0] == 2:
                return iter([{"type": "code", "format": "python", "content": "y = 2"}])
            else:
                return iter([{"type": "message", "content": "All done!"}])

        agent.llm.run = mock_run

        list(respond(agent))

        assert call_count[0] == 3
