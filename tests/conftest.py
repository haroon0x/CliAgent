"""
Pytest configuration and shared fixtures for CliAgent tests.
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cliagent.utils.call_llm import AlchemistAIProxy, GeneralLLMProxy


class MockArgs:
    """Mock arguments object for testing."""
    def __init__(self, file=None, output='console', llm='dummy', no_confirm=True, 
                 verbose=False, migration_target='Python 3', chat=False):
        self.file = file
        self.output = output
        self.llm = llm
        self.no_confirm = no_confirm
        self.verbose = verbose
        self.migration_target = migration_target
        self.chat = chat


class MockLLMProxy:
    """Comprehensive mock LLM proxy for testing."""
    
    def __init__(self):
        self.call_history = []
    
    def _record_call(self, method_name, *args, **kwargs):
        """Record method calls for testing."""
        self.call_history.append({
            'method': method_name,
            'args': args,
            'kwargs': kwargs
        })
    
    def generate_docstring(self, function_code, function_name):
        self._record_call('generate_docstring', function_code, function_name)
        return f'"""Mock docstring for {function_name}."""'
    
    def summarize_code(self, code):
        self._record_call('summarize_code', code)
        return "Mock code summary: This is a test file with basic functionality."
    
    def add_type_annotations(self, code):
        self._record_call('add_type_annotations', code)
        return code.replace('def foo(x):', 'def foo(x: int) -> int:')
    
    def migrate_code(self, code, migration_target):
        self._record_call('migrate_code', code, migration_target)
        return f"{code}\n# Migrated to {migration_target}"
    
    def generate_tests(self, code):
        self._record_call('generate_tests', code)
        return "def test_mock():\n    assert True"
    
    def detect_bugs(self, code):
        self._record_call('detect_bugs', code)
        return "No bugs detected in mock analysis."
    
    def refactor_code(self, code):
        self._record_call('refactor_code', code)
        return f"{code}\n# Refactored for better readability"
    
    def chat(self, prompt):
        self._record_call('chat', prompt)
        return "Mock chat response"


@pytest.fixture
def mock_args():
    """Provide mock arguments for testing."""
    return MockArgs()


@pytest.fixture
def mock_llm_proxy():
    """Provide mock LLM proxy for testing."""
    return MockLLMProxy()


@pytest.fixture
def temp_py_file():
    """Create a temporary Python file for testing."""
    def _create_temp_file(content, suffix='.py'):
        with tempfile.NamedTemporaryFile('w+', suffix=suffix, delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            return f.name
    
    return _create_temp_file


@pytest.fixture
def sample_python_code():
    """Provide sample Python code for testing."""
    return '''def calculate_sum(a, b):
    return a + b

def greet(name):
    print(f"Hello, {name}!")

class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x):
        self.value += x
        return self.value
'''


@pytest.fixture
def sample_python_code_with_bugs():
    """Provide sample Python code with potential bugs for testing."""
    return '''def divide_numbers(a, b):
    return a / b  # Potential division by zero

def access_list_element(lst, index):
    return lst[index]  # Potential index error

def process_data(data):
    if data is None:
        return None
    return data.upper()  # Potential attribute error
'''


@pytest.fixture
def sample_python_code_for_migration():
    """Provide sample Python code that needs migration."""
    return '''print "Hello World"  # Python 2 style
xrange(10)  # Python 2 specific
raw_input("Enter: ")  # Python 2 specific
'''


@pytest.fixture
def cleanup_temp_files():
    """Cleanup fixture to remove temporary files after tests."""
    temp_files = []
    
    def _add_temp_file(file_path):
        temp_files.append(file_path)
    
    yield _add_temp_file
    
    # Cleanup
    for file_path in temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass  # File might already be deleted 