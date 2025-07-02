# Project Specification: The Code Documentation Agent

---

## 1. Project Overview

**Project Name:** The Code Documentation Agent

**Objective:** This project aims to build an intelligent agent that automates the creation of high-quality, Google-style docstrings for Python functions. The agent will read source code, understand what each function does, leverage an AI proxy to interact with a Large Language Model (LLM), and then either display the generated docstrings or insert them directly into the source file. This tool directly tackles the common developer issue of outdated or missing code documentation, ultimately reducing technical debt, making code easier to maintain, and smoothing team onboarding.

**Target User:** Python developers and engineering teams.

**Expected Outcome:** A robust, user-friendly command-line tool that seamlessly integrates into a developer's existing workflow.

---

## 2. Agentic Design Principles

This project is built upon fundamental agentic principles:

* **Perception:** The agent will accurately read and parse Python source code files, specifically identifying function definitions and extracting their complete source code.
* **Thinking:** It will utilize a powerful LLM to analyze the extracted function code, infer its purpose, parameters, and return values, then synthesize this understanding into a structured docstring.
* **Action:** The agent will present the generated docstring to the user, with an optional capability to directly modify the source file by inserting the docstring.
* **Environment Interaction:** The agent interacts with the file system (reading source files, potentially writing modified files) and an external LLM service via a custom proxy.

---

## 3. Technical Requirements & Architecture

### 3.1 Core Components

1.  **Command-Line Interface (CLI):** Handles user input and arguments using `argparse`.
2.  **Code Parser:** Uses Python's `ast` module for robust source code parsing and function extraction.
3.  **LLM Interaction Module:** A custom `alchemist_ai_proxy` (defined in `call_llm.py`) for abstracting LLM calls.
4.  **Agent Framework:** PocketFlow will orchestrate the agent's perception, thinking, and action phases.
5.  **Docstring Formatter:** Ensures generated docstrings strictly adhere to Google-style guidelines.

### 3.2 Detailed Component Specifications

#### 3.2.1 Command-Line Interface (CLI)

* **Library:** `argparse` (standard Python library).
* **Arguments:**
    * `--file <filepath>` (Required): The path to the Python source file you want to document.
    * `--output <mode>` (Optional, Default: `console`): Defines how the agent presents the results.
        * `console`: Prints the original function code followed by the generated docstring to standard output.
        * `in-place`: Modifies the original file by inserting docstrings. **Crucially, this mode will create a backup of the original file (e.g., `filename.py.bak`) before any modification.**
        * `new-file`: Writes the documented code to a completely new file (e.g., `filename_documented.py`).
    * `--llm <model_name>` (Optional, Default: `gpt-4o`): Specifies the LLM model to use (e.g., `gpt-4o`, `claude-3-haiku-20240307`). This value will be passed directly to the `alchemist_ai_proxy`.
    * `--no-confirm` (Optional, Default: `False`): If present, the agent will proceed with `in-place` or `new-file` output modes without asking for user confirmation for each function.
    * `--verbose` (Optional, Default: `False`): If present, the agent will print detailed progress messages during its execution.
* **Error Handling:** Implement robust error handling for scenarios such as:
    * File not found.
    * Invalid file extension (only `.py` files are accepted).
    * Parsing errors (e.g., `SyntaxError` when `ast` encounters invalid Python syntax).
    * LLM API errors (e.g., network connection issues, authentication failures, rate limiting).

#### 3.2.2 Code Parser (Perception)

* **Library:** `ast` (standard Python library).
* **Functionality:**
    1.  Reads the entire content of the specified Python file.
    2.  Uses `ast.parse()` to construct the Abstract Syntax Tree (AST) from the file content.
    3.  Traverses the AST using `ast.walk()` to systematically identify all `ast.FunctionDef` nodes.
    4.  For each `FunctionDef` node identified:
        * Extracts the **function name** (`node.name`).
        * Determines the **precise start and end line numbers** of the function definition, ensuring all elements like decorators and the `def` statement are included.
        * Extracts the **full source code** of the function (including decorators, signature, and body), crucially maintaining its original indentation. The preferred method for this is `ast.get_source_segment(source_code, node)` (available in Python 3.9+). If this is not available, a robust manual extraction based on line numbers and file content should be implemented.
        * Identifies if an **existing docstring** is present. While the LLM will be prompted to *replace* it, its presence should be noted.
