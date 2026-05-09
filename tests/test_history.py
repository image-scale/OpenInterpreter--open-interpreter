"""
Tests for conversation history management.
"""

import json
import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from codeagent.history import (
    sanitize_filename,
    generate_conversation_filename,
    ensure_directory,
    save_conversation,
    load_conversation,
    list_conversations,
)
from codeagent import CodeAgent


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_removes_invalid_characters(self):
        """Should remove characters invalid in filenames."""
        result = sanitize_filename('hello<>:"/\\|?*!world')
        assert result == "helloworld"

    def test_replaces_whitespace_with_underscore(self):
        """Should replace spaces with underscores."""
        result = sanitize_filename("hello world there")
        assert result == "hello_world_there"

    def test_truncates_to_max_length(self):
        """Should truncate to max_length."""
        result = sanitize_filename("a" * 50, max_length=30)
        assert len(result) == 30

    def test_custom_max_length(self):
        """Should respect custom max_length."""
        result = sanitize_filename("hello world", max_length=5)
        assert result == "hello"

    def test_strips_leading_trailing_whitespace(self):
        """Should strip whitespace before processing."""
        result = sanitize_filename("  hello  ")
        assert result == "hello"

    def test_empty_string(self):
        """Should handle empty string."""
        result = sanitize_filename("")
        assert result == ""

    def test_removes_newlines(self):
        """Should remove newlines and carriage returns."""
        result = sanitize_filename("hello\nworld\r")
        assert result == "helloworld"


class TestGenerateConversationFilename:
    """Tests for generate_conversation_filename function."""

    def test_generates_filename_with_date(self):
        """Should include date in filename."""
        result = generate_conversation_filename("Hello world")
        assert "__" in result
        assert result.endswith(".json")

    def test_uses_first_words_as_prefix(self):
        """Should use words from first message as prefix."""
        result = generate_conversation_filename("Hello world there")
        assert result.startswith("Hello_world")

    def test_truncates_long_content(self):
        """Should truncate very long first messages."""
        long_content = "a" * 100
        result = generate_conversation_filename(long_content)
        # Should be limited in length
        assert len(result) < 100

    def test_sanitizes_prefix(self):
        """Should sanitize invalid characters in prefix."""
        result = generate_conversation_filename("Hello?World!")
        assert "?" not in result
        assert "!" not in result

    def test_single_word_message(self):
        """Should handle single word message."""
        result = generate_conversation_filename("Hello")
        assert result.startswith("Hello")
        assert result.endswith(".json")


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_new_directory(self):
        """Should create directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "subdir", "nested")
            ensure_directory(new_path)
            assert os.path.exists(new_path)

    def test_handles_existing_directory(self):
        """Should not fail if directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_directory(tmpdir)
            assert os.path.exists(tmpdir)


