#!/usr/bin/env python3
"""
Workflow CLI - Simple command-line interface for the Intelligent Workflow System

Usage:
    python workflow_cli.py                    # Interactive mode
    python workflow_cli.py execute "prompt"   # Execute workflow
    python workflow_cli.py list               # List workflows
    python workflow_cli.py record "name"      # Start recording
"""

import sys
import argparse
from intelligent_workflow_system import IntelligentWorkflowSystem


def interactive_mode(system: IntelligentWorkflowSystem):
    """Interactive command-line mode"""
    system.demo_mode()


def execute_prompt(system: IntelligentWorkflowSystem, prompt: str, auto: bool = False):
    """Execute workflow from prompt"""
    success = system.execute_from_prompt(prompt, auto_execute=auto)
    sys.exit(0 if success else 1)


def list_workflows(system: IntelligentWorkflowSystem):
    """List all workflows"""
    system.list_workflows()


def record_workflow(system: IntelligentWorkflowSystem, name: str, description: str = ""):
    """Start recording a workflow"""
    print("\n⚠️  Note: Recording requires manual stop_recording() call")
    print("    Best used from Python REPL or notebook")
    print()
    
    workflow_id = system.record_workflow(name, description=description)
    
    print("\nTo stop recording, run:")
    print("    python -c 'from intelligent_workflow_system import IntelligentWorkflowSystem; ")
    print("              system = IntelligentWorkflowSystem(); system.stop_recording()'")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Intelligent Workflow Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s execute "Close Jira ticket ABC"   # Execute workflow
  %(prog)s list                               # List all workflows
  %(prog)s record "My Workflow"               # Start recording
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['execute', 'list', 'record'],
        help='Command to run (default: interactive mode)'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-execute without confirmation (for execute command)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Verbose output (default: True)'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    try:
        system = IntelligentWorkflowSystem(verbose=args.verbose)
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        sys.exit(1)
    
    # Handle commands
    if args.command == 'execute':
        if not args.args:
            print("❌ Error: execute command requires a prompt")
            print("Usage: workflow_cli.py execute \"your prompt here\"")
            sys.exit(1)
        
        prompt = ' '.join(args.args)
        execute_prompt(system, prompt, auto=args.auto)
    
    elif args.command == 'list':
        list_workflows(system)
    
    elif args.command == 'record':
        if not args.args:
            print("❌ Error: record command requires a workflow name")
            print("Usage: workflow_cli.py record \"Workflow Name\" [description]")
            sys.exit(1)
        
        name = args.args[0]
        description = ' '.join(args.args[1:]) if len(args.args) > 1 else ""
        record_workflow(system, name, description)
    
    else:
        # Default: interactive mode
        interactive_mode(system)


if __name__ == "__main__":
    main()

