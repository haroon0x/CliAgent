import argparse
import os
import sys
from theagent.flow import (
    create_doc_agent_flow, create_enhanced_agent_flow, create_simple_enhanced_flow,
    create_chat_flow
)
from theagent.utils.call_llm import AlchemistAIProxy

class Args:
    pass

def setup_shared_context(args_obj):
    """Setup shared context with current directory and file information."""
    shared = {
        'history': [],
        'current_directory': os.getcwd(),
        'verbose': getattr(args_obj, 'verbose', False),
        'no_confirm': getattr(args_obj, 'no_confirm', False)
    }
    
    # Add file context if provided
    if hasattr(args_obj, 'file') and args_obj.file:
        shared['file'] = args_obj.file
        if os.path.exists(args_obj.file):
            shared['file_exists'] = True
            shared['file_size'] = os.path.getsize(args_obj.file)
        else:
            shared['file_exists'] = False
            shared['last_error'] = f"File not found: {args_obj.file}"
    
    return shared

def handle_error(error, shared, args_obj):
    """Handle errors gracefully with user-friendly messages."""
    print(f"[ERROR] An unexpected error occurred: {error}")
    if shared.get('verbose', False):
        import traceback
        traceback.print_exc()
    sys.exit(1)

def setup_llm_proxy(args):
    """Always use AlchemistAIProxy for all LLM calls."""
    return AlchemistAIProxy()

def run_sync_flow(flow, shared):
    """Run a synchronous flow."""
    return flow.run(shared)

def chat_with_theagent(args_obj, llm_proxy):
    """Enhanced chat function with better context awareness and error handling."""
    print("\n[TheAgent Chat] Type your instructions or questions. Type 'exit' to quit.")
    print("[TIP] Try: 'list files', 'read main.py', 'generate docstrings for main.py', or ask general questions.\n")
    
    shared = setup_shared_context(args_obj)
    
    # Use enhanced flow for better intent recognition
    flow = create_chat_flow(args_obj, llm_proxy)
    
    while True:
        try:
            user_input = input('You: ')
            if user_input.strip().lower() in {'exit', 'quit', 'bye'}:
                print('[GOODBYE] Thanks for using TheAgent!')
                break
            
            # Add user message to history
            shared['history'].append({'role': 'user', 'content': user_input})
            
            # Update instruction for the flow
            args_obj.instruction = user_input
            
            # Run the enhanced flow
            try:
                result = flow.run(shared)
                if result:
                    print(f"TheAgent: {result}")
                    shared['history'].append({'role': 'agent', 'content': result})
            except Exception as e:
                handle_error(e, shared, args_obj)
                # Try to recover gracefully
                print("[RECOVER] Attempting to recover...")
                shared['last_error'] = e
                
        except KeyboardInterrupt:
            print("\n\n[GOODBYE] Chat interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n[GOODBYE] End of input. Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            print("[RESTART] Restarting chat...")
            shared = setup_shared_context(args_obj)

def main():
    """Main entry point for TheAgent."""
    parser = argparse.ArgumentParser(description="TheAgent - AI-powered code assistant")
    
    # File and agent options
    parser.add_argument("--file", "-f", help="Python file to process")
    parser.add_argument("--agent", "-a", choices=["doc", "summary", "test", "bug", "refactor", "type", "migration"], 
                       help="Type of agent to use")
    
    # Output options
    parser.add_argument("--output", "-o", choices=["console", "in-place", "new-file"], 
                       default="console", help="Output mode")
    
    # LLM options
    parser.add_argument("--llm", choices=["alchemyst", "openai", "anthropic", "ollama"], 
                       default="alchemyst", help="LLM provider to use")
    
    # Enhanced features
    parser.add_argument("--enhanced", action="store_true", 
                       help="Use enhanced flow with safety checks and user approval")
    parser.add_argument("--chat", action="store_true", 
                       help="Start interactive chat mode")
    
    # Other options
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--no-confirm", action="store_true", 
                       help="Skip user confirmation prompts")
    parser.add_argument("--migration-target", default="Python 3", 
                       help="Target for code migration")
    
    args_obj = parser.parse_args()
    
    # Setup shared data
    shared = {
        "verbose": args_obj.verbose,
        "no_confirm": args_obj.no_confirm
    }
    
    try:
        # Setup LLM proxy
        llm_proxy = setup_llm_proxy(args_obj)
        
        # Handle different modes
        if args_obj.chat:
            # Chat mode
            print("[INFO] Starting chat mode...")
            chat_with_theagent(args_obj, llm_proxy)
        elif args_obj.file and args_obj.agent:
            # File processing mode
            print("[INFO] Starting processing...")
            if args_obj.enhanced:
                flow = create_enhanced_agent_flow(args_obj, llm_proxy)
            else:
                if args_obj.agent == "doc":
                    flow = create_doc_agent_flow(args_obj, llm_proxy)
                elif args_obj.agent == "summary":
                    # Use simple enhanced flow for summary since there's no dedicated summary flow
                    flow = create_simple_enhanced_flow(args_obj, llm_proxy)
                else:
                    flow = create_simple_enhanced_flow(args_obj, llm_proxy)
            run_sync_flow(flow, shared)
        else:
            # No valid mode specified
            parser.print_help()
            return
        
        print("[SUCCESS] Processing complete!")
        
    except Exception as e:
        handle_error(e, shared, args_obj)

if __name__ == "__main__":
    main()
