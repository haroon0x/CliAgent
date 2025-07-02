from pocketflow import Node
from theagent.utils.call_llm import AlchemistAIProxy, GeneralLLMProxy
import ast
import os
import shutil
import re
import yaml
from typing import Dict, List, Optional, Any

class BaseAgentNode(Node):
    def __init__(self, args, llm_proxy):
        super().__init__()
        self.args = args
        self.llm_proxy = llm_proxy

    def read_source(self):
        file_path = self.args.file
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_output(self, content, suffix, console_title=None):
        output_mode = getattr(self.args, 'output', 'console')
        file_path = self.args.file
        verbose = getattr(self.args, 'verbose', False)
        if output_mode == 'console':
            if console_title:
                print(f"\n=== {console_title} ===\n")
            print(content)
        elif output_mode == 'in-place':
            backup_path = file_path + '.bak'
            shutil.copyfile(file_path, backup_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.rstrip() + '\n')
            if verbose:
                print(f"Wrote {console_title or 'output'} to {file_path} (backup at {backup_path})")
        elif output_mode == 'new-file':
            new_file = file_path.replace('.py', f'_{suffix}.py')
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(content.rstrip() + '\n')
            if verbose:
                print(f"Wrote {console_title or 'output'} to {new_file}")

    def _find_end_line(self, node):
        max_line = getattr(node, 'lineno', 0)
        for child in ast.iter_child_nodes(node):
            child_line = self._find_end_line(child)
            if child_line > max_line:
                max_line = child_line
        return max_line

    def _manual_source_segment(self, source_code, start, end):
        """Manually extract source code segment."""
        lines = source_code.split('\n')
        return '\n'.join(lines[start-1:end])

class DocAgentNode(BaseAgentNode):
    def prep(self, shared):
        # Read and parse the Python file
        try:
            source_code = self.read_source()
            tree = ast.parse(source_code)
            
            # Extract function definitions
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get the function source code
                    start_line = node.lineno
                    end_line = self._find_end_line(node)
                    function_code = self._manual_source_segment(source_code, start_line, end_line)
                    
                    functions.append({
                        'name': node.name,
                        'code': function_code,
                        'line': start_line
                    })
            
            if not functions:
                print("[WARNING] No functions found in the file")
                return []
            
            return functions
            
        except Exception as e:
            print(f"[ERROR] Failed to parse file: {e}")
            return []

    def _clean_docstring(self, doc):
        """Clean up the generated docstring."""
        # Remove any markdown formatting
        doc = doc.replace('```python', '').replace('```', '').strip()
        # Ensure it starts and ends with quotes
        if not doc.startswith('"""'):
            doc = '"""' + doc
        if not doc.endswith('"""'):
            doc = doc + '"""'
        return doc

    def exec(self, functions):
        # For each function, generate a docstring
        results = []
        for func in functions:
            try:
                docstring = self.llm_proxy.generate_docstring(func['code'], func['name'])
                if docstring:
                    docstring = self._clean_docstring(docstring)
                else:
                    docstring = '"""Function documentation placeholder."""'
                
                results.append({
                    'name': func['name'],
                    'code': func['code'],
                    'docstring': docstring,
                    'line': func['line']
                })
                
            except Exception as e:
                print(f"[ERROR] Failed to generate docstring for {func['name']}: {e}")
                results.append({
                    'name': func['name'],
                    'code': func['code'],
                    'docstring': '"""Error: Failed to generate docstring"""',
                    'line': func['line']
                })
        
        return results
    
    def post(self, shared, prep_res, exec_res):
        if not exec_res:
            print("[WARNING] No docstrings were generated")
            return "default"
        
        # Display results
        print("\nGenerated docstrings:")
        print("=" * 50)
        for result in exec_res:
            print(f"\nFunction: {result['name']}")
            print("-" * 40)
            print(result['code'])
            print(f"\nGenerated docstring:\n{result['docstring']}")
        
        # Insert docstrings into the source code and write to file if needed
        file_path = self.args.file
        with open(file_path, 'r', encoding='utf-8') as f:
            source_lines = f.readlines()
        
        # Map function name to docstring and line
        doc_map = {r['name']: (r['docstring'], r['line']) for r in exec_res}
        
        # Parse AST to find function locations
        tree = ast.parse(''.join(source_lines))
        inserts = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in doc_map:
                docstring, start_line = doc_map[node.name]
                func_start = node.lineno - 1
                # Check for existing docstring
                if (len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)):
                    doc_start = node.body[0].lineno - 1
                    doc_end = node.body[0].end_lineno if hasattr(node.body[0], 'end_lineno') else doc_start + 1
                    inserts.append((doc_start, doc_end, docstring))
                else:
                    # Insert after function def line
                    header_end = func_start + 1
                    while header_end < len(source_lines) and source_lines[header_end].strip() == '':
                        header_end += 1
                    inserts.append((header_end, header_end, docstring))
        # Apply inserts in reverse order to not mess up line numbers
        new_lines = source_lines[:]
        for start, end, docstring in sorted(inserts, reverse=True):
            docstring_lines = [l + '\n' for l in docstring.strip().split('\n')]
            new_lines[start:end] = docstring_lines
        new_source = ''.join(new_lines)
        # Write output if needed
        self.write_output(new_source, 'documented', 'Documented Code')
        # Store results in shared context
        shared['docstring_results'] = exec_res
        return "default"

    def _find_docstring_end(self, func_lines, quote):
        # Find the end of the docstring block
        for i, line in enumerate(func_lines):
            if line.strip().endswith(quote):
                return i + 1
        return len(func_lines)

class SummaryAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        # Summarize the file
        try:
            summary = self.llm_proxy.summarize_code(source_code)
            if summary is None:
                summary = "Error: Failed to generate summary"
            return summary
        except Exception as e:
            print(f"[ERROR] Failed to generate summary: {e}")
            return "Error: Failed to generate summary"

    def post(self, shared, prep_res, exec_res):
        output_mode = getattr(self.args, 'output', 'console')
        if output_mode == 'new-file':
            self.write_output(exec_res, 'summary', 'Summary')
        print(f"\n[SUMMARY] Summary of {self.args.file}:")
        print("=" * 50)
        print(exec_res)
        print("=" * 50)

        shared['summary'] = exec_res
        return "default"

class TestGenerationAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        try:
            tests = self.llm_proxy.generate_tests(source_code)
            if tests is None:
                tests = "# Error: Failed to generate tests"
            return tests
        except Exception as e:
            print(f"[ERROR] Failed to generate tests: {e}")
            return "# Error: Failed to generate tests"
    
    def post(self, shared, prep_res, exec_res):
        self.write_output(exec_res, 'tests', 'Generated Tests')
        shared['tests'] = exec_res
        return "default"

class MigrationAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        migration_target = getattr(self.args, 'migration_target', 'Python 3')
        try:
            migrated_code = self.llm_proxy.migrate_code(source_code, migration_target)
            if migrated_code is None:
                migrated_code = "# Error: Failed to migrate code"
            return migrated_code
        except Exception as e:
            print(f"[ERROR] Failed to migrate code: {e}")
            return "# Error: Failed to migrate code"

    def post(self, shared, prep_res, exec_res):
        self.write_output(exec_res, 'migrated', 'Migrated Code')
        shared['migrated_code'] = exec_res
        return "default"

class BugDetectionAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        try:
            bugs = self.llm_proxy.detect_bugs(source_code)
            if bugs is None:
                bugs = "Error: Failed to detect bugs"
            return bugs
        except Exception as e:
            print(f"[ERROR] Failed to detect bugs: {e}")
            return "Error: Failed to detect bugs"

    def post(self, shared, prep_res, exec_res):
        print(f"\n[BUG DETECTION] Analysis of {self.args.file}:")
        print("=" * 50)
        print(exec_res)
        print("=" * 50)
        
        shared['bug_analysis'] = exec_res
        return "default"

class RefactorCodeAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        try:
            refactored = self.llm_proxy.refactor_code(source_code)
            if refactored is None:
                refactored = "# Error: Failed to refactor code"
            return refactored
        except Exception as e:
            print(f"[ERROR] Failed to refactor code: {e}")
            return "# Error: Failed to refactor code"

    def post(self, shared, prep_res, exec_res):
        self.write_output(exec_res, 'refactored', 'Refactored Code')
        shared['refactored_code'] = exec_res
        return "default"

class TypeAnnotationAgentNode(BaseAgentNode):
    def prep(self, shared):
        return self.read_source()

    def exec(self, source_code):
        try:
            typed_code = self.llm_proxy.add_type_annotations(source_code)
            if typed_code is None:
                typed_code = "# Error: Failed to add type annotations"
            return typed_code
        except Exception as e:
            print(f"[ERROR] Failed to add type annotations: {e}")
            return "# Error: Failed to add type annotations"

    def post(self, shared, prep_res, exec_res):
        self.write_output(exec_res, 'typed', 'Code with Type Annotations')
        shared['typed_code'] = exec_res
        return "default"

class OrchestratorAgentNode(Node):
    def __init__(self, args, llm_proxy):
        super().__init__()
        self.args = args
        self.llm_proxy = llm_proxy
    
    def prep(self, shared):
        # Get the user's instruction
        user_input = shared.get('user_input', '')
        if not user_input:
            user_input = input("Enter your instruction: ")
            shared['user_input'] = user_input
        
        # Get chat history if available
        chat_history = shared.get('chat_history', [])
        
        # Build context from chat history
        context = ""
        if chat_history:
            context = "\n".join([f"User: {msg['user']}\nAgent: {msg['agent']}" for msg in chat_history[-3:]])  # Last 3 exchanges
        
        return user_input, context

    def exec(self, context_data):
        user_input, context = context_data
        
        system_prompt = """You are an intelligent assistant that helps users with code-related tasks. Your job is to understand the user's intent and determine the best course of action.

Available actions:
1. file_management - For file operations (list, read, create, delete files)
2. code_generation - For generating code, docstrings, tests, etc.
3. code_analysis - For analyzing, summarizing, or reviewing code
4. general_question - For answering general programming questions
5. clarification_needed - When the request is ambiguous or missing information

Return your response in YAML format:
```yaml
intent: <action_name>
confidence: <0.0-1.0>
reasoning: <brief explanation>
parameters:
  file_path: <if relevant>
  operation: <specific operation>
  agent_type: <if code generation needed>
```

Examples:
- "list files" → file_management with operation: list
- "read main.py" → file_management with operation: read, file_path: main.py
- "generate docstrings" → clarification_needed (missing file)
- "what is Python?" → general_question
- "summarize this code" → clarification_needed (missing file)"""

        prompt = f"""Context from previous conversation:
{context}

User input: {user_input}

Analyze the user's intent and respond with the appropriate action."""

        try:
            response = self.llm_proxy.chat(prompt)
            
            # Extract YAML from response
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
                result = yaml.safe_load(yaml_content)
            else:
                # Fallback parsing
                result = {
                    'intent': 'general_question',
                    'confidence': 0.5,
                    'reasoning': 'Could not parse intent, treating as general question',
                    'parameters': {}
                }
            
            return result
            
        except Exception as e:
            print(f"Error in intent recognition: {e}")
            return {
                'intent': 'general_question',
                'confidence': 0.0,
                'reasoning': f'Error: {e}',
                'parameters': {}
            }

    def post(self, shared, prep_res, exec_res):
        # If exec_res is a string, treat it as a direct answer (general chat)
        if isinstance(exec_res, str):
            print(f"\n[AGENT] {exec_res}")
            shared['agent_response'] = exec_res
            return "default"
        
        # Otherwise, it's an intent recognition result
        shared['intent_result'] = exec_res
        intent = exec_res.get('intent', 'general_question')
        
        # Route to appropriate action
        if intent == 'clarification_needed':
            return 'clarification'
        elif intent == 'file_management':
            return 'file_management'
        elif intent == 'code_generation':
            return 'code_generation'
        elif intent == 'code_analysis':
            return 'code_analysis'
        else:
            return 'general_question'

