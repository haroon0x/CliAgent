import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock
from theagent.nodes import DocAgentNode, SummaryAgentNode, TypeAnnotationAgentNode, MigrationAgentNode, TestGenerationAgentNode, BugDetectionAgentNode, RefactorCodeAgentNode

class DummyArgs:
    def __init__(self, file, output='console', llm='dummy', no_confirm=True, verbose=False, migration_target='Python 3'):
        self.file = file
        self.output = output
        self.llm = llm
        self.no_confirm = no_confirm
        self.verbose = verbose
        self.migration_target = migration_target

class DummyLLMProxy:
    def __init__(self):
        self.call_history = []
    
    def _record_call(self, method_name, *args, **kwargs):
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
        return 'Mock code summary: This is a test file with basic functionality.'
    
    def add_type_annotations(self, code):
        self._record_call('add_type_annotations', code)
        return code.replace('def foo(x):', 'def foo(x: int) -> int:')
    
    def migrate_code(self, code, migration_target):
        self._record_call('migrate_code', code, migration_target)
        return code.replace('print', 'print') + f' # migrated to {migration_target}'
    
    def generate_tests(self, code):
        self._record_call('generate_tests', code)
        return 'def test_foo(): assert foo(1) == 2'
    
    def detect_bugs(self, code):
        self._record_call('detect_bugs', code)
        return 'No bugs found.'
    
    def refactor_code(self, code):
        self._record_call('refactor_code', code)
        return code + ' # refactored'

def make_temp_pyfile(code):
    tf = tempfile.NamedTemporaryFile('w+', suffix='.py', delete=False, encoding='utf-8')
    tf.write(code)
    tf.close()  # Ensure file is closed so it can be deleted on Windows
    return tf.name

# Test data fixtures
@pytest.fixture
def sample_python_code():
    return '''def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
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
    return '''print "Hello World"  # Python 2 style
