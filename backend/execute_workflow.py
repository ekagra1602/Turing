#!/usr/bin/env python3
"""
Execute Workflow - Interactive CLI
Choose and execute any learned workflow with parameters
"""

from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory


def main():
    print("=" * 70)
    print("AgentFlow - Execute Workflow")
    print("=" * 70)
    print()

    # Initialize
    print("Loading workflows...")
    memory = VisualWorkflowMemory()
    executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

    # List available workflows
    workflows = memory.list_workflows(status='ready')

    if not workflows:
        print()
        print("❌ No workflows available!")
        print()
        print("To record a workflow:")
        print("  ./START_RECORDER.sh")
        print()
        return

    print()
    print("=" * 70)
    print("Available Workflows")
    print("=" * 70)
    print()

    for i, wf in enumerate(workflows, 1):
        print(f"{i}. {wf['name']}")
        print(f"   Goal: {wf.get('description', 'N/A')}")
        print(f"   Steps: {wf['steps_count']}")
        if wf.get('tags'):
            print(f"   Tags: {', '.join(wf['tags'])}")

        # Show parameters
        full_wf = memory.get_workflow(wf['workflow_id'])
        if full_wf.get('parameters'):
            print(f"   Parameters:")
            for param in full_wf['parameters']:
                print(f"     • {param['name']}: {param.get('description', 'N/A')}")
        print()

    # Choose workflow
    try:
        choice = int(input("Select workflow (number): ")) - 1
        if choice < 0 or choice >= len(workflows):
            print("❌ Invalid selection")
            return
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Cancelled")
        return

    workflow = workflows[choice]
    full_workflow = memory.get_workflow(workflow['workflow_id'])

    print()
    print(f"Selected: {workflow['name']}")
    print()

    # Get parameters if needed
    parameters = {}
    if full_workflow.get('parameters'):
        print("This workflow requires parameters:")
        print()
        for param in full_workflow['parameters']:
            print(f"Parameter: {param['name']}")
            print(f"  Description: {param.get('description', 'N/A')}")
            print(f"  Example: {param.get('example_value', param.get('example', 'N/A'))}")
            value = input(f"  Enter value: ").strip()
            if value:
                parameters[param['name']] = value
            print()

    # Confirm execution
    print("=" * 70)
    print("Ready to Execute")
    print("=" * 70)
    print(f"Workflow: {workflow['name']}")
    print(f"Steps: {workflow['steps_count']}")
    if parameters:
        print(f"Parameters:")
        for k, v in parameters.items():
            print(f"  {k} = {v}")
    print()

    confirm = input("Execute workflow? [y/n]: ").lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return

    # Execute!
    print()
    print("=" * 70)
    print("🚀 EXECUTING WORKFLOW")
    print("=" * 70)
    print()

    success, results = executor.execute_workflow(full_workflow, parameters)

    print()
    print("=" * 70)
    if success:
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        print("⚠️  WORKFLOW COMPLETED WITH ERRORS")
    print("=" * 70)
    print()

    # Show summary
    if results:
        successful = sum(1 for r in results if r.get('success', False))
        print(f"Steps executed: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
