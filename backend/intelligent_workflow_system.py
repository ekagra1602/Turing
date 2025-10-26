"""
Intelligent Workflow System
Main interface for learning, matching, and executing workflows based on prompts

This is the core system that enables:
- "If I closed one Jira ticket, close another"
- "If I filled one job application, fill 5 more"
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

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
        
        # Choose memory backend: Snowflake (cloud) or local files
        if use_snowflake and SNOWFLAKE_AVAILABLE:
            self.memory = SnowflakeWorkflowMemory()
            self.storage_type = "Snowflake Cloud"
        else:
            if use_snowflake and not SNOWFLAKE_AVAILABLE:
                print("⚠️  Snowflake requested but not available, using local storage")
            self.memory = VisualWorkflowMemory()
            self.storage_type = "Local Files"
        
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
        
        # Step 1: Find similar workflows
        print("\n🔍 Finding similar workflows...")
        matches = self.matcher.find_similar_workflows(user_prompt, top_k=3, min_similarity=0.3)
        
        if not matches:
            print("\n❌ No matching workflows found!")
            print("\n💡 Tip: Record a workflow first:")
            print("   system.record_workflow('workflow name')")
            return False
        
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
                model="gemini-2.0-flash-exp",
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
        print("🔴 STARTING WORKFLOW RECORDING")
        print("=" * 70)
        
        workflow_id = self.recorder.start_recording(
            workflow_name=workflow_name,
            description=description,
            tags=tags
        )
        
        print(f"\n✅ Recording workflow: {workflow_name}")
        print(f"   ID: {workflow_id}")
        print()
        print("📝 Instructions:")
        print("   1. Perform your workflow naturally")
        print("   2. System will watch and learn your actions")
        print("   3. When done, call: system.stop_recording()")
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
                user_input = input("\n💬 Your request: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'list':
                    self.list_workflows()
                
                elif user_input.lower().startswith('record '):
                    workflow_name = user_input[7:].strip()
                    if workflow_name:
                        self.record_workflow(workflow_name)
                    else:
                        print("Usage: record <workflow name>")
                
                elif user_input.lower() == 'stop':
                    self.stop_recording()
                
                else:
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

