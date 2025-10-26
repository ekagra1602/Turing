"""
Intelligent Workflow System
Main interface for learning, matching, and executing workflows based on prompts

This is the core system that enables:
- "If I closed one Jira ticket, close another"
- "If I filled one job application, fill 5 more"
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pyautogui

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import GenerateContentConfig

# Support both Snowflake and local storage
try:
    from snowflake_workflow_memory import SnowflakeWorkflowMemory
    SNOWFLAKE_AVAILABLE = True
except:
    SNOWFLAKE_AVAILABLE = False

from visual_memory import VisualWorkflowMemory
from semantic_workflow_matcher import SemanticWorkflowMatcher
from gemini_workflow_executor import GeminiWorkflowExecutor
from recorder import WorkflowRecorder


class IntelligentWorkflowSystem:
    """
    The complete intelligent workflow automation system.
    
    Workflow:
    1. User says: "Close a Jira ticket"
    2. System finds: Similar past workflow (e.g., "close jira ticket for bug-123")
    3. System extracts: Parameters (ticket number, etc.)
    4. System executes: Adapted workflow using Gemini's vision
    """
    
    def __init__(self, verbose: bool = True, use_snowflake: bool = True):
        """
        Initialize the intelligent workflow system
        
        Args:
            verbose: Print detailed logs
            use_snowflake: Use Snowflake cloud storage (default: True for demos)
        """
        self.verbose = verbose
        
        # ALWAYS use local storage (Snowflake kept for demo connection only)
        self.memory = VisualWorkflowMemory()
        self.storage_type = "Local Files + Snowflake Demo"
        
        # Connect to Snowflake for demo (but don't use it for storage)
        if use_snowflake and SNOWFLAKE_AVAILABLE:
            try:
                self.snowflake_demo = SnowflakeWorkflowMemory()
            except:
                self.snowflake_demo = None
        else:
            self.snowflake_demo = None
        
        # Core components (all use the same memory backend)
        self.matcher = SemanticWorkflowMatcher(memory=self.memory, use_snowflake=use_snowflake)
        self.executor = GeminiWorkflowExecutor(memory=self.memory, verbose=verbose)
        self.recorder = WorkflowRecorder(memory=self.memory)
        
        # Gemini client for parameter extraction
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.gemini_client = genai.Client(api_key=self.api_key)
        else:
            print("⚠️  GOOGLE_API_KEY not set - parameter extraction disabled")
            self.gemini_client = None
        
        print("=" * 70)
        print("🧠 INTELLIGENT WORKFLOW SYSTEM")
        print("=" * 70)
        print(f"✅ All systems ready!")
        print(f"   Storage: {self.storage_type}")
        print()
    
    def execute_from_prompt(self, 
                           user_prompt: str,
                           auto_execute: bool = False,
                           confirm_steps: bool = False) -> bool:
        """
        Main method: Execute workflow from natural language prompt
        
        Args:
            user_prompt: What the user wants to do
                        e.g., "Close Jira ticket ABC-123"
                        e.g., "Fill out job application for Google"
            auto_execute: Execute without confirmation
            confirm_steps: Ask before each step
        
        Returns:
            True if successful
        """
        print("\n" + "=" * 70)
        print(f"💬 USER REQUEST: {user_prompt}")
        print("=" * 70)
        
        # Step 1: Find similar workflows (for guidance, not required)
        print("\n🔍 Finding similar workflows...")
        matches = self.matcher.find_similar_workflows(user_prompt, top_k=3, min_similarity=0.3)
        
        if not matches:
            print("\n⚠️  No matching workflows found")
            print("   → Executing request directly using Gemini...\n")
            
            # Execute directly without workflow matching
            return self._execute_direct(user_prompt, confirm_steps)
        
        # Show matches
        print(f"\n✓ Found {len(matches)} similar workflow(s):")
        for i, (workflow, similarity) in enumerate(matches, 1):
            print(f"\n{i}. {workflow['name']} (similarity: {similarity:.0%})")
            if workflow.get('description'):
                print(f"   {workflow['description']}")
        
        # Select best match (or let user choose)
        best_workflow, best_similarity = matches[0]
        
        if not auto_execute and len(matches) > 1:
            print("\nWhich workflow should I use?")
            choice = input(f"Enter 1-{len(matches)} or press Enter for #1: ").strip()
            if choice and choice.isdigit() and 1 <= int(choice) <= len(matches):
                best_workflow, best_similarity = matches[int(choice) - 1]
        
        print(f"\n✓ Selected: '{best_workflow['name']}'")
        
        # Step 2: Extract parameters
        print("\n🎯 Extracting parameters from your request...")
        parameters = self._extract_parameters(user_prompt, best_workflow)
        
        if parameters:
            print("\n✓ Extracted parameters:")
            for key, value in parameters.items():
                print(f"   {key} = {value}")
        else:
            print("   (No parameters needed)")
        
        # Step 3: Confirm execution
        if not auto_execute:
            print("\n" + "-" * 70)
            print(f"Ready to execute: {best_workflow['name']}")
            if parameters:
                print(f"With parameters: {json.dumps(parameters, indent=2)}")
            
            response = input("\nExecute this workflow? [y/n]: ").lower()
            if response != 'y':
                print("❌ Execution cancelled")
                return False
        
        # Step 4: Execute workflow
        print("\n🚀 Executing workflow...")
        success, results = self.executor.execute_workflow(
            workflow=best_workflow,
            parameters=parameters,
            confirm_steps=confirm_steps
        )
        
        return success
    
    def _execute_direct(self, user_prompt: str, confirm_steps: bool = False) -> bool:
        """
        Execute a request directly using Gemini without workflow matching
        
        This is used when no matching workflows exist.
        Gemini breaks down the request into actions and executes them.
        
        Args:
            user_prompt: User's natural language request
            confirm_steps: Ask before each step
        
        Returns:
            True if successful
        """
        if not self.gemini_client:
            print("❌ Gemini client not available")
            return False
        
        print("🤖 Analyzing request and planning actions...")
        
        # Ask Gemini to break down the request into actionable steps
        planning_prompt = f"""You are a computer automation assistant. The user wants to: "{user_prompt}"

