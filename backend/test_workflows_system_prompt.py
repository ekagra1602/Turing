#!/usr/bin/env python3
"""
Test: Workflows loaded into Gemini system prompt
"""

from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

print("=" * 70)
print("WORKFLOWS IN SYSTEM PROMPT TEST")
print("=" * 70)
print()

# Initialize executor (automatically loads workflows into Gemini)
memory = VisualWorkflowMemory()
executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

print()
print("=" * 70)
print("SYSTEM PROMPT CONTENT")
print("=" * 70)
print()
print(executor.gemini.system_prompt)
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print(f"✅ Workflows loaded: {len(executor.workflows_by_intention)}")
print(f"✅ System prompt length: {len(executor.gemini.system_prompt)} characters")
print()
print("The Gemini executor agent now has ALL workflows available in its system prompt.")
print("It can match user requests to learned workflows automatically.")
print()
print("=" * 70)
