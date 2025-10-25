#!/usr/bin/env python3
"""
AgentFlow Enhanced - Learn by Observation
Conversational computer control with visual workflow learning
"""

import os
import sys
import json
import time
from pathlib import Path

from google import genai

from agent_interface import AgentInterface, AgentMemory
from visual_memory import VisualWorkflowMemory
from recorder import WorkflowRecorder
from visual_analyzer import VisualAnalyzer
from visual_executor import VisualExecutor


class EnhancedAgentInterface(AgentInterface):
    """
    Enhanced agent with learn-by-observation capabilities.
    
    New features:
    - Record mode: Watch user and learn workflows
    - Visual memory: Store workflows with screenshots
    - Smart matching: Match user intent to learned workflows
    - Visual execution: Use vision to locate UI elements
    """
    
    def __init__(self):
        super().__init__()
        
        # Enhanced components
        self.visual_memory = VisualWorkflowMemory()
        self.recorder = WorkflowRecorder(memory=self.visual_memory)
        self.visual_analyzer = VisualAnalyzer()
        self.visual_executor = VisualExecutor(analyzer=self.visual_analyzer)
        
        print("✅ Enhanced AgentFlow initialized")
        print("   - Visual memory enabled")
        print("   - Workflow recording enabled")
        print("   - Visual analysis enabled")
        print("   - Visual execution enabled")
    
    def record_workflow(self, workflow_name: str = None, description: str = ""):
        """
        Start recording mode to learn a new workflow.
        
        Usage:
            agent.record_workflow("Open Canvas Class")
            # Perform actions manually
            # When done, stop with agent.stop_recording()
        """
        if workflow_name is None:
            workflow_name = input("Workflow name: ").strip()
        
        if not description:
            description = input("Description (optional): ").strip()
        
        tags_input = input("Tags (comma-separated, optional): ").strip()
        tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
        
        print()
        workflow_id = self.recorder.start_recording(
            workflow_name=workflow_name,
            description=description,
            tags=tags
        )
        
        return workflow_id
    
    def stop_recording(self):
        """Stop recording and finalize the workflow."""
        workflow_id = self.recorder.stop_recording()
        
        if workflow_id:
            # Ask if user wants to test identifying parameters
            print("\n💡 Analyzing workflow for parameters...")
            self._analyze_workflow_parameters(workflow_id)
        
        return workflow_id
    
    def _analyze_workflow_parameters(self, workflow_id: str):
        """
        Use LLM to analyze workflow and identify parameters.
        """
        workflow = self.visual_memory.get_workflow(workflow_id)
        
        # Build description of workflow for LLM
        workflow_description = f"Workflow: {workflow['name']}\n\n"
        workflow_description += "Steps:\n"
        
        for step in workflow['steps']:
            action_type = step['action_type']
            action_data = step['action_data']
            visual_context = step.get('visual_context', {})
            
            if action_type == 'click':
                clicked_text = visual_context.get('clicked_text', 'unknown')
                workflow_description += f"{step['step_number']}. Click on '{clicked_text}'\n"
            elif action_type == 'scroll':
                direction = action_data.get('direction', 'unknown')
                workflow_description += f"{step['step_number']}. Scroll {direction}\n"
            elif action_type == 'key_press':
                key = action_data.get('key', 'unknown')
                workflow_description += f"{step['step_number']}. Press {key}\n"
        
        # Use LLM to identify parameters
        try:
            prompt = f"""
Analyze this recorded workflow and identify which values are likely parameters
(i.e., variables that could change between executions):

{workflow_description}

For example, if the workflow is "Open Canvas Class" and step 2 clicks on "Machine Learning",
then "Machine Learning" is likely a parameter (class name).

Respond in JSON format with a list of parameters:
[
  {{
    "name": "class_name",
    "type": "string",
    "example": "Machine Learning",
    "step": 2,
    "description": "Name of the class to open"
  }}
]

Only identify true parameters that would vary. Return empty list [] if none.
"""
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract JSON from response (it might have markdown formatting)
            if '```' in response_text:
                # Extract JSON from code block
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                if start >= 0 and end > start:
                    response_text = response_text[start:end]
            
            parameters = json.loads(response_text)
            
            if parameters:
                print("\n📊 Identified Parameters:")
                for param in parameters:
                    print(f"  - {param['name']}: {param.get('description', 'No description')}")
                    print(f"    Example: {param['example']}")
                
                # Save parameters to workflow
                self.visual_memory.finalize_workflow(workflow_id, parameters=parameters)
                print("\n✅ Parameters saved to workflow")
            else:
                print("\n✅ No parameters identified (workflow is fully specified)")
                self.visual_memory.finalize_workflow(workflow_id, parameters=[])
        
        except Exception as e:
            print(f"\n⚠️  Could not analyze parameters: {e}")
            print("Finalizing workflow without parameters...")
            self.visual_memory.finalize_workflow(workflow_id, parameters=[])
    
    def list_learned_workflows(self):
        """List all learned workflows."""
        workflows = self.visual_memory.list_workflows(status='ready')
        
        if not workflows:
            print("\n📚 No learned workflows yet.")
            print("   Use 'record' command to teach me a new workflow!")
            return
        
        print("\n📚 Learned Workflows:")
        print("=" * 70)
        
        for wf in workflows:
            print(f"\n  {wf['name']}")
            print(f"  └─ {wf.get('description', 'No description')}")
            print(f"     Steps: {wf['steps_count']} | Uses: {wf.get('use_count', 0)}")
            
            if wf.get('parameters'):
                print(f"     Parameters: {', '.join([p['name'] for p in wf['parameters']])}")
            
            if wf.get('tags'):
                print(f"     Tags: {', '.join(wf['tags'])}")
        
        print("=" * 70)
    
    def find_matching_workflow(self, user_request: str):
        """
        Find learned workflow that matches user's request.
        
        Returns:
            (workflow, confidence, extracted_params)
        """
        # Simple text-based matching for now
        # In production, would use semantic embeddings
        
        workflows = self.visual_memory.search_workflows(user_request)
        
        if not workflows:
            return None, 0.0, {}
        
        # Use LLM to determine best match and extract parameters
        best_workflow = workflows[0]
        
        try:
            # Load full workflow
            workflow = self.visual_memory.get_workflow(best_workflow['workflow_id'])
            
            # If workflow has parameters, extract them from user request
            if workflow.get('parameters'):
                params_desc = json.dumps(workflow['parameters'], indent=2)
                
                prompt = f"""
The user said: "{user_request}"

This matches the workflow: "{workflow['name']}"

The workflow has these parameters:
{params_desc}

Extract the parameter values from the user's request.
Respond in JSON format:
{{
  "parameter_name": "extracted_value"
}}

If a parameter can't be determined, use null.
"""
                
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                )
                
                response_text = response.text.strip()
                
                # Extract JSON
                if '```' in response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        response_text = response_text[start:end]
                
                extracted_params = json.loads(response_text)
                
                return workflow, 0.9, extracted_params
            
            return workflow, 0.9, {}
        
        except Exception as e:
            print(f"⚠️  Error matching workflow: {e}")
            return None, 0.0, {}
    
    def execute_learned_workflow(self, workflow: Dict, parameters: Dict = None):
        """
        Execute a learned workflow with given parameters.
        
        This is the "replay" function that uses visual guidance to execute
        recorded actions with new parameters.
        """
        print(f"\n🎬 Executing learned workflow: {workflow['name']}")
        print("=" * 70)
        
        if parameters:
            print("\nParameters:")
            for k, v in parameters.items():
                print(f"  {k} = {v}")
        
        # Countdown before starting
        print("\n⚠️  Starting execution in 3 seconds...")
        print("DON'T TOUCH YOUR MOUSE OR KEYBOARD!")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🤖 Executing workflow...\n")
        
        # Execute with visual executor
        success = self.visual_executor.execute_workflow(
            workflow=workflow,
            parameters=parameters,
            verbose=True
        )
        
        if success:
            # Update usage count
            self.visual_memory.increment_usage(workflow['workflow_id'])
            return True
        else:
            print("\n❌ Workflow execution failed")
            return False
    
    def chat_loop(self):
        """Enhanced interactive loop with recording mode."""
        print("\n" + "=" * 70)
        print("🤖 AgentFlow Enhanced - Learn by Observation")
        print("=" * 70)
        print()
        print("I can learn workflows by watching you!")
        print()
        print("Commands:")
        print("  - 'record' - Start recording a new workflow")
        print("  - 'stop' - Stop recording")
        print("  - 'list' - Show learned workflows")
        print("  - 'memory' - See what I remember")
        print("  - 'quit' or 'exit' - Quit")
        print()
        print("Or just tell me what to do:")
        print("  - 'Open my DataVis class on Canvas'")
        print("  - 'Check my Canvas classes'")
        print("=" * 70)
        
        while True:
            try:
                user_input = input("\n💬 ").strip()
                
                if not user_input:
                    continue
                
                # Commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'record':
                    self.record_workflow()
                    continue
                
                if user_input.lower() == 'stop':
                    self.stop_recording()
                    continue
                
                if user_input.lower() == 'list':
                    self.list_learned_workflows()
                    continue
                
                if user_input.lower() == 'memory':
                    print("\n" + self.memory.get_relevant_context())
                    continue
                
                # Try to match to learned workflow first
                workflow, confidence, params = self.find_matching_workflow(user_input)
                
                if workflow and confidence > 0.7:
                    print(f"\n✨ Found matching workflow: {workflow['name']}")
                    print(f"   Confidence: {confidence*100:.0f}%")
                    
                    # Confirm with user
                    confirm = input("\n   Execute this workflow? [Y/n]: ").strip().lower()
                    
                    if confirm != 'n':
                        self.execute_learned_workflow(workflow, params)
                        continue
                
                # Fall back to regular execution
                print("\n🤔 No matching workflow found. Executing with AI...")
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
    
    # Create enhanced interface
    agent = EnhancedAgentInterface()
    
    # Start chat loop
    agent.chat_loop()


if __name__ == "__main__":
    main()

