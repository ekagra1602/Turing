#!/usr/bin/env python3
"""
AgentFlow - Conversational Computer Control Agent
Type what you want, AI figures it out and does it.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

import pyautogui

from google import genai
from google.genai import types
from google.genai.types import Content, Part

from computer_use_simple import run_computer_use_task


# Memory file for storing workflows and context
MEMORY_FILE = Path(__file__).parent / "agent_memory.json"


class AgentMemory:
    """Stores workflows, patterns, and context for the agent."""

    def __init__(self):
        self.workflows = {}
        self.context = {}
        self.history = []
        self.load()

    def load(self):
        """Load memory from disk."""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.workflows = data.get('workflows', {})
                    self.context = data.get('context', {})
                    self.history = data.get('history', [])
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")

    def save(self):
        """Save memory to disk."""
        try:
            with open(MEMORY_FILE, 'w') as f:
                json.dump({
                    'workflows': self.workflows,
                    'context': self.context,
                    'history': self.history
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")

    def add_workflow(self, name: str, description: str, steps: list):
        """Store a workflow pattern."""
        self.workflows[name] = {
            'description': description,
            'steps': steps,
            'created': datetime.now().isoformat(),
            'uses': 0
        }
        self.save()

    def get_workflow(self, name: str):
        """Retrieve a workflow."""
        return self.workflows.get(name)

    def increment_workflow_use(self, name: str):
        """Track workflow usage."""
        if name in self.workflows:
            self.workflows[name]['uses'] += 1
            self.save()

    def add_context(self, key: str, value: str):
        """Store contextual information."""
        self.context[key] = value
        self.save()

    def get_context(self, key: str):
        """Get contextual information."""
        return self.context.get(key)

    def add_to_history(self, task: str, result: str):
        """Add task to history."""
        self.history.append({
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last 50 tasks
        self.history = self.history[-50:]
        self.save()

    def get_relevant_context(self) -> str:
        """Get context summary for AI."""
        context_str = "## Previous Context\n\n"

        # Recent history
        if self.history:
            context_str += "Recent tasks:\n"
            for item in self.history[-5:]:
                context_str += f"- {item['task']}\n"

        # Known workflows
        if self.workflows:
            context_str += "\nKnown workflows:\n"
            for name, workflow in self.workflows.items():
                context_str += f"- {name}: {workflow['description']}\n"

        # User context
        if self.context:
            context_str += "\nUser preferences:\n"
            for key, value in self.context.items():
                context_str += f"- {key}: {value}\n"

        return context_str


class AgentInterface:
    """Main conversational interface for computer control."""

    def __init__(self):
        self.memory = AgentMemory()
        self.client = genai.Client()

    def open_application(self, app_name: str, url: str = None):
        """Open a macOS application, optionally with a URL."""
        try:
            if url and app_name.lower() == 'safari':
                # Open Safari with specific URL
                subprocess.run(['open', '-a', 'Safari', url], check=True)
                print(f"✅ Opened Safari at {url}")
            else:
                subprocess.run(['open', '-a', app_name], check=True)
                print(f"✅ Opened {app_name}")
            time.sleep(3)  # Wait for app to open and load
            return True
        except Exception as e:
            print(f"❌ Could not open {app_name}: {e}")
            return False

    def prepare_task(self, user_input: str) -> str:
        """
        Use AI to understand user intent and create detailed task instructions.
        This is the "planning" phase.
        """
        context = self.memory.get_relevant_context()

        planning_prompt = f"""You are an AI assistant that helps plan computer automation tasks.

{context}

The user wants: "{user_input}"

Your job is to:
1. Understand what application(s) are needed
2. Determine if this matches a known workflow
3. Create detailed step-by-step instructions for the computer control AI

Respond in this format:

APPLICATION: [Safari/Chrome/Finder/etc., or "Already Open" if not needed]
URL: [If opening Safari, what URL to start at, or "N/A"]
WORKFLOW: [Name of similar workflow if exists, or "New"]
INSTRUCTIONS:
[Detailed step-by-step instructions for the screen control AI]
PARAMETERS:
[Any specific values/inputs needed, as key: value]

Be specific about:
- What to click
- What to type
- What to look for
- What information to extract

