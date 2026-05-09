"""
The main CodeAgent class that orchestrates LLM communication and code execution.
"""

import getpass
import platform


def get_default_system_message():
    """Generate the default system message with user context."""
    return f"""You are CodeAgent, a helpful AI assistant that can execute code on the user's machine.
When you need to perform a task, you can write and execute code in Python or Shell.
The user has given you permission to execute code. Execute code when needed to accomplish tasks.

User: {getpass.getuser()}
System: {platform.system()}"""


class CodeAgent:
    """
    An LLM-powered agent that can execute code to accomplish tasks.

    The agent maintains a conversation history, sends messages to an LLM,
    and can execute code blocks from the LLM's responses.
    """

    def __init__(
        self,
        model="gpt-4o",
        auto_run=False,
        verbose=False,
        max_output=2800,
        system_message=None,
        messages=None,
        offline=False,
        temperature=0.0,
    ):
        # LLM settings
        self.model = model
        self.temperature = temperature

        # Execution settings
        self.auto_run = auto_run
        self.verbose = verbose
        self.max_output = max_output
        self.offline = offline

        # System message
        self.system_message = system_message if system_message else get_default_system_message()

        # Conversation state
        self.messages = messages if messages is not None else []
        self._responding = False
        self._last_messages_count = 0

    def chat(self, message=None, display=True, stream=False):
        """
        Send a message to the agent and get a response.

        Args:
            message: The message to send. Can be:
                - str: converted to user message
                - dict: used directly (must have role, type, content)
                - list: replaces entire message history
                - None: for interactive mode (future use)
            display: Whether to display output (for terminal interface)
            stream: Whether to return a streaming generator

        Returns:
            If stream=False: List of new messages added during this chat
            If stream=True: Generator yielding message chunks
        """
        self._responding = True

        try:
            if stream:
                return self._streaming_chat(message, display)

            # Non-streaming: consume the generator
            for _ in self._streaming_chat(message, display):
                pass

            self._responding = False
            return self.messages[self._last_messages_count:]

        except Exception:
            self._responding = False
            raise

    def _streaming_chat(self, message, display):
        """
        Internal streaming chat implementation.
        """
        if message is not None:
            self._add_message(message)
            self._last_messages_count = len(self.messages)

        # For now, yield nothing - LLM integration comes in Task 2
        return
        yield  # Make this a generator

    def _add_message(self, message):
        """
        Add a message to the conversation history.
        """
        if isinstance(message, str):
            self.messages.append({
                "role": "user",
                "type": "message",
                "content": message
            })
        elif isinstance(message, dict):
            if "role" not in message:
                message = {**message, "role": "user"}
            self.messages.append(message)
        elif isinstance(message, list):
            self.messages = message
        else:
            raise TypeError(f"Message must be str, dict, or list, not {type(message)}")

    def reset(self):
        """
        Clear the conversation history and reset state.
        """
        self.messages = []
        self._last_messages_count = 0
        self._responding = False

    @property
    def responding(self):
        """Whether the agent is currently processing a response."""
        return self._responding
