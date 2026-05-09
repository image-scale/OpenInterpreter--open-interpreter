"""
Tests for the Python executor.
"""

import pytest
from codeagent.executors import PythonExecutor


class TestPythonExecutorBasics:
    """Basic tests for Python executor."""

    def test_executor_can_be_created(self):
        """PythonExecutor can be instantiated."""
        executor = PythonExecutor()
        assert executor is not None
        assert executor.km is None

    def test_executor_starts_kernel_on_run(self):
        """Kernel is started when code is first run."""
        executor = PythonExecutor()
        try:
            list(executor.run("x = 1"))
            assert executor.km is not None
            assert executor.kc is not None
        finally:
            executor.terminate()


class TestPythonExecutorOutput:
    """Tests for output capture."""

    @pytest.fixture
    def executor(self):
        """Provide a Python executor that cleans up after."""
        ex = PythonExecutor()
        yield ex
        ex.terminate()

    def test_captures_print_output(self, executor):
        """Captures stdout from print statements."""
        outputs = list(executor.run("print('hello')"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "hello" in combined

    def test_captures_expression_result(self, executor):
        """Captures result of evaluated expressions."""
        outputs = list(executor.run("1 + 1"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "2" in combined

    def test_captures_error_output(self, executor):
        """Captures error traceback."""
        outputs = list(executor.run("raise ValueError('test error')"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        combined = "".join(o["content"] for o in console_outputs)
        assert "ValueError" in combined
        assert "test error" in combined

    def test_captures_multiple_prints(self, executor):
        """Captures multiple print statements."""
        code = """
print('first')
print('second')
print('third')
"""
        outputs = list(executor.run(code))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "first" in combined
        assert "second" in combined
        assert "third" in combined


class TestPythonExecutorOutputFormat:
    """Tests for output format compliance."""

    @pytest.fixture
    def executor(self):
        """Provide a Python executor that cleans up after."""
        ex = PythonExecutor()
        yield ex
        ex.terminate()

    def test_output_has_required_fields(self, executor):
        """Output chunks have type, format, content fields."""
        outputs = list(executor.run("print('test')"))

        for output in outputs:
            assert "type" in output
            assert "content" in output
            if output["type"] == "console":
                assert "format" in output

    def test_console_output_format(self, executor):
        """Console output has format='output'."""
        outputs = list(executor.run("print('test')"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        assert len(console_outputs) > 0
        for output in console_outputs:
            assert output["format"] == "output"


class TestPythonExecutorState:
    """Tests for kernel state management."""

    @pytest.fixture
    def executor(self):
        """Provide a Python executor that cleans up after."""
        ex = PythonExecutor()
        yield ex
        ex.terminate()

    def test_kernel_persists_state(self, executor):
        """Variables persist across executions."""
        list(executor.run("x = 42"))
        outputs = list(executor.run("print(x)"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "42" in combined

    def test_imports_persist(self, executor):
        """Imports persist across executions."""
        list(executor.run("import math"))
        outputs = list(executor.run("print(math.pi)"))

        console_outputs = [o for o in outputs if o["type"] == "console"]
        combined = "".join(o["content"] for o in console_outputs)
        assert "3.14" in combined


class TestPythonExecutorTerminate:
    """Tests for termination."""

    def test_terminate_clears_kernel(self):
        """terminate() clears the kernel reference."""
        executor = PythonExecutor()
        list(executor.run("x = 1"))
        assert executor.km is not None

        executor.terminate()
        assert executor.km is None
        assert executor.kc is None

    def test_can_run_after_terminate(self):
        """Can run code again after terminate."""
        executor = PythonExecutor()
        try:
            list(executor.run("x = 1"))
            executor.terminate()
            outputs = list(executor.run("print('new kernel')"))

            console_outputs = [o for o in outputs if o["type"] == "console"]
            combined = "".join(o["content"] for o in console_outputs)
            assert "new kernel" in combined
        finally:
            executor.terminate()


class TestPythonExecutorStop:
    """Tests for stop functionality."""

    def test_stop_sets_flag(self):
        """stop() sets the stop flag."""
        executor = PythonExecutor()
        try:
            executor._ensure_kernel()
            executor.stop()
            assert executor._stop_flag is True
        finally:
            executor.terminate()