Examples:
- If user says "check my Canvas classes", APPLICATION: Safari, URL: https://canvas.asu.edu
- If user says "find flights", APPLICATION: Safari, URL: https://www.google.com/flights
"""

        response = self.client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=planning_prompt
        )

        return response.text

    def execute_task(self, user_input: str):
        """Execute a user task end-to-end."""

        print("\n" + "=" * 70)
        print(f"📋 Task: {user_input}")
        print("=" * 70)

        # Step 1: Planning phase
        print("\n🧠 Planning...")
        plan = self.prepare_task(user_input)
        print("\nPlan:")
        print(plan)

        # Parse the plan
        lines = plan.split('\n')
        app_needed = None
        url = None
        workflow_name = None
        instructions = []
        parameters = {}

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('APPLICATION:'):
                app_needed = line.split(':', 1)[1].strip()
            elif line.startswith('URL:'):
                url = line.split(':', 1)[1].strip()
                if url.lower() in ['n/a', 'none']:
                    url = None
            elif line.startswith('WORKFLOW:'):
                workflow_name = line.split(':', 1)[1].strip()
            elif line.startswith('INSTRUCTIONS:'):
                current_section = 'instructions'
            elif line.startswith('PARAMETERS:'):
                current_section = 'parameters'
            elif current_section == 'instructions' and line:
                instructions.append(line)
            elif current_section == 'parameters' and line and ':' in line:
                key, value = line.split(':', 1)
                parameters[key.strip()] = value.strip()

        # Step 2: Open application if needed
        if app_needed and app_needed.lower() not in ['already open', 'none', 'n/a']:
            print(f"\n🚀 Opening {app_needed}...")
            self.open_application(app_needed, url=url)

        # Step 3: Auto-start with short delay (FULLY AUTONOMOUS)
        print("\n" + "=" * 70)
        print("🚀 AUTO-STARTING IN 5 SECONDS...")
        print("=" * 70)
        print("DON'T TOUCH YOUR MOUSE OR KEYBOARD!")
        print("The AI will take control automatically...")
        print()

        for i in range(5, 0, -1):
            print(f"   Starting in {i}...")
            time.sleep(1)

        # Step 4: Execute
        print("\n" + "=" * 70)
        print("🤖 AI IS NOW CONTROLLING YOUR SCREEN!")
        print("=" * 70)
        print("Watch the mouse move automatically...")
        print("Press Ctrl+C at any time to stop")
        print("=" * 70)
        print()

        # Build the task with context
        full_task = f"""
User Goal: {user_input}

{self.memory.get_relevant_context()}

Detailed Instructions:
{chr(10).join(instructions)}

Parameters:
{json.dumps(parameters, indent=2)}

IMPORTANT: Look at the current screen first and see what's visible.
Then execute the task step by step.
Be thorough and accurate. Report what you found when done.
"""

        try:
            print("\n" + "=" * 70)
            print("🎬 EXECUTING TASK...")
            print("=" * 70)
            print()
            result = run_computer_use_task(full_task, turn_limit=30, verbose=True)
            print("\n" + "=" * 70)
            print("✅ Task execution completed")
            print("=" * 70)

            # Step 5: Store results
            self.memory.add_to_history(user_input, result)

            # Step 6: Learn workflow (if new pattern)
            if workflow_name and workflow_name.lower() == 'new':
                print("\n💡 This looks like a new workflow pattern!")
                learn = input("Should I remember this workflow for next time? [Y/n]: ").strip().lower()
                if learn != 'n':
                    workflow_name = input("Give this workflow a name: ").strip()
                    if workflow_name:
                        self.memory.add_workflow(
                            workflow_name,
                            user_input,
                            instructions
                        )
                        print(f"✅ Workflow '{workflow_name}' saved!")

            return result

        except KeyboardInterrupt:
            print("\n\n⚠️ Stopped by user")
            return None
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def chat_loop(self):
        """Main interactive loop."""
        print("\n" + "=" * 70)
        print("🤖 AgentFlow - Your AI Computer Assistant")
        print("=" * 70)
        print()
        print("Tell me what you want to do, and I'll do it for you!")
        print()
        print("Examples:")
        print("  - Check my Canvas classes")
        print("  - Find the cheapest flights to SF next week")
        print("  - Search for Python tutorials on YouTube")
        print("  - Download my bank statement")
        print()
        print("Commands:")
        print("  - 'quit' or 'exit' to quit")
        print("  - 'memory' to see what I remember")
        print("  - 'clear' to clear history")
        print()
        print("=" * 70)

        while True:
            try:
                user_input = input("\n💬 What do you want me to do? ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if user_input.lower() == 'memory':
                    print("\n" + self.memory.get_relevant_context())
                    continue

                if user_input.lower() == 'clear':
                    confirm = input("Clear all history? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        self.memory.history = []
                        self.memory.save()
                        print("✅ History cleared")
                    continue

                # Execute the task
                result = self.execute_task(user_input)

                if result:
                    print("\n" + "=" * 70)
                    print("✅ RESULT:")
                    print("=" * 70)
                    print(result)
                    print("=" * 70)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Main entry point."""

    # Check API key
    if "GOOGLE_API_KEY" not in os.environ:
        print("❌ Error: GOOGLE_API_KEY not set")
        print("Set it with: export GOOGLE_API_KEY='your_key_here'")
        sys.exit(1)

    # Create interface
    agent = AgentInterface()

    # Start chat loop
    agent.chat_loop()


if __name__ == "__main__":
    main()
