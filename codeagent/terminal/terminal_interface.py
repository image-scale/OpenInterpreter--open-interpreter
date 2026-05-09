"""
Terminal interface for interactive REPL with CodeAgent.
"""

try:
    import readline
except ImportError:
    readline = None

from .components import MessageBlock, CodeBlock


def terminal_interface(agent, message=None):
    """
    Run an interactive terminal interface for the agent.

    Args:
        agent: A CodeAgent instance
        message: Optional initial message to send

    Yields:
        Message chunks from the agent
    """
    interactive = message is None

    while True:
        if interactive:
            try:
                message = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break

            if not message:
                continue

            if readline:
                try:
                    readline.add_history(message)
                except Exception:
                    pass

        active_block = None

        try:
            for chunk in agent.chat(message, display=False, stream=True):
                yield chunk

                if chunk["type"] == "confirmation":
                    if active_block:
                        active_block.refresh(cursor=False)
                        active_block.end()
                        active_block = None

                    code_info = chunk["content"]
                    language = code_info.get("format", "")
                    code = code_info.get("content", "")

                    response = input("  Run this code? (y/n): ").strip().lower()
                    print()

                    if response == "y":
                        active_block = CodeBlock()
                        active_block.margin_top = False
                        active_block.language = language
                        active_block.code = code
                    else:
                        agent.messages.append({
                            "role": "user",
                            "type": "message",
                            "content": "I declined to run this code.",
                        })
                        break

                if chunk["type"] == "message":
                    if "start" in chunk:
                        active_block = MessageBlock()

                    if "content" in chunk:
                        active_block.message += chunk["content"]
                        active_block.refresh()

                    if "end" in chunk and active_block:
                        active_block.refresh(cursor=False)
                        active_block.end()
                        active_block = None

                elif chunk["type"] == "code":
                    if "start" in chunk:
                        active_block = CodeBlock()
                        active_block.language = chunk.get("format", "")

                    if "content" in chunk:
                        active_block.code += chunk["content"]
                        active_block.refresh()

                elif chunk["type"] == "console":
                    if "content" in chunk and chunk.get("format") == "output":
                        if active_block and hasattr(active_block, "output"):
                            active_block.output += "\n" + chunk["content"]
                            active_block.output = active_block.output.strip()
                            active_block.refresh()

                    if "end" in chunk and active_block:
                        active_block.refresh(cursor=False)
                        active_block.end()
                        active_block = None

            if active_block:
                active_block.end()
                active_block = None

            if not interactive:
                break

        except KeyboardInterrupt:
            if active_block:
                active_block.end()
                active_block = None

            if interactive:
                print()
                continue
            else:
                break

        message = None


def run_terminal(agent, message=None):
    """
    Run the terminal interface, consuming all chunks.

    Args:
        agent: A CodeAgent instance
        message: Optional initial message to send
    """
    for _ in terminal_interface(agent, message=message):
        pass
