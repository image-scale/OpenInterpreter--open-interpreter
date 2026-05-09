"""
Python code executor using Jupyter kernel.
"""

import queue
import re
import threading
import time

from jupyter_client import KernelManager


class PythonExecutor:
    """
    Executes Python code using a Jupyter kernel.
    Captures stdout, stderr, and display data.
    """

    def __init__(self):
        self.km = None
        self.kc = None
        self._stop_flag = False
        self._listener_thread = None
        self._message_queue = None

    def _ensure_kernel(self):
        """Start the kernel if not already running."""
        if self.km is not None:
            return

        self.km = KernelManager(kernel_name="python3")
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()

        while not self.kc.is_alive():
            time.sleep(0.1)
        time.sleep(0.3)

    def run(self, code):
        """
        Execute Python code and yield output chunks.

        Yields dicts in LMC format:
        - {"type": "console", "format": "output", "content": "..."}
        - {"type": "image", "format": "base64.png", "content": "..."}
        """
        self._ensure_kernel()
        self._stop_flag = False
        self._message_queue = queue.Queue()

        self._start_listener()
        self.kc.execute(code)

        yield from self._capture_output()

    def _start_listener(self):
        """Start background thread to listen for kernel messages."""
        def listener():
            while not self._stop_flag:
                try:
                    msg = self.kc.iopub_channel.get_msg(timeout=0.1)
                    self._process_message(msg)

                    if (msg["header"]["msg_type"] == "status" and
                            msg["content"]["execution_state"] == "idle"):
                        self._stop_flag = True
                        return
                except queue.Empty:
                    continue
                except Exception:
                    continue

        self._listener_thread = threading.Thread(target=listener, daemon=True)
        self._listener_thread.start()

    def _process_message(self, msg):
        """Process a kernel message and queue output."""
        msg_type = msg["msg_type"]
        content = msg["content"]

        if msg_type == "stream":
            text = content.get("text", "")
            if text:
                self._message_queue.put({
                    "type": "console",
                    "format": "output",
                    "content": text
                })

        elif msg_type == "error":
            traceback = "\n".join(content.get("traceback", []))
            traceback = self._strip_ansi(traceback)
            self._message_queue.put({
                "type": "console",
                "format": "output",
                "content": traceback
            })

        elif msg_type in ["display_data", "execute_result"]:
            data = content.get("data", {})

            if "image/png" in data:
                self._message_queue.put({
                    "type": "image",
                    "format": "base64.png",
                    "content": data["image/png"]
                })
            elif "image/jpeg" in data:
                self._message_queue.put({
                    "type": "image",
                    "format": "base64.jpeg",
                    "content": data["image/jpeg"]
                })
            elif "text/html" in data:
                self._message_queue.put({
                    "type": "code",
                    "format": "html",
                    "content": data["text/html"]
                })
            elif "text/plain" in data:
                self._message_queue.put({
                    "type": "console",
                    "format": "output",
                    "content": data["text/plain"]
                })

    def _strip_ansi(self, text):
        """Remove ANSI color codes from text."""
        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

    def _capture_output(self):
        """Yield output from the message queue."""
        while True:
            try:
                output = self._message_queue.get(timeout=0.1)
                yield output
            except queue.Empty:
                if self._stop_flag:
                    while not self._message_queue.empty():
                        yield self._message_queue.get()
                    break

    def stop(self):
        """Stop the currently running code."""
        self._stop_flag = True
        if self.km:
            self.km.interrupt_kernel()

    def terminate(self):
        """Terminate the kernel."""
        self._stop_flag = True
        if self.kc:
            self.kc.stop_channels()
        if self.km:
            self.km.shutdown_kernel()
        self.km = None
        self.kc = None