xrange(10)  # Python 2 specific
raw_input("Enter: ")  # Python 2 specific
'''

# Enhanced DocAgentNode tests
def test_doc_agent_node_parses_and_inserts_docstring():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    new_file = tf_name.replace('.py', '_documented.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert 'Mock docstring for foo' in content
    os.remove(tf_name)
    os.remove(new_file)

def test_doc_agent_node_with_existing_docstrings(sample_python_code):
    """Test DocAgentNode with code that already has docstrings."""
    tf_name = make_temp_pyfile(sample_python_code)
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    new_file = tf_name.replace('.py', '_documented.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert 'Mock docstring for calculate_sum' in content
        assert 'Mock docstring for greet' in content
        assert 'Mock docstring for add' in content
    os.remove(tf_name)
    os.remove(new_file)

def test_doc_agent_node_with_empty_file():
    """Test DocAgentNode with empty Python file."""
    tf_name = make_temp_pyfile("")
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    assert functions == []
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    os.remove(tf_name)

def test_doc_agent_node_with_invalid_python():
    """Test DocAgentNode with invalid Python syntax."""
    tf_name = make_temp_pyfile("def invalid syntax {")
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    assert functions == []
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    os.remove(tf_name)

def test_doc_agent_node_with_nonexistent_file():
    """Test DocAgentNode with nonexistent file."""
    args = DummyArgs("nonexistent_file.py", output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    assert functions == []

def test_doc_agent_node_llm_failure():
    """Test DocAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.generate_docstring = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    shared = {}
    functions = node.prep(shared)
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    
    new_file = tf_name.replace('.py', '_documented.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert 'Error: Failed to generate docstring' in content
    os.remove(tf_name)
    os.remove(new_file)

# Enhanced SummaryAgentNode tests
def test_summary_agent_node():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = SummaryAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    summary = node.exec(source)
    assert summary == 'Mock code summary: This is a test file with basic functionality.'
    os.remove(tf_name)

def test_summary_agent_node_with_complex_code(sample_python_code):
    """Test SummaryAgentNode with complex Python code."""
    tf_name = make_temp_pyfile(sample_python_code)
    args = DummyArgs(tf_name)
    node = SummaryAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    summary = node.exec(source)
    assert 'Mock code summary' in summary
    os.remove(tf_name)

def test_summary_agent_node_llm_failure():
    """Test SummaryAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = SummaryAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.summarize_code = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    shared = {}
    source = node.prep(shared)
    summary = node.exec(source)
    assert "Error: Failed to generate summary" in summary
    os.remove(tf_name)

# Enhanced TypeAnnotationAgentNode tests
def test_type_annotation_agent_node():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = TypeAnnotationAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    suggestions = node.exec(source)
    assert 'def foo(x: int) -> int:' in suggestions
    assert 'return x + 1' in suggestions
    os.remove(tf_name)

def test_type_annotation_agent_node_with_complex_code(sample_python_code):
    """Test TypeAnnotationAgentNode with complex Python code."""
    tf_name = make_temp_pyfile(sample_python_code)
    args = DummyArgs(tf_name, output='new-file')
    node = TypeAnnotationAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    typed_code = node.exec(source)
    node.post(shared, source, typed_code)
    
    typed_file = tf_name.replace('.py', '_typed.py')
    assert os.path.exists(typed_file)
    with open(typed_file) as f:
        content = f.read()
        assert 'def calculate_sum' in content
    os.remove(tf_name)
    os.remove(typed_file)

def test_type_annotation_agent_node_llm_failure():
    """Test TypeAnnotationAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = TypeAnnotationAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.add_type_annotations = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    shared = {}
    source = node.prep(shared)
    typed_code = node.exec(source)
    assert "Error: Failed to add type annotations" in typed_code
    os.remove(tf_name)

# Enhanced MigrationAgentNode tests
def test_migration_agent_node():
    code = 'print("hello")\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file', migration_target='Python 3')
    node = MigrationAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        migrated = node.exec(f.read())
    node.write_output(migrated, 'migrated', 'Migrated Code')
    new_file = tf_name.replace('.py', '_migrated.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert '# migrated to Python 3' in content
    os.remove(tf_name)
    os.remove(new_file)

def test_migration_agent_node_with_python2_code(sample_python_code_for_migration):
    """Test MigrationAgentNode with Python 2 specific code."""
    tf_name = make_temp_pyfile(sample_python_code_for_migration)
    args = DummyArgs(tf_name, output='new-file', migration_target='Python 3')
    node = MigrationAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        migrated = node.exec(f.read())
    node.write_output(migrated, 'migrated', 'Migrated Code')
    new_file = tf_name.replace('.py', '_migrated.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert '# migrated to Python 3' in content
    os.remove(tf_name)
    os.remove(new_file)

def test_migration_agent_node_llm_failure():
    """Test MigrationAgentNode when LLM proxy fails."""
    code = 'print("hello")\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, migration_target='Python 3')
    node = MigrationAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.migrate_code = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    with open(tf_name) as f:
        migrated = node.exec(f.read())
    assert "Error: Failed to migrate code" in migrated
    os.remove(tf_name)

# Enhanced TestGenerationAgentNode tests
def test_test_generation_agent_node():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file')
    node = TestGenerationAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    tests = node.exec(functions)
    node.post(shared, functions, tests)
    test_file = tf_name.replace('.py', '_tests.py')
    assert os.path.exists(test_file)
    with open(test_file) as f:
        content = f.read()
        assert 'def test_foo()' in content
    os.remove(tf_name)
    os.remove(test_file)

def test_test_generation_agent_node_with_complex_code(sample_python_code):
    """Test TestGenerationAgentNode with complex Python code."""
    tf_name = make_temp_pyfile(sample_python_code)
    args = DummyArgs(tf_name, output='new-file')
    node = TestGenerationAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    tests = node.exec(functions)
    node.post(shared, functions, tests)
    test_file = tf_name.replace('.py', '_tests.py')
    assert os.path.exists(test_file)
    with open(test_file) as f:
        content = f.read()
        assert 'def test_foo()' in content
    os.remove(tf_name)
    os.remove(test_file)

def test_test_generation_agent_node_llm_failure():
    """Test TestGenerationAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file')
    node = TestGenerationAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.generate_tests = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    shared = {}
    functions = node.prep(shared)
    tests = node.exec(functions)
    node.post(shared, functions, tests)
    test_file = tf_name.replace('.py', '_tests.py')
    assert os.path.exists(test_file)
    with open(test_file) as f:
        content = f.read()
        assert 'Error: Failed to generate tests' in content
    os.remove(tf_name)
    os.remove(test_file)

# Enhanced BugDetectionAgentNode tests
def test_bug_detection_agent_node():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = BugDetectionAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        bug_report = node.exec(f.read())
    assert bug_report == 'No bugs found.'
    os.remove(tf_name)

def test_bug_detection_agent_node_with_potential_bugs(sample_python_code_with_bugs):
    """Test BugDetectionAgentNode with code that has potential bugs."""
    tf_name = make_temp_pyfile(sample_python_code_with_bugs)
    args = DummyArgs(tf_name)
    node = BugDetectionAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        bug_report = node.exec(f.read())
    assert 'No bugs found' in bug_report
    os.remove(tf_name)

def test_bug_detection_agent_node_llm_failure():
    """Test BugDetectionAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name)
    node = BugDetectionAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.detect_bugs = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    with open(tf_name) as f:
        bug_report = node.exec(f.read())
    assert "Error: Failed to detect bugs" in bug_report
    os.remove(tf_name)

# Enhanced RefactorCodeAgentNode tests
def test_refactor_code_agent_node():
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file')
    node = RefactorCodeAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        refactored = node.exec(f.read())
    node.write_output(refactored, 'refactored', 'Refactored Code')
    new_file = tf_name.replace('.py', '_refactored.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert '# refactored' in content
    os.remove(tf_name)
    os.remove(new_file) 

def test_refactor_code_agent_node_with_complex_code(sample_python_code):
    """Test RefactorCodeAgentNode with complex Python code."""
    tf_name = make_temp_pyfile(sample_python_code)
    args = DummyArgs(tf_name, output='new-file')
    node = RefactorCodeAgentNode(args, DummyLLMProxy())
    with open(tf_name) as f:
        refactored = node.exec(f.read())
    node.write_output(refactored, 'refactored', 'Refactored Code')
    new_file = tf_name.replace('.py', '_refactored.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert '# refactored' in content
    os.remove(tf_name)
    os.remove(new_file)

def test_refactor_code_agent_node_llm_failure():
    """Test RefactorCodeAgentNode when LLM proxy fails."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    args = DummyArgs(tf_name, output='new-file')
    node = RefactorCodeAgentNode(args, DummyLLMProxy())
    
    # Make the LLM proxy raise an exception
    mock_proxy = DummyLLMProxy()
    mock_proxy.refactor_code = MagicMock(side_effect=Exception("LLM Error"))
    node.llm_proxy = mock_proxy
    
    with open(tf_name) as f:
        refactored = node.exec(f.read())
    node.write_output(refactored, 'refactored', 'Refactored Code')
    new_file = tf_name.replace('.py', '_refactored.py')
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
        assert 'Error: Failed to refactor code' in content
    os.remove(tf_name)
    os.remove(new_file)

# Integration tests
def test_multiple_agent_nodes_workflow():
    """Test that multiple agent nodes can work together in a workflow."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    
    # Test doc generation
    args = DummyArgs(tf_name, output='new-file', no_confirm=True)
    node = DocAgentNode(args, DummyLLMProxy())
    shared = {}
    functions = node.prep(shared)
    docstrings = node.exec(functions)
    node.post(shared, functions, docstrings)
    
    # Test summary generation
    summary_node = SummaryAgentNode(args, DummyLLMProxy())
    source = summary_node.prep(shared)
    summary = summary_node.exec(source)
    summary_node.post(shared, source, summary)
    
    # Verify both operations worked
    documented_file = tf_name.replace('.py', '_documented.py')
    assert os.path.exists(documented_file)
    assert 'docstring_results' in shared
    assert 'summary' in shared
    
    os.remove(tf_name)
    os.remove(documented_file)

def test_file_output_modes():
    """Test different file output modes work correctly."""
    code = 'def foo(x):\n    return x + 1\n'
    tf_name = make_temp_pyfile(code)
    
    # Test console output mode
    args = DummyArgs(tf_name, output='console')
    node = SummaryAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    summary = node.exec(source)
    node.post(shared, source, summary)
    
    # Test new-file output mode
    args = DummyArgs(tf_name, output='new-file')
    node = SummaryAgentNode(args, DummyLLMProxy())
    shared = {}
    source = node.prep(shared)
    summary = node.exec(source)
    node.post(shared, source, summary)
    
    # Verify new file was created - SummaryAgentNode uses 'summary' suffix
    summary_file = tf_name.replace('.py', '_summary.py')
    assert os.path.exists(summary_file)
    
    os.remove(tf_name)
    os.remove(summary_file) 