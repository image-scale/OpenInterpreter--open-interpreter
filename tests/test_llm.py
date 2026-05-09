"""
Tests for the LLM client module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from codeagent import CodeAgent
from codeagent.llm import (
    LLMClient,
    convert_to_openai_messages,
    parse_partial_json,
    CODE_EXECUTION_TOOL,
)


class TestMessageConversion:
    """Tests for converting LMC messages to OpenAI format."""

    def test_convert_user_message(self):
        """User messages are converted correctly."""
        lmc_messages = [
            {"role": "user", "type": "message", "content": "Hello"}
        ]
        result = convert_to_openai_messages(lmc_messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    def test_convert_assistant_message(self):
        """Assistant text messages are converted correctly."""
        lmc_messages = [
            {"role": "assistant", "type": "message", "content": "Hi there!"}
        ]
        result = convert_to_openai_messages(lmc_messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hi there!"

    def test_convert_with_system_message(self):
        """System message is prepended when provided."""
        lmc_messages = [
            {"role": "user", "type": "message", "content": "Hello"}
        ]
        result = convert_to_openai_messages(lmc_messages, system_message="You are helpful.")

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful."
        assert result[1]["role"] == "user"

    def test_convert_code_message(self):
        """Code messages are converted to tool calls."""
        lmc_messages = [
            {"role": "assistant", "type": "code", "format": "python", "content": "print('hi')"}
        ]
        result = convert_to_openai_messages(lmc_messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert "tool_calls" in result[0]
        assert result[0]["tool_calls"][0]["function"]["name"] == "execute"

        args = json.loads(result[0]["tool_calls"][0]["function"]["arguments"])
        assert args["language"] == "python"
        assert args["code"] == "print('hi')"

    def test_convert_computer_output(self):
        """Computer console output is converted to tool response."""
        lmc_messages = [
            {"role": "computer", "type": "console", "content": "Output text"}
        ]
        result = convert_to_openai_messages(lmc_messages)

        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["content"] == "Output text"

    def test_convert_conversation_flow(self):
        """Full conversation is converted correctly."""
        lmc_messages = [
            {"role": "user", "type": "message", "content": "Run hello world"},
            {"role": "assistant", "type": "code", "format": "python", "content": "print('Hello')"},
            {"role": "computer", "type": "console", "content": "Hello"},
            {"role": "assistant", "type": "message", "content": "Done!"},
        ]
        result = convert_to_openai_messages(lmc_messages, system_message="Be helpful")

        assert len(result) == 5
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert "tool_calls" in result[2]
        assert result[3]["role"] == "tool"
        assert result[4]["role"] == "assistant"
        assert result[4]["content"] == "Done!"


class TestPartialJsonParsing:
    """Tests for parsing partial JSON from streaming responses."""

    def test_parse_complete_json(self):
        """Complete JSON is parsed correctly."""
        result = parse_partial_json('{"language": "python", "code": "x = 1"}')
        assert result == {"language": "python", "code": "x = 1"}

    def test_parse_partial_json_incomplete_value(self):
        """Partial JSON with incomplete string is handled."""
        result = parse_partial_json('{"language": "python", "code": "print(')
        assert result is not None
        assert result["language"] == "python"
        assert "code" in result

    def test_parse_partial_json_missing_brace(self):
        """Partial JSON with missing closing brace is handled."""
        result = parse_partial_json('{"language": "python"')
        assert result is not None
        assert result["language"] == "python"

    def test_parse_empty_string(self):
        """Empty string returns None."""
        result = parse_partial_json("")
        assert result is None

    def test_parse_whitespace_only(self):
        """Whitespace-only string returns None."""
        result = parse_partial_json("   ")
        assert result is None

    def test_parse_invalid_json(self):
        """Invalid JSON returns None."""
        result = parse_partial_json("not json at all")
        assert result is None


class TestCodeExecutionTool:
    """Tests for the code execution tool schema."""

    def test_tool_has_required_structure(self):
        """Tool schema has required OpenAI structure."""
        assert CODE_EXECUTION_TOOL["type"] == "function"
        assert "function" in CODE_EXECUTION_TOOL
        assert "name" in CODE_EXECUTION_TOOL["function"]
        assert "parameters" in CODE_EXECUTION_TOOL["function"]

    def test_tool_has_execute_function(self):
        """Tool defines execute function."""
        assert CODE_EXECUTION_TOOL["function"]["name"] == "execute"

    def test_tool_has_language_and_code_params(self):
        """Tool has language and code as required parameters."""
        params = CODE_EXECUTION_TOOL["function"]["parameters"]
        assert "language" in params["properties"]
        assert "code" in params["properties"]
        assert "language" in params["required"]
        assert "code" in params["required"]


class TestLLMClient:
    """Tests for the LLMClient class."""

    def test_client_is_created_with_agent(self):
        """LLMClient is created when CodeAgent is initialized."""
        agent = CodeAgent()
        assert hasattr(agent, "llm")
        assert isinstance(agent.llm, LLMClient)
        assert agent.llm.agent is agent

    def test_client_has_supported_languages(self):
        """LLMClient has list of supported languages."""
        agent = CodeAgent()
        assert "python" in agent.llm.supported_languages
        assert "shell" in agent.llm.supported_languages

    @patch("codeagent.llm.litellm.completion")
    def test_run_yields_message_chunks(self, mock_completion):
        """run() yields message chunks from LLM response."""
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Hello"
        mock_chunk.choices[0].delta.tool_calls = None
        mock_completion.return_value = iter([mock_chunk])

        agent = CodeAgent()
        messages = [{"role": "user", "type": "message", "content": "Hi"}]

        chunks = list(agent.llm.run(messages))

        assert len(chunks) == 1
        assert chunks[0]["type"] == "message"
        assert chunks[0]["content"] == "Hello"

    @patch("codeagent.llm.litellm.completion")
    def test_run_yields_code_chunks(self, mock_completion):
        """run() yields code chunks when tool is called."""
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = None
        mock_chunk1.choices[0].delta.tool_calls = [MagicMock()]
        mock_chunk1.choices[0].delta.tool_calls[0].function.arguments = '{"language": "python", "code": "x'

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = None
        mock_chunk2.choices[0].delta.tool_calls = [MagicMock()]
        mock_chunk2.choices[0].delta.tool_calls[0].function.arguments = ' = 1"}'

        mock_completion.return_value = iter([mock_chunk1, mock_chunk2])

        agent = CodeAgent()
        messages = [{"role": "user", "type": "message", "content": "Set x to 1"}]

        chunks = list(agent.llm.run(messages))

        code_chunks = [c for c in chunks if c["type"] == "code"]
        assert len(code_chunks) > 0
        assert code_chunks[0]["format"] == "python"

    @patch("codeagent.llm.litellm.completion")
    def test_run_handles_errors(self, mock_completion):
        """run() yields error chunk on exception."""
        mock_completion.side_effect = Exception("API Error")

        agent = CodeAgent()
        messages = [{"role": "user", "type": "message", "content": "Hi"}]

        chunks = list(agent.llm.run(messages))

        assert len(chunks) == 1
        assert chunks[0]["type"] == "error"
        assert "API Error" in chunks[0]["content"]


class TestLLMClientIntegration:
    """Integration tests for LLMClient with CodeAgent."""

    def test_agent_model_is_passed_to_llm(self):
        """Agent model setting is used by LLM client."""
        agent = CodeAgent(model="gpt-3.5-turbo")
        assert agent.llm.agent.model == "gpt-3.5-turbo"

    def test_agent_temperature_is_passed_to_llm(self):
        """Agent temperature setting is used by LLM client."""
        agent = CodeAgent(temperature=0.7)
        assert agent.llm.agent.temperature == 0.7