class UserApprovalNode(Node):
    def __init__(self, key_to_review, message="Please review the result below:", title="User Approval"):
        super().__init__()
        self.key_to_review = key_to_review
        self.message = message
        self.title = title

    def prep(self, shared):
        return shared.get(self.key_to_review, "No content to review")

    def exec(self, value):
        print(f"\n=== {self.title} ===")
        print(self.message)
        print("-" * 50)
        print(value)
        print("-" * 50)
        
        while True:
            response = input("Approve (a), Refine (r), or Deny (d)? ").lower().strip()
            if response in ['a', 'approve']:
                return 'approved'
            elif response in ['r', 'refine']:
                return 'refine'
            elif response in ['d', 'deny']:
                return 'denied'
            else:
                print("Please enter 'a', 'r', or 'd'")
    
    def post(self, shared, prep_res, exec_res):
        return exec_res

class IntentRecognitionNode(Node):
    """Node for recognizing user intent in chat mode."""
    
    def __init__(self, args, llm_proxy):
        super().__init__()
        self.args = args
        self.llm_proxy = llm_proxy

    def prep(self, shared):
        # Get the user's instruction
        user_input = shared.get('user_input', '')
        if not user_input:
            user_input = input("Enter your instruction: ")
            shared['user_input'] = user_input
        
        # Get chat history if available
        chat_history = shared.get('chat_history', [])
        
        # Build context from chat history
        context = ""
        if chat_history:
            context = "\n".join([f"User: {msg['user']}\nAgent: {msg['agent']}" for msg in chat_history[-3:]])  # Last 3 exchanges
        
        shared['context'] = context
        
        return user_input, context

    def exec(self, context_data):
        user_input, context = context_data
        
        system_prompt = """You are an intelligent assistant that helps users with code-related tasks. Your job is to understand the user's intent and determine the best course of action.

Available actions:
1. file_management - For file operations (list, read, create, delete files)
2. code_generation - For generating code, docstrings, tests, etc.
3. code_analysis - For analyzing, summarizing, or reviewing code
4. general_question - For answering general programming questions
5. clarification_needed - When the request is ambiguous or missing information

Return your response in YAML format:
```yaml
intent: <action_name>
confidence: <0.0-1.0>
reasoning: <brief explanation>
parameters:
  file_path: <if relevant>
  operation: <specific operation>
  agent_type: <if code generation needed>
```

Examples:
- "list files" → file_management with operation: list
- "read main.py" → file_management with operation: read, file_path: main.py
- "generate docstrings" → clarification_needed (missing file)
- "what is Python?" → general_question
- "summarize this code" → clarification_needed (missing file)"""

        prompt = f"""Context from previous conversation:
{context}

User input: {user_input}

Analyze the user's intent and respond with the appropriate action."""

        try:
            response = self.llm_proxy.chat(prompt)
            
            # Extract YAML from response
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
                result = yaml.safe_load(yaml_content)
            else:
                # Fallback parsing
                result = {
                    'intent': 'general_question',
                    'confidence': 0.5,
                    'reasoning': 'Could not parse intent, treating as general question',
                    'parameters': {}
                }
            
            return result
            
        except Exception as e:
            print(f"Error in intent recognition: {e}")
            return {
                'intent': 'general_question',
                'confidence': 0.0,
                'reasoning': f'Error: {e}',
                'parameters': {}
            }

    def post(self, shared, prep_res, exec_res):
        shared['intent_result'] = exec_res
        intent = exec_res.get('intent', 'general_question')
        
        # Route to appropriate action
        if intent == 'clarification_needed':
            return 'clarification'
        elif intent == 'file_management':
            return 'file_management'
        elif intent == 'code_generation':
            return 'code_generation'
        elif intent == 'code_analysis':
            return 'code_analysis'
        else:
            return 'general_question'

