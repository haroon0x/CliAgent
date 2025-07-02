# utils/call_llm.py
import os
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from .utils import ProgressTracker, create_progress_tracker

class AlchemistAIProxy:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("ALCHEMYST_API_KEY")
        self.base_url = "https://platform-backend.getalchemystai.com/api/v1/proxy/default"

    def chat(self, prompt: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """
        General chat method for intent recognition and other conversational tasks.
        """
        from langchain_openai import ChatOpenAI
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "Error: Failed to get response"

    def generate_docstring(self, function_code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """
        Generate a Google-style docstring for the given function code using the specified LLM model.
        """
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python documentation agent. "
            "Your job is to generate professional, comprehensive, and accurate Google-style docstrings for Python functions. "
            "You must strictly follow these rules: "
            "- Only output the docstring content, do NOT include triple quotes or markdown code fences. "
            "- Do NOT include any explanations, code, or extra text. "
            "- The docstring must adhere to the Google Python style guide and include, where applicable: "
            "  1. A concise one-line summary of the function's purpose. "
            "  2. A detailed multi-line description of what the function does, including important context or algorithm details. "
            "  3. Args: List each argument with its type hint and a clear description. "
            "  4. Returns: Describe the return value, its type hint, and what it represents. "
            "  5. Raises: (If applicable) Describe any exceptions that the function might raise. "
            "  6. Yields: (If applicable) Describe any values yielded by a generator function. "
            "  7. Note: (Optional) Any important notes or caveats. "
            "  8. Examples: (Highly Recommended) One or more clear code examples using >>>. "
            "- For boolean arguments, explain what True and False signify. "
            "- For arguments with default values, mention them in the description. "
            "- Ensure correct indentation and formatting. "
            "- If the function is a generator, document Yields instead of Returns. "
            "- If the function is a method, document 'self' only if it is relevant. "
            "- If the function has *args or **kwargs, document them. "
            "- If the function has type hints, use them in the docstring. "
            "- If the function has an existing docstring, replace it. "
            "- Do not repeat the function signature. "
            "- Do not include any markdown or code fences. "
            "\n\nOutput Format:\nOnly output the docstring content, no triple quotes, no markdown, no extra text.\n\nSample Output (for a function that adds two numbers):\nAdds two numbers together.\n\nArgs:\n    a (int): The first number.\n    b (int): The second number.\n\nReturns:\n    int: The sum of a and b.\n"
        )
        prompt = f"Document this Python function:\n{function_code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "# Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "# Error: Failed to generate docstring"

    def summarize_code(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python code summarization agent. "
            "Your job is to read Python code and generate a concise, high-level summary of what the code does. "
            "- Only output the summary, do NOT include any code, markdown, or extra text. "
            "- The summary should mention the main purpose, key functions/classes, and any important algorithms or patterns. "
            "- If the code is a script, mention its entry point and main workflow. "
            "- If the code is a module, mention its API and usage. "
            "- Be clear, accurate, and concise. "
            "\n\nOutput Format:\nA single concise paragraph. No code, no markdown, no extra text.\n\nSample Output:\nThis script processes CSV files and generates summary statistics for each column, including mean, median, and standard deviation. The main function orchestrates file loading, data cleaning, and result output."
        )
        prompt = "Summarize this Python code:\n" + code
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=512,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "Error: Failed to generate summary"

    def suggest_type_annotations(self, function_code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python type annotation agent. "
            "Your job is to add proper type hints to Python functions. "
            "- Only output the function with type annotations, do NOT include any explanations, markdown, or extra text. "
            "- Use modern Python type hints (Python 3.7+). "
            "- Import necessary types from typing module if needed. "
            "- If the function is already properly typed, return it unchanged. "
            "\n\nOutput Format:\nOnly output the function with type annotations. No explanations, no markdown, no extra text.\n\nSample Output:\nfrom typing import List, Optional\n\ndef process_data(items: List[str], count: Optional[int] = None) -> List[str]:\n    return items[:count] if count else items\n"
        )
        prompt = f"Add type annotations to this Python function:\n{function_code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "# Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "# Error: Failed to add type annotations"

    def test_generation(self, function_code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python testing agent. "
            "Your job is to generate comprehensive unit tests for Python functions. "
            "- Only output the test code, do NOT include any explanations, markdown, or extra text. "
            "- Use pytest style tests with clear test names. "
            "- Include tests for normal cases, edge cases, and error cases. "
            "- Import necessary modules and use appropriate assertions. "
            "- If the function has multiple parameters, test different combinations. "
            "- If the function can raise exceptions, test those cases. "
            "\n\nOutput Format:\nOnly output the test code. No explanations, no markdown, no extra text.\n\nSample Output:\nimport pytest\nfrom mymodule import my_function\n\ndef test_my_function_normal_case():\n    assert my_function(2, 3) == 5\n\ndef test_my_function_edge_case():\n    assert my_function(0, 0) == 0\n"
        )
        prompt = f"Generate unit tests for this Python function:\n{function_code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "# Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "# Error: Failed to generate tests"

    def bug_detection(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python code review agent specializing in bug detection. "
            "Your job is to analyze Python code and identify potential bugs, issues, or improvements. "
            "- Only output the analysis, do NOT include any code, markdown, or extra text. "
            "- Focus on logical errors, potential runtime issues, and best practice violations. "
            "- Be specific about what could go wrong and why. "
            "- Suggest improvements where applicable. "
            "- If no significant issues are found, mention that the code appears to be well-written. "
            "\n\nOutput Format:\nA clear analysis of potential issues. No code, no markdown, no extra text.\n\nSample Output:\nThe code looks generally well-structured, but there are a few potential issues: 1) The function doesn't handle the case where the input list is empty, which could cause an IndexError. 2) There's no validation of input parameters, which could lead to unexpected behavior with invalid inputs. 3) The variable naming could be more descriptive to improve readability."
        )
        prompt = f"Analyze this Python code for potential bugs and issues:\n{code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
                )
            result = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])
            if result.content is None:
                return "Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "Error: Failed to analyze code"

    def refactor_code(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python refactoring agent. "
            "Your job is to refactor Python code to improve readability, performance, and maintainability. "
            "- Only output the refactored code, do NOT include any explanations, markdown, or extra text. "
            "- Maintain the same functionality while improving code quality. "
            "- Use modern Python features and best practices. "
            "- Improve variable names, function structure, and code organization. "
            "- Add appropriate comments where needed. "
            "- Ensure the code is PEP 8 compliant. "
            "\n\nOutput Format:\nOnly output the refactored code. No explanations, no markdown, no extra text.\n\nSample Output:\ndef calculate_average(numbers: list[float]) -> float:\n    \"\"\"Calculate the average of a list of numbers.\"\"\"\n    if not numbers:\n        raise ValueError(\"Cannot calculate average of empty list\")\n    return sum(numbers) / len(numbers)\n"
        )
        prompt = f"Refactor this Python code to improve quality:\n{code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "# Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "# Error: Failed to refactor code"

    def _migration_code(self, code: str, migration_target: str = "Python 3", model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        from langchain_openai import ChatOpenAI
        system_prompt = (
            "You are an expert Python code migration agent. "
            "Your job is to migrate Python code to the specified target version. "
            "- Only output the migrated code, do NOT include any explanations, markdown, or extra text. "
            "- Ensure the code is compatible with the target Python version. "
            "- Update deprecated functions and syntax. "
            "- Use modern Python features where appropriate. "
            "- Maintain the original functionality. "
            "\n\nOutput Format:\nOnly output the migrated code. No explanations, no markdown, no extra text.\n\nSample Output:\nfrom typing import List\n\ndef process_items(items: List[str]) -> List[str]:\n    return [item.upper() for item in items]\n"
        )
        prompt = f"Migrate this Python code to {migration_target}:\n{code}"
        try:
            if not self.api_key:
                raise ValueError("ALCHEMYST_API_KEY not found in environment variables")
            
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url,
                temperature=0.2,
                top_p=0.9,
                max_tokens=1024,
            )
            result = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            if result.content is None:
                return "# Error: No response from LLM"
            return result.content.strip()
        except Exception as e:
            print(f"[AlchemistAIProxy] LLM API error: {e}")
            return "# Error: Failed to migrate code"

    # Method aliases to match the interface expected by nodes
    def generate_tests(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """Alias for test_generation method."""
        return self.test_generation(code, model_name)
    
    def migrate_code(self, code: str, migration_target: str = "Python 3", model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """Alias for _migration_code method."""
        return self._migration_code(code, migration_target, model_name)
    
    def detect_bugs(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """Alias for bug_detection method."""
        return self.bug_detection(code, model_name)
    
    def add_type_annotations(self, code: str, model_name: str = "alchemyst-ai/alchemyst-c1") -> str:
        """Alias for suggest_type_annotations method."""
        return self.suggest_type_annotations(code, model_name)

class GeneralLLMProxy:
    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

    def call_llm(self, prompt, provider='openai', **kwargs):
        """
        Call LLM with the specified provider.
        """
        if provider == 'openai':
            return self._call_openai_llm(prompt, **kwargs)
        elif provider == 'anthropic':
            return self._call_anthropic_llm(prompt, **kwargs)
        elif provider == 'ollama':
            return self._call_ollama_llm(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _call_openai_llm(self, prompt, model='gpt-4o', api_key=None, base_url=None, temperature=0.2, top_p=0.9, max_tokens=1024, **kwargs):
        from langchain_openai import ChatOpenAI
        try:
            llm = ChatOpenAI(
                api_key=api_key or self.openai_api_key,
                model=model,
                base_url=base_url,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            result = llm.invoke([{"role": "user", "content": prompt}])
            return result.content if result.content else "Error: No response from LLM"
        except Exception as e:
            print(f"[GeneralLLMProxy] OpenAI API error: {e}")
            return f"Error: Failed to call OpenAI LLM - {e}"

    def _call_anthropic_llm(self, prompt, model='claude-2', api_key=None, **kwargs):
        from anthropic import Anthropic
        try:
            client = Anthropic(api_key=api_key or self.anthropic_api_key)
            response = client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return response.content[0].text if response.content else "Error: No response from LLM"
        except Exception as e:
            print(f"[GeneralLLMProxy] Anthropic API error: {e}")
            return f"Error: Failed to call Anthropic LLM - {e}"

    def _call_ollama_llm(self, prompt, model='llama2', **kwargs):
        from ollama import chat
        try:
            response = chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.message.content if response.message else "Error: No response from LLM"
        except Exception as e:
            print(f"[GeneralLLMProxy] Ollama API error: {e}")
            return f"Error: Failed to call Ollama LLM - {e}"