class TestSaveAndLoadConversation:
    """Tests for save_conversation and load_conversation functions."""

    def test_save_and_load_messages(self):
        """Should save and load messages correctly."""
        messages = [
            {"role": "user", "type": "message", "content": "Hello"},
            {"role": "assistant", "type": "message", "content": "Hi there"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            save_conversation(messages, filepath)
            loaded = load_conversation(filepath)
            assert loaded == messages

    def test_creates_directory_if_needed(self):
        """Should create parent directory if it doesn't exist."""
        messages = [{"role": "user", "type": "message", "content": "Test"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "test.json")
            save_conversation(messages, filepath)
            assert os.path.exists(filepath)

    def test_preserves_unicode(self):
        """Should handle unicode content correctly."""
        messages = [
            {"role": "user", "type": "message", "content": "Hello 你好 👋"}
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "unicode.json")
            save_conversation(messages, filepath)
            loaded = load_conversation(filepath)
            assert loaded[0]["content"] == "Hello 你好 👋"

    def test_saves_pretty_json(self):
        """Should save as indented JSON for readability."""
        messages = [{"role": "user", "type": "message", "content": "Test"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "pretty.json")
            save_conversation(messages, filepath)
            with open(filepath, 'r') as f:
                content = f.read()
            # Pretty printed JSON has newlines
            assert "\n" in content


class TestListConversations:
    """Tests for list_conversations function."""

    def test_lists_json_files(self):
        """Should list all JSON files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            for name in ["conv1.json", "conv2.json"]:
                filepath = os.path.join(tmpdir, name)
                with open(filepath, 'w') as f:
                    json.dump([], f)

            result = list_conversations(tmpdir)
            assert len(result) == 2
            filenames = [r['filename'] for r in result]
            assert "conv1.json" in filenames
            assert "conv2.json" in filenames

    def test_ignores_non_json_files(self):
        """Should ignore non-JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["conv.json", "readme.txt", "data.csv"]:
                filepath = os.path.join(tmpdir, name)
                with open(filepath, 'w') as f:
                    f.write("test")

            result = list_conversations(tmpdir)
            assert len(result) == 1
            assert result[0]['filename'] == "conv.json"

    def test_returns_empty_for_nonexistent_directory(self):
        """Should return empty list if directory doesn't exist."""
        result = list_conversations("/nonexistent/path")
        assert result == []

    def test_sorted_by_modified_time_descending(self):
        """Should return files sorted by modification time, newest first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import time
            # Create files with slight delay
            for i, name in enumerate(["old.json", "new.json"]):
                filepath = os.path.join(tmpdir, name)
                with open(filepath, 'w') as f:
                    json.dump([], f)
                if i == 0:
                    time.sleep(0.1)

            result = list_conversations(tmpdir)
            # Newest should be first
            assert result[0]['filename'] == "new.json"
            assert result[1]['filename'] == "old.json"

    def test_includes_filepath_and_modified(self):
        """Should include filepath and modified time in results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            with open(filepath, 'w') as f:
                json.dump([], f)

            result = list_conversations(tmpdir)
            assert result[0]['filepath'] == filepath
            assert isinstance(result[0]['modified'], datetime)


class TestCodeAgentHistorySettings:
    """Tests for CodeAgent conversation history settings."""

    def test_conversation_history_disabled_by_default(self):
        """Should have conversation_history disabled by default."""
        agent = CodeAgent()
        assert agent.conversation_history is False

    def test_enable_conversation_history(self):
        """Should allow enabling conversation history."""
        agent = CodeAgent(conversation_history=True)
        assert agent.conversation_history is True

    def test_default_history_path(self):
        """Should have default history path."""
        agent = CodeAgent()
        assert ".codeagent" in agent.conversation_history_path
        assert "conversations" in agent.conversation_history_path

    def test_custom_history_path(self):
        """Should allow custom history path."""
        agent = CodeAgent(conversation_history_path="/custom/path")
        assert agent.conversation_history_path == "/custom/path"

    def test_conversation_filename_initially_none(self):
        """Should start with no filename."""
        agent = CodeAgent()
        assert agent.conversation_filename is None

    def test_reset_clears_filename(self):
        """Reset should clear conversation filename."""
        agent = CodeAgent()
        agent.conversation_filename = "test.json"
        agent.reset()
        assert agent.conversation_filename is None


class TestCodeAgentHistoryOperations:
    """Tests for CodeAgent conversation history operations."""

    def test_load_history_sets_messages(self):
        """Should load messages from file."""
        messages = [
            {"role": "user", "type": "message", "content": "Hello"},
            {"role": "assistant", "type": "message", "content": "Hi"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            save_conversation(messages, filepath)

            agent = CodeAgent()
            agent.load_history(filepath)
            assert agent.messages == messages
            assert agent.conversation_filename == "test.json"

    def test_save_history_creates_file(self):
        """Should save messages to file when history enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=True,
                conversation_history_path=tmpdir,
                offline=True,
            )
            agent.messages = [
                {"role": "user", "type": "message", "content": "Hello world"}
            ]
            agent._save_history()

            # Check file was created
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert files[0].endswith(".json")

    def test_save_history_generates_filename(self):
        """Should generate filename from first message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=True,
                conversation_history_path=tmpdir,
            )
            agent.messages = [
                {"role": "user", "type": "message", "content": "Test message"}
            ]
            agent._save_history()

            assert agent.conversation_filename is not None
            assert "Test" in agent.conversation_filename

    def test_save_history_preserves_existing_filename(self):
        """Should use existing filename if set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=True,
                conversation_history_path=tmpdir,
                conversation_filename="existing.json",
            )
            agent.messages = [
                {"role": "user", "type": "message", "content": "Hello"}
            ]
            agent._save_history()

            assert agent.conversation_filename == "existing.json"
            assert os.path.exists(os.path.join(tmpdir, "existing.json"))

    def test_save_history_no_messages(self):
        """Should not save if no messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=True,
                conversation_history_path=tmpdir,
            )
            agent._save_history()

            files = os.listdir(tmpdir)
            assert len(files) == 0

    def test_chat_saves_history_when_enabled(self):
        """Chat should save history when conversation_history is True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=True,
                conversation_history_path=tmpdir,
                offline=True,
            )
            # Mock respond to do nothing
            with patch("codeagent.agent.respond") as mock_respond:
                mock_respond.return_value = iter([])
                agent.chat("Hello")

            files = os.listdir(tmpdir)
            assert len(files) == 1

    def test_chat_does_not_save_when_disabled(self):
        """Chat should not save history when conversation_history is False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                conversation_history=False,
                conversation_history_path=tmpdir,
                offline=True,
            )
            with patch("codeagent.agent.respond") as mock_respond:
                mock_respond.return_value = iter([])
                agent.chat("Hello")

            files = os.listdir(tmpdir)
            assert len(files) == 0
