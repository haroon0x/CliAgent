from src.theagent.flow import create_chat_flow
from src.theagent.utils.visualize_flow import DummyArgs, DummyLLMProxy

# Create the flow
flow = create_chat_flow(DummyArgs(), DummyLLMProxy())

print("=== Flow Structure Analysis ===")
print(f"Start node: {type(flow.start_node).__name__}")
print(f"Start node successors: {flow.start_node.successors}")

# Check each node's successors
for action, node in flow.start_node.successors.items():
    print(f"\n{type(node).__name__} (from action '{action}'):")
    print(f"  Successors: {node.successors}")

# Check if there are any missing connections
print("\n=== Checking for missing connections ===")
all_nodes = set()
all_nodes.add(flow.start_node)

# Collect all nodes
for node in flow.start_node.successors.values():
    all_nodes.add(node)
    for next_node in node.successors.values():
        all_nodes.add(next_node)

print(f"Total nodes found: {len(all_nodes)}")
for i, node in enumerate(all_nodes):
    print(f"  Node{i}: {type(node).__name__} - Successors: {node.successors}") 