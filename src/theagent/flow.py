from pocketflow import Flow
from theagent.nodes import (
    DocAgentNode, SummaryAgentNode, TestGenerationAgentNode, BugDetectionAgentNode,
    RefactorCodeAgentNode, TypeAnnotationAgentNode, MigrationAgentNode,
    IntentRecognitionNode, ClarificationNode, FileManagementNode, SafetyCheckNode,
    ContextAwarenessNode, ErrorHandlingNode, UserApprovalNode
)

def create_doc_agent_flow(args, llm_proxy):
    # Example: just use the doc agent node directly
    doc_node = DocAgentNode(args, llm_proxy)
    return Flow(start=doc_node)

def create_enhanced_agent_flow(args, llm_proxy):
    """Create an enhanced flow with safety checks and user approval."""
    context_node = ContextAwarenessNode()
    safety_node = SafetyCheckNode('in_place_modification', getattr(args, 'file', None))
    
    # Create agent nodes based on type
    if args.agent == 'doc':
        agent_node = DocAgentNode(args, llm_proxy)
    elif args.agent == 'summary':
        agent_node = SummaryAgentNode(args, llm_proxy)
    elif args.agent == 'test':
        agent_node = TestGenerationAgentNode(args, llm_proxy)
    elif args.agent == 'bug':
        agent_node = BugDetectionAgentNode(args, llm_proxy)
    elif args.agent == 'refactor':
        agent_node = RefactorCodeAgentNode(args, llm_proxy)
    elif args.agent == 'type':
        agent_node = TypeAnnotationAgentNode(args, llm_proxy)
    elif args.agent == 'migration':
        agent_node = MigrationAgentNode(args, llm_proxy)
    else:
        raise ValueError(f"Unknown agent type: {args.agent}")
    
    approval_node = UserApprovalNode('result', "Please review the generated result:", "Result Review")
    error_node = ErrorHandlingNode('main_operation')
    
    # Connect nodes
    context_node >> safety_node
    safety_node - "approved" >> agent_node
    safety_node - "denied" >> error_node
    agent_node >> approval_node
    approval_node - "approved" >> error_node  # End flow
    approval_node - "refine" >> agent_node  # Loop back for refinement
    
    return Flow(start=context_node)

def create_simple_enhanced_flow(args, llm_proxy):
    """Create a simple enhanced flow with basic safety and error handling."""
    context_node = ContextAwarenessNode()
    
    # Create agent nodes based on type
    if args.agent == 'doc':
        agent_node = DocAgentNode(args, llm_proxy)
    elif args.agent == 'summary':
        agent_node = SummaryAgentNode(args, llm_proxy)
    elif args.agent == 'test':
        agent_node = TestGenerationAgentNode(args, llm_proxy)
    elif args.agent == 'bug':
        agent_node = BugDetectionAgentNode(args, llm_proxy)
    elif args.agent == 'refactor':
        agent_node = RefactorCodeAgentNode(args, llm_proxy)
    elif args.agent == 'type':
        agent_node = TypeAnnotationAgentNode(args, llm_proxy)
    elif args.agent == 'migration':
        agent_node = MigrationAgentNode(args, llm_proxy)
    else:
        raise ValueError(f"Unknown agent type: {args.agent}")
    
    error_node = ErrorHandlingNode('main_operation')
    
    # Connect nodes
    context_node >> agent_node
    agent_node >> error_node
    
    return Flow(start=context_node)

def create_chat_flow(args, llm_proxy):
    """Create a chat flow with intent recognition."""
    intent_node = IntentRecognitionNode(args, llm_proxy)
    clarification_node = ClarificationNode("Please clarify your request")
    file_management_node = FileManagementNode(args, llm_proxy)
    error_node = ErrorHandlingNode('main_operation')
    
    # Create agent nodes for code operations
    doc_node = DocAgentNode(args, llm_proxy)
    summary_node = SummaryAgentNode(args, llm_proxy)
    
    # Connect nodes - reuse the same error_node for all end points
    intent_node - "clarification" >> clarification_node
    intent_node - "file_management" >> file_management_node
    intent_node - "code_generation" >> doc_node
    intent_node - "code_analysis" >> summary_node
    intent_node - "general_question" >> error_node  # Handle general questions
    
    clarification_node >> intent_node  # Loop back after clarification
    file_management_node >> error_node  # End after file operations
    doc_node >> error_node  # End after docstring generation
    summary_node >> error_node  # End after summary generation
    
    return Flow(start=intent_node)