Break this down into specific, actionable steps that can be executed on a computer.

Return a JSON array of actions:
[
    {{
        "action_type": "open_application" | "click" | "type" | "key" | "scroll" | "wait",
        "target": "description of what to interact with (for click/open_application)",
        "value": "text to type (for type) or key name (for key) or wait seconds (for wait)",
        "description": "human-readable description of this step"
    }},
    ...
]

Rules:
- Be specific (e.g., "Chrome browser" not just "browser")
- For clicks, describe the element clearly (e.g., "GitHub search bar", "username field")
- Include reasonable wait times between actions
- Keep it simple - 3-10 steps max
- Only include steps that are directly needed

Example for "open github":
[
    {{"action_type": "open_application", "target": "Chrome", "description": "Open web browser"}},
    {{"action_type": "wait", "value": "2", "description": "Wait for browser to load"}},
    {{"action_type": "click", "target": "address bar", "description": "Click address bar"}},
    {{"action_type": "type", "value": "github.com", "description": "Type GitHub URL"}},
    {{"action_type": "key", "value": "enter", "description": "Press Enter to navigate"}}
]

CRITICAL RULES FOR macOS:
- Apps are opened using Raycast launcher (Option + Space shortcut)
- NEVER use target="Raycast" - Raycast is the LAUNCHER itself, not an app to open
- For any app (Chrome, Safari, Twitter, etc.), use "open_application" with the app name
- The system will automatically use Raycast to open it
- Example: target="Chrome" will trigger: Option+Space → type "Chrome" → Enter

