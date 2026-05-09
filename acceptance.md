# Acceptance Criteria

## Task 1: Main Interpreter Class

### Acceptance Criteria
- [x] Create CodeAgent class that can be instantiated with default settings
- [x] Support configurable properties: model, auto_run, verbose, max_output, system_message, messages
- [x] chat(message) method accepts string messages and appends them to messages list with role="user"
- [x] chat(message) method accepts dict messages with explicit role/type/content
- [x] chat() without arguments should work (for later interactive use)
- [x] reset() method clears messages list
- [x] Multiple instances have independent message histories
- [x] messages list stores messages in LMC format: {"role": "...", "type": "...", "content": "..."}

## Task 2: LLM Communication

### Acceptance Criteria
- [x] Create LLMClient class that wraps LiteLLM for API calls
- [x] Convert LMC format messages to OpenAI format for API requests
- [x] Support streaming responses from LLM
- [x] Define tool schema for code execution with language and code parameters
- [x] Parse tool calls from LLM response to detect code blocks
- [x] Yield message chunks with type="message" for regular text responses
- [x] Yield code chunks with type="code" and format=language when tool is called
- [x] Handle partial JSON parsing for streaming tool arguments

## Task 3: Python Code Execution

### Acceptance Criteria
- [x] Create PythonExecutor class that manages a Jupyter kernel
- [x] Start kernel on first code execution
- [x] Execute code and capture stdout output
- [x] Execute code and capture stderr output
- [x] Capture display data (images, HTML) from execution
- [x] Stream output incrementally as it's produced
- [x] Yield results in LMC format with type="console", format="output"
- [x] Support stopping running code
- [x] Support terminating the kernel

## Task 4: Shell Code Execution

### Acceptance Criteria
- [x] Create ShellExecutor class that manages a subprocess
- [x] Start shell process on first code execution
- [x] Execute shell commands and capture stdout
- [x] Capture stderr output
- [x] Support multi-line scripts
- [x] Detect when execution completes via end marker
- [x] Stream output incrementally as it's produced
- [x] Yield results in LMC format with type="console", format="output"
- [x] Support stopping running commands
- [x] Support terminating the shell process

## Task 5: Respond Loop

### Acceptance Criteria
- [ ] Create respond function that orchestrates the LLM-code-output loop
- [ ] Send messages to LLM and yield response chunks
- [ ] Detect when LLM response includes code blocks
- [ ] Execute detected code using appropriate executor (Python or Shell)
- [ ] Capture execution output and add to messages
- [ ] Feed output back to LLM for continuation
- [ ] Continue loop until LLM responds without code
- [ ] Support auto_run mode that skips confirmation
- [ ] Truncate long outputs to max_output setting
