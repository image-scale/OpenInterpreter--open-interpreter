"""
The respond loop that orchestrates the LLM-code-output cycle.
"""

from .executors import PythonExecutor, ShellExecutor


def truncate_output(output, max_length):
    """Truncate output to max length, adding indicator if truncated."""
    if len(output) <= max_length:
        return output
    half = max_length // 2
    return output[:half] + "\n\n... [output truncated] ...\n\n" + output[-half:]


def get_executor_for_language(language, executors):
    """Get or create executor for the given language."""
    language = language.lower()

    if language in ("python", "py"):
        if "python" not in executors:
            executors["python"] = PythonExecutor()
        return executors["python"]

    if language in ("shell", "bash", "sh", "zsh"):
        if "shell" not in executors:
            executors["shell"] = ShellExecutor()
        return executors["shell"]

    return None


def respond(agent):
    """
    The main response loop. Yields chunks as the agent responds.

    This function:
    1. Sends messages to the LLM
    2. Yields text response chunks
    3. When code is detected, executes it
    4. Captures output and adds to messages
    5. Continues until LLM responds without code
    """
    executors = {}

    try:
        while True:
            code_detected = False
            accumulated_code = ""
            code_language = None
            accumulated_message = ""

            for chunk in agent.llm.run(agent.messages, agent.system_message):
                chunk_type = chunk.get("type")

                if chunk_type == "message":
                    accumulated_message += chunk.get("content", "")
                    yield {"role": "assistant", **chunk}

                elif chunk_type == "code":
                    code_detected = True
                    code_language = chunk.get("format", "python")
                    accumulated_code += chunk.get("content", "")
                    yield {"role": "assistant", **chunk}

                elif chunk_type == "error":
                    yield {"role": "assistant", "type": "message", "content": f"Error: {chunk.get('content', '')}"}
                    return

            if accumulated_message:
                agent.messages.append({
                    "role": "assistant",
                    "type": "message",
                    "content": accumulated_message
                })

            if not code_detected:
                break

            agent.messages.append({
                "role": "assistant",
                "type": "code",
                "format": code_language,
                "content": accumulated_code
            })

            if not agent.auto_run:
                yield {
                    "role": "computer",
                    "type": "confirmation",
                    "format": "execution",
                    "content": {
                        "type": "code",
                        "format": code_language,
                        "content": accumulated_code
                    }
                }

            executor = get_executor_for_language(code_language, executors)
            if executor is None:
                output = f"Language '{code_language}' is not supported."
                agent.messages.append({
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": output
                })
                yield {"role": "computer", "type": "console", "format": "output", "content": output}
                continue

            accumulated_output = ""
            for output_chunk in executor.run(accumulated_code):
                yield {"role": "computer", **output_chunk}
                if output_chunk.get("type") == "console":
                    accumulated_output += output_chunk.get("content", "")

            truncated_output = truncate_output(accumulated_output, agent.max_output)
            agent.messages.append({
                "role": "computer",
                "type": "console",
                "format": "output",
                "content": truncated_output
            })

    finally:
        for executor in executors.values():
            try:
                executor.terminate()
            except Exception:
                pass