Be very specific with click targets (e.g., "address bar at top of browser window")
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=planning_prompt,
                config=GenerateContentConfig(temperature=0.1, max_output_tokens=2048)
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            actions = json.loads(content)
            
            if not isinstance(actions, list) or not actions:
                print("❌ Could not generate action plan")
                return False
            
            print(f"\n✓ Generated {len(actions)} actions\n")
            
            # Show action plan
            if self.verbose:
                print("📋 Action Plan:")
                print("-" * 70)
                for i, action in enumerate(actions, 1):
                    print(f"{i}. {action.get('description', action.get('action_type'))}")
                print("-" * 70)
                print()
            
            # Confirm execution?
            if confirm_steps:
                response = input("Proceed with execution? [y/n]: ").lower()
                if response != 'y':
                    print("❌ Execution cancelled")
                    return False
            
            # Execute each action
            print("🚀 Executing actions...\n")
            print("⚠️  Minimizing terminal to prevent focus issues...")
            print("   (Terminal will auto-restore after execution)\n")
            
            # Minimize terminal window to prevent typing in it
            try:
                pyautogui.hotkey('command', 'm')  # Minimize window on Mac
                time.sleep(0.5)
            except:
                pass
            
            for i, action in enumerate(actions, 1):
                action_type = action.get('action_type', '').lower()
                target = action.get('target', '')
                value = action.get('value', '')
                description = action.get('description', action_type)
                
                print(f"📍 Step {i}/{len(actions)}: {description}")
                
                try:
                    if action_type == "open_application":
                        # Use pyautogui to open application
                        print(f"   🚀 Opening: {target}")
                        # Use Raycast (option + space) instead of Spotlight
                        pyautogui.hotkey('option', 'space')
                        time.sleep(0.7)  # Wait for Raycast to open
                        pyautogui.write(target, interval=0.05)
                        time.sleep(0.5)  # Wait for results
                        pyautogui.press('return')
                        time.sleep(2.5)  # Wait for app to fully open and become focused
                        print("   ✓ Done")
                    
                    elif action_type == "click":
                        # Use Gemini to find and click element
                        print(f"   🖱️  Clicking: {target}")
                        success = self.executor.gemini.click(target)
                        if success:
                            print("   ✓ Click successful")
                        else:
                            print("   ⚠️  Click may have failed")
                        time.sleep(0.5)
                    
                    elif action_type == "type":
                        # Type text
                        print(f"   ⌨️  Typing: {value[:50]}...")
                        # Small delay to ensure focus is correct
                        time.sleep(0.2)
                        pyautogui.write(value, interval=0.05)
                        print("   ✓ Done")
                        time.sleep(0.3)
                    
                    elif action_type == "key":
                        # Press key
                        print(f"   ⌨️  Pressing: {value}")
                        pyautogui.press(value)
                        print("   ✓ Done")
                        time.sleep(0.5)
                    
                    elif action_type == "wait":
                        # Wait
                        wait_time = float(value) if value else 1.0
                        print(f"   ⏳ Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        print("   ✓ Done")
                    
                    elif action_type == "scroll":
                        # Scroll
                        print(f"   📜 Scrolling...")
                        pyautogui.scroll(-300)  # Scroll down
                        print("   ✓ Done")
                        time.sleep(0.5)
                    
                    else:
                        print(f"   ⚠️  Unknown action type: {action_type}")
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    if not confirm_steps:
                        # Continue anyway
                        continue
                    else:
                        response = input("   Continue? [y/n]: ").lower()
                        if response != 'y':
                            print("❌ Execution stopped")
                            return False
                
                print()
            
            print("=" * 70)
            print("✅ EXECUTION COMPLETED")
            print("=" * 70)
            
            # Bring terminal back to focus
            try:
                # Click on terminal in dock or use Cmd+Tab
                time.sleep(1)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Direct execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_parameters(self, user_prompt: str, workflow: Dict) -> Dict[str, str]:
        """
        Extract parameter values from user prompt using Gemini
        
        Args:
            user_prompt: User's natural language request
            workflow: Matched workflow
        
        Returns:
            Dictionary of parameter values
        """
        if not self.gemini_client:
            return {}
        
        # Get workflow context
        workflow_name = workflow['name']
        workflow_desc = workflow.get('description', '')
        
        # Load workflow to see what parameters it needs
        try:
            full_workflow = self.memory.get_workflow(workflow['workflow_id'])
            steps = full_workflow.get('steps', [])
            
            # Analyze steps to find parameterizable elements
            # Look for things like text that was typed, clicked elements, etc.
            
        except:
            steps = []
        
        # Use Gemini to extract parameters
        prompt = f"""Analyze this user request and extract relevant parameters.

User Request: "{user_prompt}"
Workflow: "{workflow_name}"
Description: "{workflow_desc}"

Based on the request, extract any specific values the user wants to use.
For example:
- Ticket numbers (e.g., "ABC-123")
- Company names (e.g., "Google")
- Course names (e.g., "Machine Learning")
- File names
- Search terms
- Etc.

Return a JSON object with parameter names and values:
{{
    "param_name": "value",
    ...
}}

If no parameters needed, return {{}}
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=GenerateContentConfig(temperature=0.1)
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parameters = json.loads(content)
            return parameters if isinstance(parameters, dict) else {}
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Parameter extraction failed: {e}")
            return {}
    
    def record_workflow(self, workflow_name: str, description: str = "", tags: List[str] = None):
        """
        Start recording a new workflow
        
        Args:
            workflow_name: Name for this workflow
            description: What it does
            tags: Optional tags
        
        Returns:
            workflow_id
        """
        print("\n" + "=" * 70)
        print("🔴 RECORDING STARTED")
        print("=" * 70)
        
        workflow_id = self.recorder.start_recording(
            workflow_name=workflow_name,
            description=description,
            tags=tags
        )
        
        print(f"\n✅ Now recording: {workflow_name}")
        print()
        print("📝 What to do:")
        print("   1. Perform your workflow now (I'm watching!)")
        print("   2. Click, type, navigate - do whatever you need")
        print()
        print("⏹  When done, type: stop")
        print()
        print("=" * 70)
        
        return workflow_id
    
    def stop_recording(self):
        """Stop recording and finalize workflow"""
        return self.recorder.stop_recording()
    
    def list_workflows(self):
        """List all learned workflows"""
        workflows = self.memory.list_workflows(status='ready')
        
        if not workflows:
            print("\n📚 No learned workflows yet")
            print("\n💡 Record your first workflow:")
            print("   system.record_workflow('Close Jira Ticket')")
            return
        
        print("\n" + "=" * 70)
        print(f"📚 LEARNED WORKFLOWS ({len(workflows)} total)")
        print("=" * 70)
        
        for i, wf in enumerate(workflows, 1):
            print(f"\n{i}. {wf['name']}")
            if wf.get('description'):
                print(f"   {wf['description']}")
            if wf.get('tags'):
                print(f"   Tags: {', '.join(wf['tags'])}")
            print(f"   Used: {wf.get('use_count', 0)} times")
        
        print("\n" + "=" * 70)
    
    def demo_mode(self):
        """Interactive demo mode"""
        print("\n" + "=" * 70)
        print("🎮 DEMO MODE")
        print("=" * 70)
        print()
        print("Commands:")
        print("  - Type a natural language request")
        print("  - 'list' - Show all workflows")
        print("  - 'record <name>' - Start recording")
        print("  - 'stop' - Stop recording")
        print("  - 'quit' - Exit demo mode")
        print()
        
        while True:
            try:
                # Show if currently recording
                if self.recorder.is_recording:
                    user_input = input("\n🔴 RECORDING > Type 'stop' to finish: ").strip()
                else:
                    user_input = input("\n💬 Your request: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    if self.recorder.is_recording:
                        print("\n⚠️  Still recording! Type 'stop' first, then 'quit'")
                        continue
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'list':
                    self.list_workflows()
                
                elif user_input.lower().startswith('record '):
                    if self.recorder.is_recording:
                        print("\n⚠️  Already recording! Type 'stop' first")
                        continue
                    workflow_name = user_input[7:].strip()
                    if workflow_name:
                        self.record_workflow(workflow_name)
                    else:
                        print("Usage: record <workflow name>")
                
                elif user_input.lower() == 'stop':
                    if not self.recorder.is_recording:
                        print("\n⚠️  Not recording anything")
                    else:
                        self.stop_recording()
                
                else:
                    if self.recorder.is_recording:
                        print("\n⚠️  Currently recording - type 'stop' to finish recording first")
                        continue
                    # Execute from prompt
                    self.execute_from_prompt(user_input, auto_execute=False, confirm_steps=False)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Type 'quit' to exit.")
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    print()
    print("=" * 70)
    print("🚀 INTELLIGENT WORKFLOW AUTOMATION SYSTEM")
    print("=" * 70)
    print()
    print("Learn workflows by demonstration, then execute them with prompts!")
    print()
    print("Examples:")
    print("  • 'Close Jira ticket ABC-123'")
    print("  • 'Download files from Canvas for Machine Learning class'")
    print("  • 'Fill out job application for Google'")
    print()
    
    # Initialize system
    system = IntelligentWorkflowSystem(verbose=True)
    
    # Show available workflows
    system.list_workflows()
    
    print("\n" + "=" * 70)
    print("Ready! Try:")
    print("  system.execute_from_prompt('your request here')")
    print("  system.record_workflow('Workflow Name')")
    print("  system.demo_mode()  # Interactive mode")
    print("=" * 70)
    
    return system


if __name__ == "__main__":
    system = main()
    
    # Optionally start demo mode
    import sys
    if '--demo' in sys.argv:
        system.demo_mode()