class ClarificationNode(Node):
    """Node for requesting clarification from the user."""
    
    def __init__(self, clarification_message):
        super().__init__()
        self.clarification_message = clarification_message

    def prep(self, shared):
        return shared.get('context', '')

    def exec(self, context):
        print(f"\n[CLARIFICATION NEEDED] {self.clarification_message}")
        if context:
            print(f"Context: {context}")
        
        clarification = input("Please provide more details: ")
        return clarification

    def post(self, shared, prep_res, exec_res):
        # Add clarification exchange to history
        chat_history = shared.get('chat_history', [])
        chat_history.append({
            'user': shared.get('user_input', ''),
            'agent': f"Clarification requested: {self.clarification_message}"
        })
        chat_history.append({
            'user': exec_res,
            'agent': 'Thank you for the clarification.'
        })
        shared['chat_history'] = chat_history
        
        return "default"

class FileManagementNode(Node):
    """Node for handling file management operations."""
    
    def __init__(self, args, llm_proxy):
        super().__init__()
        self.args = args
        self.llm_proxy = llm_proxy

    def prep(self, shared):
        return shared.get('intent_result', {})

    def exec(self, context):
        intent_data = context
        operation = intent_data.get('parameters', {}).get('operation', '')
        file_path = intent_data.get('parameters', {}).get('file_path', '')
        
        current_dir = os.getcwd()
        
        if operation == 'list':
            return self._list_files(current_dir)
        elif operation == 'read':
            return self._read_file(file_path, current_dir)
        elif operation == 'create':
            return self._create_file(file_path, current_dir)
        elif operation == 'delete':
            return self._delete_file(file_path, current_dir)
        else:
            return f"Unknown file operation: {operation}"

    def _list_files(self, directory):
        """List files in the current directory."""
        try:
            files = os.listdir(directory)
            file_list = []
            for file in files:
                if os.path.isfile(os.path.join(directory, file)):
                    file_list.append(f"📄 {file}")
                else:
                    file_list.append(f"📁 {file}/")
            
            return f"Files in {directory}:\n" + "\n".join(file_list)
        except Exception as e:
            return f"Error listing files: {e}"

    def _read_file(self, instruction, current_dir):
        """Read a file based on instruction."""
        try:
            # Extract filename from instruction
            if not instruction:
                return "No file specified"
            
            file_path = os.path.join(current_dir, instruction)
            if not os.path.exists(file_path):
                return f"File not found: {instruction}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"Content of {instruction}:\n{'-' * 40}\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"

    def _create_file(self, instruction, current_dir):
        """Create a file based on instruction."""
        try:
            if not instruction:
                return "No file specified"
            
            file_path = os.path.join(current_dir, instruction)
            if os.path.exists(file_path):
                return f"File already exists: {instruction}"
            
            # Create empty file
            with open(file_path, 'w') as f:
                f.write("# Created by TheAgent\n")
            
            return f"Created file: {instruction}"
        except Exception as e:
            return f"Error creating file: {e}"

    def _delete_file(self, instruction, current_dir):
        """Delete a file based on instruction."""
        try:
            if not instruction:
                return "No file specified"
            
            file_path = os.path.join(current_dir, instruction)
            if not os.path.exists(file_path):
                return f"File not found: {instruction}"
            
            os.remove(file_path)
            return f"Deleted file: {instruction}"
        except Exception as e:
            return f"Error deleting file: {e}"

    def post(self, shared, prep_res, exec_res):
        print(f"\n[FILE OPERATION] {exec_res}")
        shared['file_operation_result'] = exec_res
        return "default"

