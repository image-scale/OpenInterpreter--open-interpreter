"""
Tests for the Shell executor.
"""

import pytest
from codeagent.executors import ShellExecutor


class TestShellExecutorBasics:
    """Basic tests for Shell executor."""

    def test_executor_can_be_created(self):
        """ShellExecutor can be instantiated."""
        executor = ShellExecutor()
        assert executor is not None
        assert executor.process is None

    def test_executor_starts_process_on_run(self):
        """Shell process is started when code is first run."""
        executor = ShellExecutor()
        try:
            list(executor.run("echo hello"))
            assert executor.process is not None
        finally:
            executor.terminate()


class TestShellExecutorOutput:
    """Tests for output capture."""

    @pytest.fixture
    def executor(self):
        """Provide a Shell executor that cleans up after."""
        ex = ShellExecutor()
        yield ex
        ex.terminate()

    def test_captures_echo_output(self, executor):
        """Captures stdout from echo command."""
        outputs = list(executor.run("echo hello"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "hello" in combined

    def test_captures_command_result(self, executor):
        """Captures output from command execution."""
        outputs = list(executor.run("expr 2 + 2"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "4" in combined

    def test_captures_error_output(self, executor):
        """Captures stderr from failed commands."""
        outputs = list(executor.run("ls /nonexistent_directory_12345"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "No such file" in combined or "cannot access" in combined

    def test_captures_multiline_script(self, executor):
        """Captures output from multi-line scripts."""
        code = """
echo first
echo second
echo third
"""
        outputs = list(executor.run(code))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "first" in combined
        assert "second" in combined
        assert "third" in combined


class TestShellExecutorOutputFormat:
    """Tests for output format compliance."""

    @pytest.fixture
    def executor(self):
        """Provide a Shell executor that cleans up after."""
        ex = ShellExecutor()
        yield ex
        ex.terminate()

    def test_output_has_required_fields(self, executor):
        """Output chunks have type, format, content fields."""
        outputs = list(executor.run("echo test"))

        for output in outputs:
            assert "type" in output
            assert "content" in output
            if output["type"] == "console":
                assert "format" in output

    def test_console_output_format(self, executor):
        """Console output has format='output'."""
        outputs = list(executor.run("echo test"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        for output in console_outputs:
            assert output["format"] == "output"


class TestShellExecutorState:
    """Tests for shell state management."""

    @pytest.fixture
    def executor(self):
        """Provide a Shell executor that cleans up after."""
        ex = ShellExecutor()
        yield ex
        ex.terminate()

    def test_shell_persists_state(self, executor):
        """Environment variables persist across executions."""
        list(executor.run("export TESTVAR=hello"))
        outputs = list(executor.run("echo $TESTVAR"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "hello" in combined

    def test_working_directory_persists(self, executor):
        """Working directory persists across executions."""
        list(executor.run("cd /tmp"))
        outputs = list(executor.run("pwd"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "/tmp" in combined


class TestShellExecutorTerminate:
    """Tests for termination."""

    def test_terminate_clears_process(self):
        """terminate() clears the process reference."""
        executor = ShellExecutor()
        list(executor.run("echo hello"))
        assert executor.process is not None

        executor.terminate()
        assert executor.process is None

    def test_can_run_after_terminate(self):
        """Can run commands again after terminate."""
        executor = ShellExecutor()
        try:
            list(executor.run("echo first"))
            executor.terminate()
            outputs = list(executor.run("echo second"))

            console_outputs = [o for o in outputs if o["type"] == "console"]
            combined = "".join(o["content"] for o in console_outputs)
            assert "second" in combined
        finally:
            executor.terminate()


class TestShellExecutorStop:
    """Tests for stop functionality."""

    def test_stop_sets_flag(self):
        """stop() sets the stop flag."""
        executor = ShellExecutor()
        try:
            executor._ensure_process()
            executor.stop()
            assert executor._stop_flag is True
        finally:
            executor.terminate()
