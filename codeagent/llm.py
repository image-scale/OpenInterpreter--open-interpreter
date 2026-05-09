"""
LLM client that handles communication with language models via LiteLLM.
"""

import json
import re

import litellm

litellm.suppress_debug_info = True


CODE_EXECUTION_TOOL = {
    "type": "function",
    "function": {
        "name": "execute",
        "description": "Executes code on the user's machine and returns the output",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "The programming language to use",
                    "enum": ["python", "shell", "bash", "javascript"],
                },
                "code": {
                    "type": "string",
                    "description": "The code to execute",
                },
            },
            "required": ["language", "code"],
        },
    },
}


def convert_to_openai_messages(lmc_messages, system_message=None):
    """
    Convert LMC format messages to OpenAI API format.

    LMC format: {"role": "user/assistant/computer", "type": "message/code/console", "content": "..."}
    OpenAI format: {"role": "user/assistant/system/tool", "content": "..."}
    """
    openai_messages = []

    if system_message:
        openai_messages.append({"role": "system", "content": system_message})

    for msg in lmc_messages:
        role = msg.get("role", "user")
        msg_type = msg.get("type", "message")
        content = msg.get("content", "")

        if role == "user":
            openai_messages.append({"role": "user", "content": content})
        elif role == "assistant":
            if msg_type == "message":
                openai_messages.append({"role": "assistant", "content": content})
            elif msg_type == "code":
                language = msg.get("format", "python")
                openai_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_code",
                        "type": "function",
                        "function": {
                            "name": "execute",
                            "arguments": json.dumps({"language": language, "code": content})
                        }
                    }]
                })
        elif role == "computer":
            if msg_type == "console":
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": "call_code",
                    "content": content
                })

    return openai_messages


def parse_partial_json(s):
    """
    Try to parse partial JSON from streaming response.
    Returns parsed dict or None if not valid JSON yet.
    """
    s = s.strip()
    if not s:
        return None

    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    if not s.startswith("{"):
        return None

    depth = 0
    in_string = False
    escape = False

    for i, c in enumerate(s):
        if escape:
            escape = False
            continue
        if c == '\\' and in_string:
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1

    if depth > 0:
        s += '"' * in_string + '}' * depth
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass

    return None


class LLMClient:
    """
    Client for communicating with LLMs via LiteLLM.
    Handles message conversion, streaming, and tool calling.
    """

    def __init__(self, agent):
        self.agent = agent
        self.supported_languages = ["python", "shell", "bash", "javascript"]

    def run(self, messages, system_message=None):
        """
        Send messages to LLM and yield response chunks.

        Yields dicts in format:
        - {"type": "message", "content": "..."} for text responses
        - {"type": "code", "format": "python", "content": "..."} for code blocks
        """
        openai_messages = convert_to_openai_messages(messages, system_message)

        tool = CODE_EXECUTION_TOOL.copy()
        tool["function"]["parameters"]["properties"]["language"]["enum"] = self.supported_languages

        params = {
            "model": self.agent.model,
            "messages": openai_messages,
            "tools": [tool],
            "stream": True,
            "temperature": self.agent.temperature,
        }

        accumulated_args = ""
        language = None
        code = ""
        in_tool_call = False

        try:
            for chunk in litellm.completion(**params):
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if hasattr(delta, "content") and delta.content:
                    if not in_tool_call:
                        yield {"type": "message", "content": delta.content}

                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    in_tool_call = True
                    for tool_call in delta.tool_calls:
                        if tool_call.function and tool_call.function.arguments:
                            accumulated_args += tool_call.function.arguments

                            parsed = parse_partial_json(accumulated_args)
                            if parsed:
                                if language is None and "language" in parsed and "code" in parsed:
                                    language = parsed["language"]

                                if language and "code" in parsed:
                                    new_code = parsed["code"]
                                    if len(new_code) > len(code):
                                        code_delta = new_code[len(code):]
                                        code = new_code
                                        yield {
                                            "type": "code",
                                            "format": language,
                                            "content": code_delta
                                        }
        except Exception as e:
            yield {"type": "error", "content": str(e)}
