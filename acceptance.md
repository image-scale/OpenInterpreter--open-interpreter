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
- [ ] Create LLMClient class that wraps LiteLLM for API calls
- [ ] Convert LMC format messages to OpenAI format for API requests
- [ ] Support streaming responses from LLM
- [ ] Define tool schema for code execution with language and code parameters
- [ ] Parse tool calls from LLM response to detect code blocks
- [ ] Yield message chunks with type="message" for regular text responses
- [ ] Yield code chunks with type="code" and format=language when tool is called
- [ ] Handle partial JSON parsing for streaming tool arguments
