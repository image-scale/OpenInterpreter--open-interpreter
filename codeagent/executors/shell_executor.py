"""
Shell code executor using subprocess.
"""

import os
import platform
import queue
import re
import subprocess
import threading
import time


class ShellExecutor:
    """
    Executes shell commands using a persistent subprocess.
    Captures stdout and stderr, streaming output incrementally.
    """

    END_MARKER = "##end_of_execution##"

    def __init__(self):
        self.process = None
        self._output_queue = queue.Queue()
        self._done = threading.Event()
        self._stop_flag = False

    def _get_shell_cmd(self):
        """Get the appropriate shell command for the platform."""
        if platform.system() == "Windows":
            return ["cmd.exe"]
        return [os.environ.get("SHELL", "bash")]

    def _ensure_process(self):
        """Start the shell process if not already running."""
        if self.process is not None:
            return

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        self.process = subprocess.Popen(
            self._get_shell_cmd(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            env=env,
            encoding="utf-8",
            errors="replace",
        )

        threading.Thread(
            target=self._read_stream,
            args=(self.process.stdout, False),
            daemon=True
        ).start()

        threading.Thread(
            target=self._read_stream,
            args=(self.process.stderr, True),
            daemon=True
        ).start()

    def _read_stream(self, stream, is_stderr):
        """Read from a stream and queue output."""
        try:
            for line in iter(stream.readline, ""):
                if self._stop_flag:
                    break

                if self.END_MARKER in line:
                    line = line.replace(self.END_MARKER, "").strip()
                    if line:
                        self._output_queue.put({
                            "type": "console",
                            "format": "output",
                            "content": line + "\n"
                        })
                    self._done.set()
                else:
                    if line:
                        self._output_queue.put({
                            "type": "console",
                            "format": "output",
                            "content": line
                        })
        except ValueError:
            pass

    def _preprocess_code(self, code):
        """Add end marker to code."""
        code = code.strip()
        code += f'\necho "{self.END_MARKER}"\n'
        return code

    def run(self, code):
        """
        Execute shell code and yield output chunks.

        Yields dicts in LMC format:
        - {"type": "console", "format": "output", "content": "..."}
        """
        self._ensure_process()
        self._stop_flag = False
        self._done.clear()

        code = self._preprocess_code(code)

        try:
            self.process.stdin.write(code)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            self._restart_process()
            self.process.stdin.write(code)
            self.process.stdin.flush()

        yield from self._capture_output()

    def _restart_process(self):
        """Restart the shell process."""
        self.terminate()
        self._ensure_process()

    def _capture_output(self):
        """Yield output from the queue until done."""
        while True:
            try:
                output = self._output_queue.get(timeout=0.1)
                yield output
            except queue.Empty:
                if self._done.is_set():
                    while not self._output_queue.empty():
                        yield self._output_queue.get()
                    break

    def stop(self):
        """Stop the currently running command."""
        self._stop_flag = True
        self._done.set()

    def terminate(self):
        """Terminate the shell process."""
        self._stop_flag = True
        self._done.set()
        if self.process:
            try:
                self.process.terminate()
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
            except Exception:
                pass
        self.process = None
