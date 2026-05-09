# Goal

## Project
open-interpreter — a python project.

## Description
A CLI tool and Python library that allows LLMs to execute code locally on the user's machine. It provides a ChatGPT-like natural language interface to your computer's capabilities, enabling users to create files, run scripts, analyze data, and more by chatting with an AI assistant. The assistant can write and execute code in multiple languages (Python, Shell, JavaScript) and stream the output back to the user.

## Scope
- Core interpreter class with chat functionality
- LLM integration via LiteLLM for multiple model support  
- Code execution engine supporting Python (via Jupyter kernel) and Shell (via subprocess)
- Streaming response system with LMC message format
- Conversation history management
- Terminal interface for interactive use
- Configurable settings (auto_run, verbose, max_output, etc.)
- Multiple language support architecture
