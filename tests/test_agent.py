"""
Tests for the CodeAgent class.
"""

import pytest
from codeagent import CodeAgent


class TestCodeAgentInstantiation:
    """Tests for creating CodeAgent instances."""

    def test_create_with_defaults(self):
        """Agent can be created with default settings."""
        agent = CodeAgent()
        assert agent.model == "gpt-4o"
        assert agent.auto_run is False
        assert agent.verbose is False
        assert agent.max_output == 2800
        assert agent.messages == []
        assert agent.system_message is not None

    def test_create_with_custom_settings(self):
        """Agent can be created with custom settings."""
        agent = CodeAgent(
            model="gpt-3.5-turbo",
            auto_run=True,
            verbose=True,
            max_output=5000,
            temperature=0.5
        )
        assert agent.model == "gpt-3.5-turbo"
        assert agent.auto_run is True
        assert agent.verbose is True
        assert agent.max_output == 5000
        assert agent.temperature == 0.5

    def test_create_with_custom_system_message(self):
        """Agent can be created with custom system message."""
        custom_msg = "You are a helpful Python tutor."
        agent = CodeAgent(system_message=custom_msg)
        assert agent.system_message == custom_msg

    def test_create_with_initial_messages(self):
        """Agent can be created with initial message history."""
        initial = [
            {"role": "user", "type": "message", "content": "Hello"},
            {"role": "assistant", "type": "message", "content": "Hi there!"}
        ]
        agent = CodeAgent(messages=initial)
        assert len(agent.messages) == 2
        assert agent.messages[0]["content"] == "Hello"


class TestCodeAgentChat:
    """Tests for the chat functionality."""

    def test_chat_with_string_message(self):
        """chat() with string adds user message to history."""
        agent = CodeAgent()
        agent.chat("Hello, world!")

        assert len(agent.messages) == 1
        msg = agent.messages[0]
        assert msg["role"] == "user"
        assert msg["type"] == "message"
        assert msg["content"] == "Hello, world!"

    def test_chat_with_dict_message(self):
        """chat() with dict message uses it directly."""
        agent = CodeAgent()
        agent.chat({"role": "user", "type": "message", "content": "Test dict"})

        assert len(agent.messages) == 1
        msg = agent.messages[0]
        assert msg["role"] == "user"
        assert msg["content"] == "Test dict"

    def test_chat_with_dict_adds_default_role(self):
        """chat() with dict without role adds user role."""
        agent = CodeAgent()
        agent.chat({"type": "message", "content": "No role specified"})

        assert len(agent.messages) == 1
        assert agent.messages[0]["role"] == "user"

    def test_chat_with_list_replaces_history(self):
        """chat() with list replaces entire message history."""
        agent = CodeAgent()
        agent.chat("First message")

        new_history = [
            {"role": "user", "type": "message", "content": "New history"},
            {"role": "assistant", "type": "message", "content": "Response"}
        ]
        agent.chat(new_history)

        assert len(agent.messages) == 2
        assert agent.messages[0]["content"] == "New history"

    def test_chat_returns_new_messages(self):
        """chat() returns only new messages from this turn."""
        agent = CodeAgent()
        agent.chat("First message")
        result = agent.chat("Second message")

        # Result should only contain messages from this chat call
        # Since no LLM is integrated yet, result will be empty
        assert result == []


class TestCodeAgentReset:
    """Tests for the reset functionality."""

    def test_reset_clears_messages(self):
        """reset() clears the message history."""
        agent = CodeAgent()
        agent.chat("Hello")
        agent.chat("World")
        assert len(agent.messages) == 2

        agent.reset()
        assert agent.messages == []

    def test_reset_clears_state(self):
        """reset() resets internal state."""
        agent = CodeAgent()
        agent.chat("Test")
        agent.reset()

        assert agent._last_messages_count == 0
        assert agent._responding is False


class TestCodeAgentMultipleInstances:
    """Tests for multiple agent instances."""

    def test_instances_have_independent_messages(self):
        """Different instances maintain separate message histories."""
        agent1 = CodeAgent()
        agent2 = CodeAgent()

        agent1.chat("Message for agent 1")
        agent2.chat("Message for agent 2")

        assert len(agent1.messages) == 1
        assert len(agent2.messages) == 1
        assert agent1.messages[0]["content"] == "Message for agent 1"
        assert agent2.messages[0]["content"] == "Message for agent 2"

    def test_instances_have_independent_settings(self):
        """Different instances maintain separate settings."""
        agent1 = CodeAgent(model="gpt-4o")
        agent2 = CodeAgent(model="gpt-3.5-turbo")

        agent1.system_message = "Agent 1 system"
        agent2.system_message = "Agent 2 system"

        assert agent1.model == "gpt-4o"
        assert agent2.model == "gpt-3.5-turbo"
        assert agent1.system_message == "Agent 1 system"
        assert agent2.system_message == "Agent 2 system"


class TestMessageFormat:
    """Tests for LMC message format compliance."""

    def test_message_has_required_fields(self):
        """Messages have role, type, and content fields."""
        agent = CodeAgent()
        agent.chat("Test message")

        msg = agent.messages[0]
        assert "role" in msg
        assert "type" in msg
        assert "content" in msg

    def test_message_role_is_string(self):
        """Message role is a string."""
        agent = CodeAgent()
        agent.chat("Test")
        assert isinstance(agent.messages[0]["role"], str)

    def test_message_type_is_string(self):
        """Message type is a string."""
        agent = CodeAgent()
        agent.chat("Test")
        assert isinstance(agent.messages[0]["type"], str)

    def test_message_content_is_string(self):
        """Message content is a string."""
        agent = CodeAgent()
        agent.chat("Test")
        assert isinstance(agent.messages[0]["content"], str)
