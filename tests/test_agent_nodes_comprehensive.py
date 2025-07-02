"""
Comprehensive tests for TheAgent nodes with better coverage and validation.
"""
import pytest
import os
import ast
from unittest.mock import patch, MagicMock
from theagent.nodes import (
    DocAgentNode, SummaryAgentNode, TypeAnnotationAgentNode, 
    MigrationAgentNode, TestGenerationAgentNode, BugDetectionAgentNode, 
    RefactorCodeAgentNode, OrchestratorAgentNode, UserApprovalNode,
    IntentRecognitionNode, ClarificationNode, FileManagementNode,
    SafetyCheckNode, ContextAwarenessNode, ErrorHandlingNode
)


class TestDocAgentNode:
    """Comprehensive tests for DocAgentNode."""
    
    def test_prep_with_valid_python_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                        sample_python_code, cleanup_temp_files):
        """Test prep method with valid Python file."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        
        # Should find 4 functions: calculate_sum, greet, __init__, add
        assert len(functions) == 4
        assert any(f['name'] == 'calculate_sum' for f in functions)
        assert any(f['name'] == 'greet' for f in functions)
        assert any(f['name'] == '__init__' for f in functions)
        assert any(f['name'] == 'add' for f in functions)
        
        # Verify function code extraction
        for func in functions:
            assert 'code' in func
            assert 'name' in func
            assert 'line' in func
            assert func['code'].startswith('def ') or func['code'].startswith('    def ')
    
    def test_prep_with_empty_file(self, mock_args, mock_llm_proxy, temp_py_file, cleanup_temp_files):
        """Test prep method with empty Python file."""
        file_path = temp_py_file("")
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        assert functions == []
    
    def test_prep_with_invalid_python(self, mock_args, mock_llm_proxy, temp_py_file, cleanup_temp_files):
        """Test prep method with invalid Python syntax."""
        file_path = temp_py_file("def invalid syntax {")
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        assert functions == []
    
    def test_prep_with_nonexistent_file(self, mock_args, mock_llm_proxy):
        """Test prep method with nonexistent file."""
        mock_args.file = "nonexistent_file.py"
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        # The node handles FileNotFoundError gracefully and returns empty list
        functions = node.prep(shared)
        assert functions == []
    
    def test_exec_generates_docstrings(self, mock_args, mock_llm_proxy, temp_py_file, 
                                     sample_python_code, cleanup_temp_files):
        """Test exec method generates docstrings for functions."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        results = node.exec(functions)
        
        assert len(results) == len(functions)
        for result in results:
            assert 'docstring' in result
            assert result['docstring'].startswith('"""')
            assert result['docstring'].endswith('"""')
            assert mock_llm_proxy.call_history[-1]['method'] == 'generate_docstring'
    
    def test_exec_handles_llm_failure(self, mock_args, mock_llm_proxy, temp_py_file, 
                                    sample_python_code, cleanup_temp_files):
        """Test exec method handles LLM proxy failures gracefully."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        # Make the LLM proxy raise an exception
        mock_llm_proxy.generate_docstring = MagicMock(side_effect=Exception("LLM Error"))
        
        functions = node.prep(shared)
        results = node.exec(functions)
        
        assert len(results) == len(functions)
        for result in results:
            assert 'docstring' in result
            assert 'Error: Failed to generate docstring' in result['docstring']
    
    def test_post_writes_documented_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                        sample_python_code, cleanup_temp_files):
        """Test post method writes documented file when output mode is new-file."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.output = 'new-file'
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        results = node.exec(functions)
        node.post(shared, functions, results)
        
        documented_file = file_path.replace('.py', '_documented.py')
        cleanup_temp_files(documented_file)
        
        assert os.path.exists(documented_file)
        with open(documented_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Mock docstring for calculate_sum' in content
            assert 'def calculate_sum' in content
    
    def test_post_stores_results_in_shared(self, mock_args, mock_llm_proxy, temp_py_file, 
                                         sample_python_code, cleanup_temp_files):
        """Test post method stores results in shared context."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = DocAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        functions = node.prep(shared)
        results = node.exec(functions)
        node.post(shared, functions, results)
        
        assert 'docstring_results' in shared
        assert shared['docstring_results'] == results


class TestSummaryAgentNode:
    """Comprehensive tests for SummaryAgentNode."""
    
    def test_prep_reads_source_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                  sample_python_code, cleanup_temp_files):
        """Test prep method reads source file correctly."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = SummaryAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        assert source == sample_python_code
    
    def test_exec_generates_summary(self, mock_args, mock_llm_proxy, temp_py_file, 
                                  sample_python_code, cleanup_temp_files):
        """Test exec method generates code summary."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = SummaryAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        summary = node.exec(source)
        
        assert summary == "Mock code summary: This is a test file with basic functionality."
        assert mock_llm_proxy.call_history[-1]['method'] == 'summarize_code'
    
    def test_exec_handles_llm_failure(self, mock_args, mock_llm_proxy, temp_py_file, 
                                    sample_python_code, cleanup_temp_files):
        """Test exec method handles LLM proxy failures."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = SummaryAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        # Make the LLM proxy raise an exception
        mock_llm_proxy.summarize_code = MagicMock(side_effect=Exception("LLM Error"))
        
        source = node.prep(shared)
        summary = node.exec(source)
        
        assert "Error: Failed to generate summary" in summary
    
    def test_post_displays_and_stores_summary(self, mock_args, mock_llm_proxy, temp_py_file, 
                                            sample_python_code, cleanup_temp_files):
        """Test post method displays and stores summary."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = SummaryAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        summary = node.exec(source)
        node.post(shared, source, summary)
        
        assert 'summary' in shared
        assert shared['summary'] == summary


class TestTypeAnnotationAgentNode:
    """Comprehensive tests for TypeAnnotationAgentNode."""
    
    def test_exec_adds_type_annotations(self, mock_args, mock_llm_proxy, temp_py_file, 
                                      sample_python_code, cleanup_temp_files):
        """Test exec method adds type annotations to code."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = TypeAnnotationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        typed_code = node.exec(source)
        
        # The mock should return the original code since it doesn't contain 'def foo(x):'
        assert typed_code == sample_python_code
        assert mock_llm_proxy.call_history[-1]['method'] == 'add_type_annotations'
    
    def test_post_writes_typed_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                  sample_python_code, cleanup_temp_files):
        """Test post method writes typed file when output mode is new-file."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.output = 'new-file'
        node = TypeAnnotationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        typed_code = node.exec(source)
        node.post(shared, source, typed_code)
        
        typed_file = file_path.replace('.py', '_typed.py')
        cleanup_temp_files(typed_file)
        
        assert os.path.exists(typed_file)
        with open(typed_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'def calculate_sum' in content
            assert 'def greet' in content


class TestMigrationAgentNode:
    """Comprehensive tests for MigrationAgentNode."""
    
    def test_exec_migrates_code(self, mock_args, mock_llm_proxy, temp_py_file, 
                              sample_python_code_for_migration, cleanup_temp_files):
        """Test exec method migrates code to target version."""
        file_path = temp_py_file(sample_python_code_for_migration)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.migration_target = 'Python 3'
        node = MigrationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        migrated_code = node.exec(source)
        
        assert "Migrated to Python 3" in migrated_code
        assert mock_llm_proxy.call_history[-1]['method'] == 'migrate_code'
    
    def test_post_writes_migrated_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                     sample_python_code_for_migration, cleanup_temp_files):
        """Test post method writes migrated file when output mode is new-file."""
        file_path = temp_py_file(sample_python_code_for_migration)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.output = 'new-file'
        mock_args.migration_target = 'Python 3'
        node = MigrationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        migrated_code = node.exec(source)
        node.post(shared, source, migrated_code)
        
        migrated_file = file_path.replace('.py', '_migrated.py')
        cleanup_temp_files(migrated_file)
        
        assert os.path.exists(migrated_file)
        with open(migrated_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Migrated to Python 3" in content


class TestTestGenerationAgentNode:
    """Comprehensive tests for TestGenerationAgentNode."""
    
    def test_exec_generates_tests(self, mock_args, mock_llm_proxy, temp_py_file, 
                                sample_python_code, cleanup_temp_files):
        """Test exec method generates test code."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = TestGenerationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        test_code = node.exec(source)
        
        assert "def test_mock():" in test_code
        assert mock_llm_proxy.call_history[-1]['method'] == 'generate_tests'
    
    def test_post_writes_test_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                 sample_python_code, cleanup_temp_files):
        """Test post method writes test file when output mode is new-file."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.output = 'new-file'
        node = TestGenerationAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        test_code = node.exec(source)
        node.post(shared, source, test_code)
        
        test_file = file_path.replace('.py', '_tests.py')
        cleanup_temp_files(test_file)
        
        assert os.path.exists(test_file)
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "def test_mock():" in content


class TestBugDetectionAgentNode:
    """Comprehensive tests for BugDetectionAgentNode."""
    
    def test_exec_detects_bugs(self, mock_args, mock_llm_proxy, temp_py_file, 
                             sample_python_code_with_bugs, cleanup_temp_files):
        """Test exec method detects bugs in code."""
        file_path = temp_py_file(sample_python_code_with_bugs)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = BugDetectionAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        bug_analysis = node.exec(source)
        
        assert "No bugs detected" in bug_analysis
        assert mock_llm_proxy.call_history[-1]['method'] == 'detect_bugs'
    
    def test_post_stores_bug_analysis(self, mock_args, mock_llm_proxy, temp_py_file, 
                                    sample_python_code_with_bugs, cleanup_temp_files):
        """Test post method stores bug analysis in shared context."""
        file_path = temp_py_file(sample_python_code_with_bugs)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = BugDetectionAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        bug_analysis = node.exec(source)
        node.post(shared, source, bug_analysis)
        
        assert 'bug_analysis' in shared
        assert shared['bug_analysis'] == bug_analysis


class TestRefactorCodeAgentNode:
    """Comprehensive tests for RefactorCodeAgentNode."""
    
    def test_exec_refactors_code(self, mock_args, mock_llm_proxy, temp_py_file, 
                               sample_python_code, cleanup_temp_files):
        """Test exec method refactors code."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        node = RefactorCodeAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        refactored_code = node.exec(source)
        
        assert "Refactored for better readability" in refactored_code
        assert mock_llm_proxy.call_history[-1]['method'] == 'refactor_code'
    
    def test_post_writes_refactored_file(self, mock_args, mock_llm_proxy, temp_py_file, 
                                       sample_python_code, cleanup_temp_files):
        """Test post method writes refactored file when output mode is new-file."""
        file_path = temp_py_file(sample_python_code)
        cleanup_temp_files(file_path)
        
        mock_args.file = file_path
        mock_args.output = 'new-file'
        node = RefactorCodeAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        source = node.prep(shared)
        refactored_code = node.exec(source)
        node.post(shared, source, refactored_code)
        
        refactored_file = file_path.replace('.py', '_refactored.py')
        cleanup_temp_files(refactored_file)
        
        assert os.path.exists(refactored_file)
        with open(refactored_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Refactored for better readability" in content


class TestOrchestratorAgentNode:
    """Comprehensive tests for OrchestratorAgentNode."""
    
    def test_prep_with_user_input(self, mock_args, mock_llm_proxy):
        """Test prep method with user input."""
        mock_args.chat = False
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        shared = {'user_input': 'test input'}
        
        result = node.prep(shared)
        assert result == ('test input', '')
    
    def test_prep_with_chat_history(self, mock_args, mock_llm_proxy):
        """Test prep method with chat history."""
        mock_args.chat = True
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        shared = {
            'user_input': 'test input',
            'chat_history': [{'user': 'test user input', 'agent': 'test agent response'}]
        }
        
        result = node.prep(shared)
        assert 'test user input' in result[1]  # context contains the chat history
    
    @patch('builtins.input', return_value='test input')
    def test_prep_prompts_for_input(self, mock_input, mock_args, mock_llm_proxy):
        """Test prep method prompts for input when not provided."""
        mock_args.chat = False
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        result = node.prep(shared)
        assert result == ('test input', '')
    
    def test_exec_recognizes_intent(self, mock_args, mock_llm_proxy):
        """Test exec method recognizes user intent."""
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        
        # Mock the LLM response to return structured intent
        mock_llm_proxy.chat = MagicMock(return_value='''
```yaml
intent: code_generation
confidence: 0.9
reasoning: User wants to generate code
parameters:
  agent_type: docstring
```
''')
        
        result = node.exec(('test input', ''))
        assert 'intent' in result
        assert result['intent'] == 'code_generation'
    
    def test_exec_handles_malformed_response(self, mock_args, mock_llm_proxy):
        """Test exec method handles malformed LLM responses."""
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        
        # Mock the LLM response to return unstructured text
        mock_llm_proxy.chat = MagicMock(return_value='Just a regular response without YAML')
        
        result = node.exec(('test input', ''))
        assert 'intent' in result
        assert result['intent'] == 'general_question'
    
    def test_post_routes_to_correct_action(self, mock_args, mock_llm_proxy):
        """Test post method routes to correct action based on intent."""
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        intent_result = {
            'intent': 'code_generation',
            'parameters': {'agent_type': 'docstring'}
        }
        
        action = node.post(shared, 'input', intent_result)
        assert action == 'code_generation'
        assert 'intent_result' in shared
    
    def test_post_handles_string_response(self, mock_args, mock_llm_proxy):
        """Test post method handles string responses (general chat)."""
        node = OrchestratorAgentNode(mock_args, mock_llm_proxy)
        shared = {}
        
        chat_response = "This is a general chat response"
        action = node.post(shared, 'input', chat_response)
        
        assert action == 'default'
        assert 'agent_response' in shared
        assert shared['agent_response'] == chat_response


class TestUserApprovalNode:
    """Comprehensive tests for UserApprovalNode."""
    
    def test_prep_retrieves_value_from_shared(self, mock_args, mock_llm_proxy):
        """Test prep method retrieves value from shared context."""
        node = UserApprovalNode('test_key', 'Test message')
        shared = {'test_key': 'test value'}
        
        result = node.prep(shared)
        assert result == 'test value'
    
    def test_prep_handles_missing_key(self, mock_args, mock_llm_proxy):
        """Test prep method handles missing key gracefully."""
        node = UserApprovalNode('missing_key', 'Test message')
        shared = {}
        
        result = node.prep(shared)
        assert result == 'No content to review'
    
    @patch('builtins.input', return_value='a')
    def test_exec_approves_with_a(self, mock_input, mock_args, mock_llm_proxy):
        """Test exec method approves with 'a' input."""
        node = UserApprovalNode('test_key', 'Test message')
        
        result = node.exec('test value')
        assert result == 'approved'
    
    @patch('builtins.input', return_value='approve')
    def test_exec_approves_with_approve(self, mock_input, mock_args, mock_llm_proxy):
        """Test exec method approves with 'approve' input."""
        node = UserApprovalNode('test_key', 'Test message')
        
        result = node.exec('test value')
        assert result == 'approved'
    
    @patch('builtins.input', return_value='r')
    def test_exec_refines_with_r(self, mock_input, mock_args, mock_llm_proxy):
        """Test exec method refines with 'r' input."""
        node = UserApprovalNode('test_key', 'Test message')
        
        result = node.exec('test value')
        assert result == 'refine'
    
    @patch('builtins.input', return_value='d')
    def test_exec_denies_with_d(self, mock_input, mock_args, mock_llm_proxy):
        """Test exec method denies with 'd' input."""
        node = UserApprovalNode('test_key', 'Test message')
        
        result = node.exec('test value')
        assert result == 'denied'
    
    @patch('builtins.input', side_effect=['invalid', 'a'])
    def test_exec_retries_on_invalid_input(self, mock_input, mock_args, mock_llm_proxy):
        """Test exec method retries on invalid input."""
        node = UserApprovalNode('test_key', 'Test message')
        
        result = node.exec('test value')
        assert result == 'approved'
        assert mock_input.call_count == 2


class TestFileManagementNode:
    """Comprehensive tests for FileManagementNode."""
    
    def test_prep_retrieves_context(self, mock_args, mock_llm_proxy):
        """Test prep method retrieves context from shared."""
        node = FileManagementNode(mock_args, mock_llm_proxy)
        shared = {'intent_result': 'test context'}
        
        result = node.prep(shared)
        assert result == 'test context'
    
    def test_exec_handles_list_operation(self, mock_args, mock_llm_proxy):
        """Test exec method handles list files operation."""
        node = FileManagementNode(mock_args, mock_llm_proxy)
        
        # The exec method expects a dict with parameters
        context = {'parameters': {'operation': 'list', 'directory': '.'}}
        result = node.exec(context)
        
        assert 'Files in' in result
        # Check for file indicators or current directory listing
        assert '📄' in result or '📁' in result or 'Files in' in result
    
    def test_post_stores_result(self, mock_args, mock_llm_proxy):
        """Test post method stores result in shared context."""
        node = FileManagementNode(mock_args, mock_llm_proxy)
        shared = {}
        
        result = {'operation': 'list', 'files': ['file1.py', 'file2.py']}
        action = node.post(shared, 'context', result)
        
        assert action == 'default'
        assert 'file_operation_result' in shared
        assert shared['file_operation_result'] == result


class TestSafetyCheckNode:
    """Comprehensive tests for SafetyCheckNode."""
    
    def test_prep_retrieves_context(self, mock_args, mock_llm_proxy):
        """Test prep method retrieves context from shared."""
        node = SafetyCheckNode('file_operation', 'test.py')
        shared = {'context': 'test context'}
        
        result = node.prep(shared)
        assert result == 'test context'
    
    def test_exec_performs_safety_check(self, mock_args, mock_llm_proxy):
        """Test exec method performs safety check."""
        node = SafetyCheckNode('file_operation', 'test.py')
        
        result = node.exec('delete file test.py')
        assert result == 'approved'
    
    def test_post_approves_safe_operation(self, mock_args, mock_llm_proxy):
        """Test post method approves safe operations."""
        node = SafetyCheckNode('file_operation', 'test.py')
        shared = {}
        
        result = 'approved'
        action = node.post(shared, 'context', result)
        
        assert action == 'approved'
    
    def test_post_denies_unsafe_operation(self, mock_args, mock_llm_proxy):
        """Test post method denies unsafe operations."""
        node = SafetyCheckNode('file_operation', 'test.py')
        shared = {}
        
        result = 'denied'
        action = node.post(shared, 'context', result)
        
        assert action == 'denied'


class TestContextAwarenessNode:
    """Comprehensive tests for ContextAwarenessNode."""
    
    def test_prep_retrieves_context(self, mock_args, mock_llm_proxy):
        """Test prep method retrieves context from shared."""
        node = ContextAwarenessNode()
        shared = {'args': 'test context'}
        
        result = node.prep(shared)
        assert result == 'test context'
    
    def test_exec_gathers_context(self, mock_args, mock_llm_proxy):
        """Test exec method gathers context information."""
        node = ContextAwarenessNode()
        
        result = node.exec('test context')
        assert 'current_directory' in result
        assert 'python_version' in result
        assert 'platform' in result
    
    def test_post_stores_context(self, mock_args, mock_llm_proxy):
        """Test post method stores context in shared."""
        node = ContextAwarenessNode()
        shared = {}
        
        context = {
            'current_directory': '/test', 
            'python_version': '3.11', 
            'platform': 'win32',
            'available_files': ['test.py', 'main.py']
        }
        action = node.post(shared, 'input', context)
        
        assert action == 'default'
        assert 'context_info' in shared
        assert shared['context_info'] == context


class TestErrorHandlingNode:
    """Comprehensive tests for ErrorHandlingNode."""
    
    def test_prep_retrieves_context(self, mock_args, mock_llm_proxy):
        """Test prep method retrieves context from shared."""
        node = ErrorHandlingNode('test_operation')
        shared = {'error_context': 'test context'}
        
        result = node.prep(shared)
        assert result == 'test context'
    
    def test_exec_analyzes_error(self, mock_args, mock_llm_proxy):
        """Test exec method analyzes error context."""
        node = ErrorHandlingNode('test_operation')
        
        # The exec method expects a dict, not a string
        error_context = {'error_type': 'FileNotFoundError', 'error_message': 'test.py not found'}
        result = node.exec(error_context)
        
        assert 'error_type' in result
        assert result['error_type'] == 'FileNotFoundError'
        assert 'error_message' in result
        assert 'suggestion' in result
    
    def test_post_stores_error_analysis(self, mock_args, mock_llm_proxy):
        """Test post method stores error analysis."""
        node = ErrorHandlingNode('test_operation')
        shared = {}
        
        analysis = {'error_type': 'FileNotFoundError', 'suggestion': 'Check file path', 'error_message': 'test.py not found'}
        action = node.post(shared, 'context', analysis)
        
        assert action == 'default'
        assert 'error_info' in shared
        assert shared['error_info'] == analysis 