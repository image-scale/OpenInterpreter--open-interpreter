# Todo

## Plan
Build the interpreter from the user-facing API inward. Start with the main Interpreter class that users interact with, then add LLM communication, then code execution. Each feature delivers working functionality that can be tested independently.

## Tasks
- [x] Task 1: Create the main Interpreter class with chat functionality, message handling, and configurable settings. Users should be able to create an interpreter instance, configure it (model, auto_run, verbose, etc.), and call chat() to start a conversation. Messages are stored in the interpreter.messages list.

- [x] Task 2: Implement LLM communication using LiteLLM that converts messages to OpenAI format, sends requests to the LLM, and streams responses. The LLM component should support tool calling to detect when the model wants to execute code, returning structured chunks with type (message/code) and content.

- [x] Task 3: Add Python code execution via Jupyter kernel that runs code and yields streaming output. The executor should start a kernel, execute code blocks, capture stdout/stderr/display data, and return results in LMC format with type=console.

- [>] Task 4: Add Shell code execution via subprocess that spawns a persistent shell process and streams output. It should handle both single commands and multi-line scripts, detecting when execution completes.

- [ ] Task 5: Implement the respond loop that orchestrates the conversation - sending messages to LLM, detecting code blocks, executing code, capturing output, and feeding results back to the LLM until no more code needs to run.

- [ ] Task 6: Add conversation history persistence that saves conversations to JSON files and allows loading previous conversations. Include filename generation from first message content and date.

- [ ] Task 7: Create a terminal interface that provides an interactive REPL for chatting with the interpreter, with rich markdown display, code block highlighting, and user input handling.
