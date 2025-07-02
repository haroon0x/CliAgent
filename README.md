# CliAgent

**CliAgent** is a powerful, extensible command-line and Python tool for automating Python code understanding and transformation tasks. It leverages advanced LLMs to generate docstrings, summaries, type annotations, tests, bug detection, refactoring, and more—all from your terminal or scripts.

---

## 🚀 Features
- **Docstring Generation**: Automatically generate Google-style docstrings for your Python functions.
- **Code Summarization**: Get concise summaries of your code files.
- **Type Annotation**: Add or update type annotations in your code.
- **Test Generation**: Generate unit tests for your code automatically.
- **Bug Detection**: Analyze code for potential bugs and issues.
- **Refactoring**: Suggest and apply code refactorings.
- **Multi-step Flows**: Orchestrate complex code workflows using natural language instructions.
- **Chat & CLI Modes**: Use in interactive chat mode or as a one-shot CLI tool.

---

## 🤖 Powered by Alchemyst AI
- **Model**: Uses the `alchemyst-ai/alchemyst-c1` model for all agentic code tasks.
- **Provider**: [getalchemystai.com](https://getalchemystai.com)
- **Why Alchemyst?**: Purpose-built for code, with high accuracy and reliability for Python automation and analysis.

---

## 📦 Installation

```bash
# Clone the repository
 git clone https://github.com/YOUR_USERNAME/CliAgent.git
 cd CliAgent

# Install in editable/development mode
 python -m pip install -e .
```

> **Requirements:** Python 3.11+

---

## 🛠️ CLI Usage

CliAgent provides a flexible command-line interface with multiple agent types and options. Below is a comprehensive guide to all CLI commands and options.

### Basic Syntax

```bash
cliagent [OPTIONS]
```

### Main Options

| Option                        | Description                                                        | Example                          |
|-------------------------------|--------------------------------------------------------------------|----------------------------------|
| `--file`, `-f <file>`         | Python file to process                                             | `--file myscript.py`             |
| `--agent`, `-a <type>`        | Type of agent to use (see below)                                   | `--agent doc`                    |
| `--output`, `-o <mode>`       | Output mode: `console`, `in-place`, `new-file` (default: console)  | `--output in-place`              |
| `--llm <provider>`            | LLM provider: `alchemyst` (only option currently supported)        | `--llm alchemyst`                |
| `--enhanced`                  | Use enhanced flow with safety checks and user approval             | `--enhanced`                     |
| `--chat`                      | Start interactive chat mode                                        | `--chat`                         |
| `--verbose`, `-v`             | Enable verbose output                                              | `--verbose`                      |
| `--no-confirm`                | Skip user confirmation prompts                                     | `--no-confirm`                   |
| `--migration-target <target>` | Target for code migration (default: Python 3)                      | `--migration-target Python 3.12`  |

### Agent Types

| Agent Type   | Description                                  |
|--------------|----------------------------------------------|
| `doc`        | Generate docstrings for functions/classes     |
| `summary`    | Summarize the code file                      |
| `test`       | Generate unit tests                          |
| `bug`        | Detect bugs and issues                       |
| `refactor`   | Suggest and apply code refactorings          |
| `type`       | Add or update type annotations               |
| `migration`  | Migrate code to a new version or library     |

### Example Commands

```bash
# Generate docstrings for a file (output to console)
cliagent --file myscript.py --agent doc

# Summarize a file and write to a new file
cliagent --file myscript.py --agent summary --output new-file

# Generate unit tests and write in-place (with safety checks)
cliagent --file myscript.py --agent test --output in-place --enhanced

# Detect bugs in a file (verbose mode)
cliagent --file myscript.py --agent bug --verbose

# Refactor code and skip confirmation prompts
cliagent --file myscript.py --agent refactor --no-confirm

# Add type annotations using OpenAI as the LLM provider
cliagent --file myscript.py --agent type --llm openai

# Migrate code to Python 3.12
cliagent --file myscript.py --agent migration --migration-target Python 3.12

# Start interactive chat mode
cliagent --chat
```

### Help

To see all available options at any time, run:

```bash
cliagent --help
```

---

## 🛠️ Python Usage

You can also use CliAgent programmatically:

```python
from cliagent.main import main

# You can invoke the main entry point programmatically
main()
```

---

## ⚙️ Configuration & Instructions
- **Model**: By default, CliAgent uses the `alchemyst-ai/alchemyst-c1` model. You can configure your API key and endpoint via environment variables or CLI flags if needed.
- **Instructions**: For best results, provide clear instructions or select the appropriate agent type (doc, summary, test, bug, refactor, type, migration).
- **Project Structure**: See the `docs/` folder for design, implementation, and usage guides.

---

## 🌐 More Information
- **Website**: [getalchemystai.com](https://getalchemystai.com)
- **Docs**: See the `docs/` directory for detailed guides and architecture.
- **Issues**: Please report bugs or feature requests via GitHub Issues.
- **Related Projects**: Check out [alchemyst-ai/awesome-saas](https://github.com/alchemyst-ai/awesome-saas) for more Alchemyst AI templates and resources.

---

## 🤝 Contributing

Contributions are welcome! To get started:
1. Fork the repo and create your branch (`git checkout -b feature/your-feature`)
2. Make your changes and add tests
3. Run the test suite: `python -m pytest tests/`
4. Submit a pull request

---

## 📂 Project Structure

```
CliAgent/
├── src/cliagent/           # Main package code
├── tests/                  # Test suite
├── docs/                   # Documentation and design
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Build and project metadata
└── README.md               # This file
```