class SafetyCheckNode(Node):
    """Node for performing safety checks before operations."""
    
    def __init__(self, operation_type, target_file=None):
        super().__init__()
        self.operation_type = operation_type
        self.target_file = target_file

    def prep(self, shared):
        return shared.get('context', '')

    def exec(self, context):
        if self.operation_type == 'in_place_modification':
            if self.target_file:
                print(f"\n[SAFETY CHECK] You are about to modify {self.target_file} in-place.")
                print("This will create a backup file with .bak extension.")
                
                response = input("Do you want to proceed? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    return 'approved'
                else:
                    return 'denied'
        
        return 'approved'

    def post(self, shared, prep_res, exec_res):
        return exec_res

class ContextAwarenessNode(Node):
    """Node for gathering context about the current environment."""
    
    def __init__(self):
        super().__init__()

    def prep(self, shared):
        return shared.get('args', {})

    def exec(self, context):
        # Gather context about the current environment
        context_info = {
            'current_directory': os.getcwd(),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'platform': os.sys.platform,
            'available_files': []
        }
        
        # List Python files in current directory
        try:
            files = os.listdir('.')
            python_files = [f for f in files if f.endswith('.py')]
            context_info['available_files'] = python_files
        except Exception as e:
            context_info['available_files'] = [f"Error listing files: {e}"]
        
        return context_info

    def post(self, shared, prep_res, exec_res):
        shared['context_info'] = exec_res
        
        # Display context information
        print(f"\n[CONTEXT] Current environment:")
        print(f"  Directory: {exec_res['current_directory']}")
        print(f"  Python: {exec_res['python_version']}")
        print(f"  Platform: {exec_res['platform']}")
        print(f"  Python files: {', '.join(exec_res['available_files'][:5])}")
        if len(exec_res['available_files']) > 5:
            print(f"  ... and {len(exec_res['available_files']) - 5} more")
        
        return "default"

class ErrorHandlingNode(Node):
    """Node for handling errors and providing suggestions."""
    
    def __init__(self, operation_name):
        super().__init__()
        self.operation_name = operation_name

    def prep(self, shared):
        return shared.get('error_context', {})

    def exec(self, context):
        error_type = context.get('error_type', 'unknown')
        error_message = context.get('error_message', 'Unknown error')
        
        suggestion = self._get_suggestion(error_type, context)
        
        return {
            'error_type': error_type,
            'error_message': error_message,
            'suggestion': suggestion
        }

    def _get_suggestion(self, error_type, context):
        """Get helpful suggestions based on error type."""
        suggestions = {
            'file_not_found': "Check if the file exists and the path is correct.",
            'permission_denied': "Check file permissions or try running with elevated privileges.",
            'api_error': "Check your API key and internet connection.",
            'parsing_error': "The file might contain syntax errors. Check the code structure.",
            'timeout': "The operation took too long. Try with a smaller file or check your connection.",
            'unknown': "An unexpected error occurred. Check the error message above."
        }
        
        return suggestions.get(error_type, suggestions['unknown'])

    def post(self, shared, prep_res, exec_res):
        print(f"\n[ERROR] {self.operation_name} failed:")
        print(f"  Type: {exec_res['error_type']}")
        print(f"  Message: {exec_res['error_message']}")
        print(f"  Suggestion: {exec_res['suggestion']}")
        
        shared['error_info'] = exec_res
        return "default"

def create_doc_agent_nodes(args, llm_proxy):
    """Create nodes for docstring generation."""
    return {
        'doc': DocAgentNode(args, llm_proxy),
        'summary': SummaryAgentNode(args, llm_proxy),
        'test': TestGenerationAgentNode(args, llm_proxy),
        'bug': BugDetectionAgentNode(args, llm_proxy),
        'refactor': RefactorCodeAgentNode(args, llm_proxy),
        'type': TypeAnnotationAgentNode(args, llm_proxy),
        'migration': MigrationAgentNode(args, llm_proxy)
    }