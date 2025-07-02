import sys
from pocketflow import Flow, Node


def flow_to_mermaid(flow: Flow) -> str:
    """Generate a Mermaid diagram for a given Flow object."""
    edges = []
    visited = set()
    node_names = {}
    node_counter = [0]

    def get_node_name(node):
        if node not in node_names:
            node_names[node] = f"Node{node_counter[0]}"
            node_counter[0] += 1
        return node_names[node]

    def walk(node):
        if node in visited:
            return
        visited.add(node)
        this_name = get_node_name(node)
        # Get transitions from the successors attribute
        transitions = getattr(node, 'successors', {})
        for action, next_node in transitions.items():
            next_name = get_node_name(next_node)
            label = f"|{action}|" if action != 'default' else ''
            edges.append(f"    {this_name}{label} --> {next_name}")
            walk(next_node)

    walk(flow.start_node)
    # Node labels
    node_labels = [f"    {name}[\"{type(node).__name__}\"]" for node, name in node_names.items()]
    mermaid = ["flowchart TD"] + node_labels + edges
    return '\n'.join(mermaid)

# --- Dummies for visualization ---
class DummyArgs:
    file = "dummy.py"
    output = "console"
    verbose = False
    chat = False
    agent = "doc"  # Add default agent type

class DummyLLMProxy:
    def chat(self, prompt): return "dummy"
    def generate_docstring(self, *a, **k): return '"""Dummy docstring."""'
    def summarize_code(self, *a, **k): return "Dummy summary"
    def generate_tests(self, *a, **k): return "def test_dummy(): pass"
    def add_type_annotations(self, *a, **k): return "# typed"
    def migrate_code(self, *a, **k): return "# migrated"
    def detect_bugs(self, *a, **k): return "No bugs"
    def refactor_code(self, *a, **k): return "# refactored"


def main():
    # Example usage: python -m theagent.utils.visualize_flow <flow_name>
    import importlib
    import inspect
    if len(sys.argv) < 2:
        print("Usage: python -m theagent.utils.visualize_flow <flow_module>:<flow_func>")
        sys.exit(1)
    arg = sys.argv[1]
    if ':' not in arg:
        print("Please specify as <module>:<function>")
        sys.exit(1)
    module_name, func_name = arg.split(':', 1)
    mod = importlib.import_module(module_name)
    flow_func = getattr(mod, func_name)
    sig = inspect.signature(flow_func)
    # If the flow function requires 2 args, provide dummies
    if len(sig.parameters) == 2:
        flow = flow_func(DummyArgs(), DummyLLMProxy())
    else:
        flow = flow_func()
    print(flow_to_mermaid(flow))

if __name__ == "__main__":
    main()
