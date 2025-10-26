#!/usr/bin/env python3
"""
Test script showing executor with workflow dictionary loading
"""

from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

print("=" * 70)
print("Testing Executor Workflow Loading")
print("=" * 70)
print()

# Initialize executor
memory = VisualWorkflowMemory()
executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

print()
print("=" * 70)
print("LOADED WORKFLOWS BY INTENTION")
print("=" * 70)

# Show all loaded workflows
for intention, actions in executor.workflows_by_intention.items():
    print(f"\n📌 Intention: {intention}")
    print(f"   Total Actions: {len(actions)}")
    print(f"   Action Types: {', '.join(set(a['semantic_type'] for a in actions))}")

    # Show first 3 actions
    print(f"\n   First Actions:")
    for i, action in enumerate(actions[:3], 1):
        desc = action.get('description', 'N/A')
        if len(desc) > 70:
            desc = desc[:67] + "..."
        print(f"     {i}. [{action['semantic_type']}] {desc}")

    if len(actions) > 3:
        print(f"     ... and {len(actions) - 3} more")

print()
print("=" * 70)
print("TESTING INTENTION MATCHING")
print("=" * 70)

# Test fuzzy matching
test_queries = [
    "check syllabus",
    "navigate Canvas",
    "view course syllabus"
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    actions = executor.get_workflow_by_intention(query)
    if actions:
        print(f"  ✅ Found workflow with {len(actions)} actions")
    else:
        print(f"  ❌ No matching workflow found")

print()
print("=" * 70)
print("ACCESSING WORKFLOWS DICTIONARY")
print("=" * 70)
print()
print("You can access workflows directly:")
print(f"  executor.workflows_by_intention -> Dict with {len(executor.workflows_by_intention)} entries")
print()
print("Example usage in your code:")
print("""
  # Get all intentions
  intentions = list(executor.workflows_by_intention.keys())

  # Get semantic actions for an intention
  actions = executor.workflows_by_intention[intention]

  # Or use fuzzy matching
  actions = executor.get_workflow_by_intention("check syllabus")
""")

print("=" * 70)
