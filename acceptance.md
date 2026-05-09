# Acceptance Criteria

## Task 1: Main Interpreter Class

### Acceptance Criteria
- [ ] Create CodeAgent class that can be instantiated with default settings
- [ ] Support configurable properties: model, auto_run, verbose, max_output, system_message, messages
- [ ] chat(message) method accepts string messages and appends them to messages list with role="user"
- [ ] chat(message) method accepts dict messages with explicit role/type/content
- [ ] chat() without arguments should work (for later interactive use)
- [ ] reset() method clears messages list
- [ ] Multiple instances have independent message histories
- [ ] messages list stores messages in LMC format: {"role": "...", "type": "...", "content": "..."}