* **Output:** A list of dictionaries. Each dictionary will represent a function and contain the following keys:
    * `'name'`: `str` - The name of the function.
    * `'source_code'`: `str` - The full source code of the function.
    * `'start_line'`: `int` - The starting line number of the function definition.
    * `'end_line'`: `int` - The ending line number of the function definition.
    * `'indentation'`: `str` - The leading whitespace (indentation) of the function's `def` line.

#### 3.2.3 LLM Interaction Module (`alchemist_ai_proxy` in `call_llm.py`)

* **Purpose:** To provide a unified, abstracted interface for interacting with various LLM providers (e.g., OpenAI, Anthropic). This module encapsulates API calls and prompt formatting.
* **File:** `call_llm.py`
* **Class/Function:** A class named `AlchemistAIProxy` will contain a method, for example, `generate_docstring(function_code: str, model_name: str) -> str`.
* **Dependencies:** Specific LLM client libraries such as `openai` (for GPT models) and `anthropic` (for Claude models).
* **Configuration:** API keys for LLM services **must** be loaded from environment variables (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) to ensure security and flexibility.
* **Error Handling:** Implement robust `try-except` blocks to manage potential API call failures, including network issues, authentication errors, and rate limit exceptions.
* **Prompt Engineering (within `generate_docstring` method):** The prompt is meticulously crafted to guide the LLM to produce high-quality, Google-style docstrings.

    ```python
    prompt = f"""You are an expert Python programmer specialized in documentation. Your task is to analyze the following Python function and generate a professional, comprehensive, and accurate Google-style docstring for it.

    Your response MUST ONLY contain the docstring text. Do NOT include any other text, code, or explanations. The docstring should immediately follow the triple quotes.

    The docstring must adhere strictly to the Google style guide and include the following sections where applicable:

    1.  A concise one-line summary of the function's purpose.
    2.  A more detailed, multi-line description of what the function does, including any important context or algorithm details.
    3.  `Args:`: List each argument with its type hint and a clear description.
        Example:
            `param_name (param_type): Description of the parameter.`
    4.  `Returns:`: Describe the return value, its type hint, and what it represents.
        Example:
            `return_value_type: Description of the return value.`
    5.  `Raises:`: (If applicable) Describe any exceptions that the function might raise.
        Example:
            `ValueError: If the input is invalid.`
    6.  `Yields:`: (If applicable) Describe any values yielded by a generator function.
    7.  `Note:`: (Optional) Any important notes or caveats.
    8.  `Examples:`: (Highly Recommended) One or more clear code examples demonstrating how to use the function. Use `>>>` for interactive examples.

    Ensure correct indentation and formatting. For boolean arguments, explain what `True` and `False` signify. For arguments with default values, mention them in the description.

    Here is the Python function to document:

    ```python
    {function_code}
    ```
    """
    ```
* **LLM Parameters:** The following parameters will be used for LLM calls to ensure deterministic and focused output:
    * `temperature`: `0.2` (for factual and less creative responses).
    * `top_p`: `0.9`.
    * `max_tokens`: An appropriate value (e.g., `512-1024`) to allow for detailed docstrings without excessive length.

#### 3.2.4 Agent Framework (PocketFlow)

* **Integration:** The main script (`doc_agent.py`) will orchestrate the entire documentation workflow by leveraging PocketFlow's capabilities.
* **Agent Definition:** A `DocAgent` class will be defined, likely inheriting from a PocketFlow `Agent` base class or similar pattern, to encapsulate the agent's logic.
* **Workflow Orchestration (`run` Method):** The `DocAgent`'s primary execution method (`run`) will perform the following steps:
    1.  **Initialization:** The `DocAgent` will be initialized with an instance of `AlchemistAIProxy` and the parsed CLI arguments.
    2.  **Function Data Retrieval:** It will call the Code Parser to obtain a list of function data from the target file.
    3.  **Iterative Docstring Generation (Thinking):** The agent will loop through each identified function. For every function:
        * It will invoke `AlchemistAIProxy.generate_docstring()` with the function's source code and the selected LLM model.
        * The `AlchemistAIProxy` will handle the communication with the LLM API and return the generated docstring.
    4.  **Docstring Integration (Action):** Based on the `--output` mode specified by the user:
        * **`console` mode:** The agent will print the original function's source code followed by the newly generated docstring to standard output.
        * **`in-place` / `new-file` modes:**
            * The agent will meticulously manipulate the file content to insert the generated docstring. This involves reading the file line by line, identifying the function's `def` line, inserting the docstring (correctly wrapped in `"""` or `'''`) with the appropriate indentation immediately after the `def` line, and then continuing with the rest of the function's body and the file's content.
            * It will ensure the generated docstring is correctly indented to match the function's existing indentation level.
            * If a docstring already exists for a function, the new one will seamlessly replace it.
            * For `in-place` mode, a crucial **backup mechanism** (`.bak` file) will be implemented before overwriting the original file.
            * For `new-file` mode, the modified content will be written to a newly named file (e.g., `my_module_documented.py`).
            * If the `--no-confirm` flag is *not* set, the agent will prompt the user for confirmation before applying changes for each function in destructive modes.

### 3.3 Project Structure

── doc_agent.py              # The main script, orchestrating the agent using PocketFlow
├── call_llm.py               # Contains the AlchemistAIProxy class for LLM interactions
├── README.md                 # Project description, setup, and usage instructions
├── requirements.txt          # Lists all Python dependencies
└── tests/                    # Directory for unit and integration tests (recommended)
├── test_doc_agent.py
└── test_call_llm.py

### 3.4 Dependencies

The following Python libraries will be required:

* `argparse` (built-in)
* `ast` (built-in)
* `os` (built-in)
* `shutil` (built-in, for file operations like backups)
* `pocketflow` (The chosen agent framework; specific version to be confirmed based on availability)
* `openai` (for interacting with OpenAI's LLMs)
* `anthropic` (for interacting with Anthropic's LLMs)
* `python-dotenv` (Highly recommended for loading environment variables from a `.env` file during local development)

---

## 4. Workflow (Sequence of Operations)

1.  **User Execution:** A developer initiates the agent from the command line, for example: `python doc_agent.py --file my_module.py --output in-place`.
2.  **CLI Argument Parsing:** `argparse` processes the command-line arguments, extracting the file path, output mode, and LLM preference.
3.  **Agent Initialization:** The `DocAgent` instance is created, configured with the provided arguments, and an `AlchemistAIProxy` instance is instantiated.
4.  **File Reading:** The agent opens and reads the entire content of `my_module.py`.
5.  **AST Parsing:** The `ast` module parses the file content, building a comprehensive Abstract Syntax Tree.
6.  **Function Identification:** The agent traverses the AST to locate all `FunctionDef` nodes. For each node, it extracts its name, exact source code, and its indentation level.
7.  **Iterative Docstring Generation (Thinking):**
    * For each function's extracted source code:
        * The agent calls `alchemist_ai_proxy.generate_docstring(function_code, model_name)`.
        * The `AlchemistAIProxy` constructs the detailed prompt and sends it to the specified LLM API.
        * The LLM processes the request and responds with *only* the generated Google-style docstring text.
        * The `AlchemistAIProxy` returns this docstring to the `DocAgent`.
8.  **Docstring Integration (Action):** The agent performs its action based on the chosen `--output` mode:
    * **If `--output console`:** The agent prints the original function code followed by the newly generated docstring to the standard output.
    * **If `--output in-place`:**
        * A backup of `my_module.py` (e.g., `my_module.py.bak`) is created.
        * The agent reads `my_module.py` line by line.
        * Upon encountering the `def` line of a function, it inserts the generated docstring (with correct indentation and triple quotes) immediately after this line.
        * The agent continues reading and appending the rest of the original file's content.
        * The complete, modified content is then written back to `my_module.py`.
        * (If `--no-confirm` is not set) The user is prompted for confirmation for each function before modification.
    * **If `--output new-file`:**
        * The same docstring insertion logic as `in-place` mode is applied.
        * The modified code is then written to a new file named `my_module_documented.py`.

---

## 5. Error Handling and Edge Cases

Robust error handling is crucial for a reliable tool:

* **Empty File:** The agent should gracefully handle input files that are empty.
* **No Functions Found:** If no function definitions are detected in the file, the user should be informed.
* **Syntax Errors:** `ast.parse` will raise a `SyntaxError` for invalid Python code. This error should be caught, and a user-friendly message explaining the syntax issue should be provided.
* **LLM API Failures:** Implement comprehensive `try-except` blocks for LLM API calls. This includes handling network errors, authentication issues (e.g., invalid API key), and rate limiting. For transient errors, consider implementing **retries with exponential backoff**. Persistent errors should be logged clearly.
* **Existing Docstrings:** The LLM prompt is designed for replacement. The agent's file manipulation logic **must** correctly identify and replace any existing docstring, including its triple-quote delimiters, rather than merely inserting a new one.
* **Complex Function Signatures:** The `ast` module should inherently handle various function signature complexities (e.g., `*args`, `**kwargs`, type hints, default values). The agent must ensure the extracted source code passed to the LLM includes these correctly.
* **Indentation Issues:** This is a critical point for Python code. The agent **must** accurately determine and apply the function's existing indentation level to the generated docstring to ensure the output code is valid Python.

---

## 6. Testing Strategy

A multi-faceted testing approach will ensure the agent's quality and reliability:

* **Unit Tests:**
    * **`call_llm.py`:** Test the `AlchemistAIProxy`'s ability to correctly format prompts and simulate receiving responses from the LLM (by **mocking** actual LLM API calls).
    * **Code Parser:** Test the parser with a variety of sample Python files to confirm that functions are correctly identified, their exact source code is extracted, and their indentation is accurately determined.
    * **Docstring Insertion Logic:** Thoroughly test the mechanism responsible for inserting docstrings into file content, covering different scenarios such as functions with and without existing docstrings, and varying indentation levels.
* **Integration Tests:**
    * Run the complete CLI tool against a suite of diverse sample Python files.
    * Verify the quality and format of the generated docstrings.
    * Confirm the correctness of file modifications (`in-place` and `new-file` modes), including backup creation.
* **Regression Tests:** Implement tests to ensure that new features or bug fixes do not inadvertently introduce regressions to existing, working functionality.

---

## 7. Future Enhancements (Beyond Initial Scope)

While the initial project focuses on the core functionality, several valuable enhancements could be considered for future iterations:

* **Support for Classes and Methods:** Extend the `ast` parsing to identify and document methods within `ast.ClassDef` nodes.
* **Multi-Language Support:** Generalize the agent to handle documentation for other programming languages, which would require different parsers and LLM prompt adjustments.
* **Custom Docstring Formats:** Allow users to specify preferred docstring styles beyond Google-style (e.g., reStructuredText, NumPy style).
* **CI/CD Integration:** Develop capabilities to integrate the agent into Continuous Integration/Continuous Deployment pipelines to enforce documentation standards automatically.
* **Interactive Mode:** Introduce an interactive mode where the user can review and approve/reject generated docstrings for each function individually before changes are applied.
* **Configuration File:** Implement support for a configuration file (e.g., `pyproject.toml` or `doc_agent.ini`) to manage default settings and preferences.
* **Docstring Validation:** Add a post-generation step to validate that the generated docstrings adhere to Python's PEP 257 or other specified style guides.

