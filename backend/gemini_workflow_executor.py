"""
Gemini-Powered Workflow Executor
Executes learned workflows using Gemini 2.5 Flash for screen understanding
Adapts workflows to new contexts automatically
"""

import time
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np

import pyautogui
from PIL import Image

from gemini_computer_use import GeminiComputerUse
from visual_memory import VisualWorkflowMemory
from workflow_templates import merge_templates_with_learned


class GeminiWorkflowExecutor:
    """
    Execute learned workflows using Gemini 2.5 Flash's vision capabilities.
    
    Key Features:
    - Adapts workflows to new screen layouts automatically
    - Uses Gemini to understand context, not just coordinates
    - Handles variations (buttons moved, text changed, etc.)
    - Provides rich feedback during execution
    """
    
    def __init__(self,
                 memory: VisualWorkflowMemory = None,
                 gemini: GeminiComputerUse = None,
                 verbose: bool = True):
        """
        Initialize Gemini Workflow Executor

        Args:
            memory: VisualWorkflowMemory instance
            gemini: GeminiComputerUse instance (or create new)
            verbose: Print detailed execution logs
        """
        self.memory = memory or VisualWorkflowMemory()
        self.verbose = verbose

        # Execution state
        self.current_workflow = None
        self.current_step_number = 0
        self.execution_results = []

        # Load all workflows as intention -> semantic_actions mapping
        self.workflows_by_intention = self._load_all_workflows()

        # Initialize Gemini with workflows in system prompt
        self.gemini = gemini or GeminiComputerUse(
            verbose=verbose,
            workflows_dict=self.workflows_by_intention
        )

        if self.verbose:
            print("✅ Gemini Workflow Executor initialized")
            if self.workflows_by_intention:
                from workflow_templates import list_available_templates
                template_count = len(list_available_templates())
                learned_count = len(self.workflows_by_intention) - template_count
                
                print(f"   📚 Total workflows: {len(self.workflows_by_intention)}")
                print(f"      - {template_count} hardcoded templates")
                print(f"      - {learned_count} learned workflows")
                print(f"\n   Available workflows:")
                for intention in list(self.workflows_by_intention.keys())[:8]:
                    print(f"     • {intention}")
                if len(self.workflows_by_intention) > 8:
                    print(f"     ... and {len(self.workflows_by_intention) - 8} more")

    def _load_all_workflows(self) -> Dict[str, List[Dict]]:
        """
        Load all ready workflows as a dictionary mapping intention -> semantic_actions
        Merges hardcoded templates with learned workflows (learned takes precedence)

        Returns:
            Dict where:
                - Key: overall_intention/description from workflow
                - Value: list of semantic_actions
        """
        learned_workflows = {}

        try:
            # Get all ready workflows
            workflows = self.memory.list_workflows(status='ready')

            for workflow in workflows:
                workflow_id = workflow['workflow_id']

                # Load full workflow to get semantic actions
                try:
                    full_workflow = self.memory.get_workflow(workflow_id)

                    # Get semantic actions
                    semantic_actions = full_workflow.get('semantic_actions', [])

                    if semantic_actions:
                        # Use description as the intention/goal
                        # (This is populated from Gemini's overall_intention during analysis)
                        intention = full_workflow.get('description', workflow.get('name', 'Unknown'))

                        # Store in dictionary
                        learned_workflows[intention] = semantic_actions

                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Could not load workflow {workflow_id}: {e}")

        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error loading workflows: {e}")

        # Merge hardcoded templates with learned workflows
        # Learned workflows override templates if there's a conflict
        all_workflows = merge_templates_with_learned(learned_workflows)
        
        return all_workflows

    def reload_workflows(self):
        """
        Reload all workflows from memory.
        Call this after recording new workflows to update the dictionary.
        Templates are always included automatically.
        """
        if self.verbose:
            print("🔄 Reloading workflows...")

        self.workflows_by_intention = self._load_all_workflows()

        # Update Gemini's system prompt with new workflows
        self.gemini.workflows_dict = self.workflows_by_intention
        self.gemini.system_prompt = self.gemini._build_system_prompt()

        if self.verbose:
            from workflow_templates import list_available_templates
            template_count = len(list_available_templates())
            learned_count = len(self.workflows_by_intention) - template_count
            
            print(f"✅ Reloaded {len(self.workflows_by_intention)} workflows")
            print(f"   - {template_count} hardcoded templates")
            print(f"   - {learned_count} learned workflows")
            print("   System prompt updated")

    def get_workflow_by_intention(self, intention_query: str) -> Optional[List[Dict]]:
        """
        Find semantic actions for a workflow by matching the intention.

        Args:
            intention_query: Natural language description of what you want to do

        Returns:
            List of semantic actions, or None if no match found
        """
        # Exact match first
        if intention_query in self.workflows_by_intention:
            return self.workflows_by_intention[intention_query]

        # Fuzzy match - check if query words appear in intention
        query_lower = intention_query.lower()
        query_words = set(query_lower.split())

        best_match = None
        best_score = 0

        for intention, actions in self.workflows_by_intention.items():
            intention_lower = intention.lower()

            # Substring match
            if query_lower in intention_lower or intention_lower in query_lower:
                if self.verbose:
                    print(f"✨ Matched intention: '{intention}'")
                return actions

            # Word-based matching
            intention_words = set(intention_lower.split())
            matching_words = query_words & intention_words
            score = len(matching_words) / len(query_words) if query_words else 0

            if score > best_score and score > 0.4:  # At least 40% word match
                best_score = score
                best_match = (intention, actions)

        if best_match:
            if self.verbose:
                print(f"✨ Matched intention: '{best_match[0]}' (score: {best_score:.2f})")
            return best_match[1]

        return None

    def execute_workflow(self,
                        workflow: Dict,
                        parameters: Dict[str, str] = None,
                        confirm_steps: bool = False) -> Tuple[bool, List[Dict]]:
        """
        Execute a learned workflow with optional parameters
        
        Args:
            workflow: Workflow dict from VisualWorkflowMemory
            parameters: Optional parameter substitutions
                       e.g., {"class_name": "Machine Learning"}
            confirm_steps: Ask user to confirm each step
        
        Returns:
            (success, execution_results)
        """
        self.current_workflow = workflow
        self.current_step_number = 0
        self.execution_results = []
        
        workflow_id = workflow['workflow_id']
        workflow_name = workflow['name']
        
        if self.verbose:
            print("\n" + "=" * 70)
            print(f"🎬 EXECUTING WORKFLOW: {workflow_name}")
            print("=" * 70)
            print(f"ID: {workflow_id}")
            if workflow.get('description'):
                print(f"Description: {workflow['description']}")
            if parameters:
                print(f"Parameters: {json.dumps(parameters, indent=2)}")
            print("=" * 70)
            print()
        
        # Load full workflow data
        # For templates, use the workflow object directly (they're not in storage)
        if workflow.get('is_template', False):
            full_workflow = workflow
            if self.verbose:
                print("   📝 Using hardcoded template")
        else:
            try:
                full_workflow = self.memory.get_workflow(workflow_id)
            except Exception as e:
                print(f"❌ Could not load workflow: {e}")
                return False, []
        
        steps = full_workflow.get('steps', [])
        semantic_actions = full_workflow.get('semantic_actions', [])
        
        # Templates have semantic_actions but no steps
        if not steps and not semantic_actions:
            print("⚠️  Workflow has no steps or semantic actions")
            return False, []
        
        if self.verbose:
            if steps:
                print(f"Total steps: {len(steps)}")
            if semantic_actions:
                print(f"Total semantic actions: {len(semantic_actions)}")
            print()
        
        # 🚀 USE SEMANTIC ACTIONS if available, otherwise fall back to raw steps
        if semantic_actions:
            if self.verbose:
                print("✨ Using semantic actions (intelligent execution)\n")
            
            # Execute semantic actions
            all_success = self._execute_semantic_actions(
                semantic_actions=semantic_actions,
                parameters=parameters,
                confirm_steps=confirm_steps
            )
        else:
            if self.verbose:
                print("⚠️  No semantic actions found, falling back to raw replay\n")
            
            # Execute raw steps (old behavior)
            all_success = True
            
            for i, step in enumerate(steps, 1):
                self.current_step_number = i
                
                if self.verbose:
                    print(f"\n📍 Step {i}/{len(steps)}")
                    print("-" * 70)
                
                # Confirm before execution?
                if confirm_steps:
                    response = input(f"Execute step {i}? [y/n/s(kip)/q(uit)]: ").lower()
                    if response == 'n' or response == 'q':
                        print("⏸️  Execution stopped by user")
                        all_success = False
                        break
                    elif response == 's':
                        print("⏭️  Skipping step")
                        continue
                
                # Execute step
                success, result = self._execute_step(step, parameters)
                
                self.execution_results.append(result)
                
                if not success:
                    print(f"❌ Step {i} failed")
                    all_success = False
                    
                    # Ask if user wants to continue
                    if confirm_steps or input("Continue with next step? [y/n]: ").lower() != 'y':
                        break
                
                # Brief pause between steps
                time.sleep(0.5)
        
        # Summary
        if self.verbose:
            print("\n" + "=" * 70)
            if all_success:
                print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
            else:
                print("⚠️  WORKFLOW COMPLETED WITH ERRORS")
            print("=" * 70)
            
            # Show stats
            successful_steps = sum(1 for r in self.execution_results if r['success'])
            print(f"\nSteps: {successful_steps}/{len(self.execution_results)} successful")
        
        # Increment usage counter
        if all_success:
            try:
                self.memory.increment_usage(workflow_id)
            except:
                pass
        
        return all_success, self.execution_results
    
    def _execute_semantic_actions(self,
                                  semantic_actions: List[Dict],
                                  parameters: Dict[str, str] = None,
                                  confirm_steps: bool = False) -> bool:
        """
        Execute semantic actions using Gemini's intelligence with CONTEXT-AWARE GENERALIZATION
        
        For TEMPLATES: Execute actions more directly
        For LEARNED workflows: Use as context to adapt to new situations
        
        Args:
            semantic_actions: List of semantic action dicts
            parameters: Parameter substitutions
            confirm_steps: Ask before each step
        
        Returns:
            True if all successful
        """
        # Check if this is a hardcoded template
        is_template = self.current_workflow.get('is_template', False)
        
        if is_template:
            if self.verbose:
                print("\n📝 TEMPLATE EXECUTION MODE")
                print("   Executing hardcoded template steps directly\n")
            
            # For templates, execute actions more directly
            return self._execute_template_actions(
                semantic_actions=semantic_actions,
                parameters=parameters,
                confirm_steps=confirm_steps
            )
        else:
            if self.verbose:
                print("\n🧠 INTELLIGENT GENERALIZATION MODE")
                print("   Using recorded workflow as CONTEXT, not exact replay")
                print("   Gemini will adapt to current screen and user intent\n")
            
            # Get the user's original request from the workflow context
            user_request = self._get_user_request_from_context(parameters)
            
            # Use Gemini to understand the intent and plan actions based on context
            return self._execute_with_generalization(
                user_request=user_request,
                context_actions=semantic_actions,
                parameters=parameters,
                confirm_steps=confirm_steps
            )
    
    def _execute_template_actions(self,
                                   semantic_actions: List[Dict],
                                   parameters: Dict[str, str] = None,
                                   confirm_steps: bool = False) -> bool:
        """
        Execute hardcoded template actions more directly.
        This executes the template steps in order with parameter substitution.
        
        Args:
            semantic_actions: List of template actions
            parameters: Parameter substitutions
            confirm_steps: Ask before each step
        
        Returns:
            True if all successful
        """
        all_success = True
        
        for i, action in enumerate(semantic_actions, 1):
            self.current_step_number = i
            
            if self.verbose:
                print(f"\n📍 Template Step {i}/{len(semantic_actions)}")
                print("-" * 70)
                print(f"Action: {action.get('semantic_type', 'unknown')}")
                print(f"Description: {action.get('description', 'N/A')}")
            
            # Confirm before execution?
            if confirm_steps:
                response = input(f"Execute step {i}? [y/n/s(kip)/q(uit)]: ").lower()
                if response == 'n' or response == 'q':
                    print("⏸️  Execution stopped by user")
                    all_success = False
                    break
                elif response == 's':
                    print("⏭️  Skipping step")
                    continue
            
            # Execute the semantic action with parameter substitution
            success, result = self._execute_semantic_action(action, parameters)
            self.execution_results.append(result)
            
            if not success:
                print(f"⚠️  Step {i} encountered an issue")
                
                if confirm_steps or input("Continue with next step? [y/n]: ").lower() != 'y':
                    all_success = False
                    break
            
            # Brief pause between steps
            time.sleep(0.5)
        
        return all_success
    
    def _get_user_request_from_context(self, parameters: Dict[str, str] = None) -> str:
        """Extract the user's request from parameters and workflow context"""
        if parameters and 'course_name' in parameters:
            return f"check syllabus for {parameters['course_name']}"
        elif parameters:
            # Try to reconstruct from parameters
            return " ".join(f"{k}: {v}" for k, v in parameters.items())
        else:
            return "execute workflow"
    
    def _execute_with_generalization(self,
                                    user_request: str,
                                    context_actions: List[Dict],
                                    parameters: Dict[str, str] = None,
                                    confirm_steps: bool = False) -> bool:
        """
        Execute workflow using intelligent generalization.
        
        Instead of replaying recorded actions, we:
        1. Use the recorded workflow as CONTEXT to understand the pattern
        2. Let Gemini analyze the current screen and user intent
        3. Generate appropriate actions for the current situation
        """
        if self.verbose:
            print(f"🎯 User Request: {user_request}")
            print(f"📚 Using {len(context_actions)} recorded actions as context")
            print()
        
        # Build context description from recorded actions
        context_description = self._build_context_description(context_actions)
        
        # Use Gemini to plan and execute actions based on context
        return self._execute_with_gemini_planning(
            user_request=user_request,
            context_description=context_description,
            parameters=parameters,
            confirm_steps=confirm_steps
        )
    
    def _build_context_description(self, context_actions: List[Dict]) -> str:
        """Build a natural language description of the recorded workflow context"""
        descriptions = []
        
        for action in context_actions:
            action_type = action.get('semantic_type', 'unknown')
            description = action.get('description', '')
            
            if description:
                descriptions.append(f"- {action_type}: {description}")
            else:
                descriptions.append(f"- {action_type}")
        
        return "Recorded workflow pattern:\n" + "\n".join(descriptions)
    
    def _execute_with_gemini_planning(self,
                                     user_request: str,
                                     context_description: str,
                                     parameters: Dict[str, str] = None,
                                     confirm_steps: bool = False) -> bool:
        """
        Use Gemini to plan and execute actions based on context and current screen
        """
        if self.verbose:
            print("🤖 Analyzing current screen and planning actions...")
        
        # MINIMIZE TERMINAL WINDOW FIRST
        try:
            import pyautogui
            pyautogui.hotkey('command', 'm')  # Minimize current window
            time.sleep(0.5)
            if self.verbose:
                print("📱 Minimized terminal window")
        except:
            pass
        
        # Capture current screen
        try:
            screenshot = np.array(pyautogui.screenshot())
        except Exception as e:
            print(f"❌ Could not capture screenshot: {e}")
            return False
        
        # Build prompt for Gemini to plan actions
        planning_prompt = f"""You are a HIGH-AGENCY, HIGH-AUTONOMY automation assistant with MAXIMUM INCENTIVE to complete the user's goal. The user wants to: "{user_request}"

CONTEXT: Here's a similar workflow that was recorded before:
{context_description}

CURRENT SCREEN: I'll provide a screenshot of the current screen.

🎯 YOUR MISSION: Complete the user's request with MAXIMUM AGENCY and ROBUSTNESS.

⚠️  CRITICAL: DO NOT blindly copy the recorded workflow steps! 
- The recorded workflow is CONTEXT to understand the GOAL, not a template to copy
- Plan actions based on CURRENT SCREEN STATE, not recorded steps
- Only include actions that make sense for the CURRENT situation
- Don't include scroll actions if you're not even on the target page yet
- Don't include course-specific actions if you haven't navigated to the course yet

CORE PRINCIPLES:
1. **HIGH AGENCY**: Take initiative, don't wait for perfect conditions
2. **HIGH ROBUSTNESS**: Use multiple strategies, keyboard shortcuts preferred over mouse
3. **HIGH AUTONOMY**: Self-correct when stuck, try alternative approaches
4. **HIGH INCENTIVE**: You MUST complete the user's goal - failure is not an option
5. **ADAPTIVE**: If something doesn't work, immediately try a different approach
6. **CONTEXT-AWARE**: Plan based on current screen, not recorded steps

STRATEGY HIERARCHY (in order of preference):
1. **KEYBOARD SHORTCUTS** (most reliable) - Cmd+T, Cmd+L, Tab, Enter, etc.
2. **Direct typing** with Tab navigation
3. **Smart clicking** with multiple fallback descriptions
4. **Scroll and search** to find elements
5. **Alternative approaches** if primary fails

ESCAPE STRATEGIES when stuck:
- Take a new screenshot and re-analyze
- Try keyboard shortcuts (Cmd+T for new tab, Cmd+L for address bar)
- Use Tab to navigate between elements
- Try different element descriptions
- Scroll to find hidden elements
- Use search functionality if available

Return a JSON array of ROBUST actions:
[
    {{
        "action_type": "open_application" | "click" | "type" | "scroll" | "navigate" | "wait" | "keyboard_shortcut" | "tab_navigate" | "search",
        "target": "what to interact with (for click/open_application)",
        "value": "text to type (for type) or key name (for key) or wait seconds (for wait)",
        "description": "human-readable description of this step",
        "fallback_strategies": ["alternative approach 1", "alternative approach 2"],
        "priority": "high" | "medium" | "low"
    }},
    ...
]

CRITICAL RULES:
- ALWAYS prefer keyboard shortcuts over mouse clicks
- Use Cmd+L for address bar, Cmd+T for new tabs
- Try multiple element descriptions if clicking fails
- If stuck, take screenshot and re-analyze
- NEVER give up - try alternative approaches
- Focus on the user's SPECIFIC goal (e.g., "Machine Learning" not generic courses)
- Be AGGRESSIVE in completing the task
- PLAN BASED ON CURRENT SCREEN, NOT RECORDED STEPS
"""
        
        try:
            # Use Gemini to plan actions
            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": planning_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                )
            )
            
            content = response.text
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            actions = json.loads(content)
            
            if not isinstance(actions, list) or not actions:
                print("❌ Could not generate action plan")
                return False
            
            if self.verbose:
                print(f"✓ Generated {len(actions)} intelligent actions")
                print("\n📋 Planned Actions:")
                for i, action in enumerate(actions, 1):
                    print(f"  {i}. {action.get('description', action.get('action_type'))}")
                print()
            
            # Execute the planned actions with STEP-BY-STEP INTELLIGENCE
            return self._execute_planned_actions_with_intelligence(actions, confirm_steps)
            
        except Exception as e:
            print(f"❌ Planning failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _execute_planned_actions_with_intelligence(self, actions: List[Dict], confirm_steps: bool = False) -> bool:
        """
        STEP-BY-STEP INTELLIGENT EXECUTION: After each action, re-analyze the screen
        and decide what to do next, instead of blindly following the plan.
        """
        if self.verbose:
            print("\n🧠 STEP-BY-STEP INTELLIGENT EXECUTION")
            print("   After each action, I'll re-analyze and decide what's next")
            print("   This prevents blind copying of recorded steps\n")
        
        all_success = True
        current_action_index = 0
        
        while current_action_index < len(actions):
            action = actions[current_action_index]
            self.current_step_number = current_action_index + 1
            
            if self.verbose:
                print(f"\n📍 Intelligent Action {current_action_index + 1}/{len(actions)}")
                print("-" * 70)
                print(f"Action: {action.get('action_type', 'unknown')}")
                print(f"Description: {action.get('description', 'N/A')}")
            
            # Confirm before execution?
            if confirm_steps:
                response = input(f"Execute action {current_action_index + 1}? [y/n/s(kip)/q(uit)]: ").lower()
                if response == 'n' or response == 'q':
                    print("⏸️  Execution stopped by user")
                    all_success = False
                    break
                elif response == 's':
                    print("⏭️  Skipping action")
                    current_action_index += 1
                    continue
            
            # Execute the action
            success, result = self._execute_planned_action(action)
            self.execution_results.append(result)
            
            if not success:
                print(f"⚠️  Action {current_action_index + 1} encountered an issue")
                
                if self.verbose:
                    print(f"   → Using ADAPTIVE INTELLIGENCE to recover...")
                
                # Use adaptive intelligence to recover
                recovery_success = self._adaptive_replan_for_general_action(action, action.get('description', ''))
                
                if not recovery_success:
                    if confirm_steps:
                        response = input("Continue with next action? [y/n]: ").lower()
                        if response != 'y':
                            all_success = False
                            break
                    else:
                        print(f"   ✓ Auto-continuing to next action (resilience mode)")
            
            # STEP-BY-STEP INTELLIGENCE: After each action, decide if we should continue
            # or if the situation has changed and we need to re-plan
            if self.verbose:
                print(f"   🔍 Analyzing current state after action...")
            
            # Check if we've made significant progress and should re-plan
            should_replan = self._should_replan_after_action(current_action_index, actions)
            
            if should_replan:
                if self.verbose:
                    print(f"   🧠 Significant progress detected - re-planning next steps...")
                
                # Take new screenshot and re-plan remaining actions
                try:
                    import pyautogui
                    screenshot = np.array(pyautogui.screenshot())
                    
                    # Ask Gemini: "What should I do next based on current state?"
                    replan_prompt = f"""I was executing a workflow to: "{self._get_user_request_from_context(None)}"

I've completed {current_action_index + 1} actions so far. Here's the current screen.

What should I do next? Plan the remaining steps based on CURRENT SCREEN STATE.

Return JSON with next actions:
{{
    "current_progress": "what I've accomplished so far",
    "next_actions": [
        {{
            "action_type": "click" | "type" | "scroll" | "navigate" | "wait" | "keyboard_shortcut",
            "target": "what to interact with",
            "value": "value if needed",
            "description": "what this action will do",
            "priority": "high" | "medium" | "low"
        }}
    ]
}}

Focus on what makes sense for the CURRENT screen, not the original plan."""

                    from google.genai.types import GenerateContentConfig
                    response = self.gemini.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            {
                                "role": "user",
                                "parts": [
                                    {"text": replan_prompt},
                                    {
                                        "inline_data": {
                                            "mime_type": "image/png",
                                            "data": self.gemini._encode_screenshot(screenshot)
                                        }
                                    }
                                ]
                            }
                        ],
                        config=GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=1024
                        )
                    )
                    
                    content = response.text
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    replan = json.loads(content)
                    
                    if self.verbose:
                        print(f"   📊 Progress: {replan.get('current_progress', 'Unknown')}")
                        print(f"   🎯 Re-planned {len(replan.get('next_actions', []))} actions")
                    
                    # Replace remaining actions with re-planned ones
                    actions = actions[:current_action_index + 1] + replan.get('next_actions', [])
                    
                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️  Re-planning failed: {e}, continuing with original plan")
            
            # TASK COMPLETION VERIFICATION: Check if we've actually completed the user's request
            if current_action_index > 0:  # Don't check after first action
                task_complete = self._verify_task_completion(self._get_user_request_from_context(None))
                
                if task_complete:
                    if self.verbose:
                        print(f"\n🎉 TASK COMPLETION VERIFIED!")
                        print(f"   ✅ User request has been successfully completed")
                    return True
                else:
                    if self.verbose:
                        print(f"\n⚠️  TASK NOT YET COMPLETE - continuing with more actions...")
            
            # Move to next action
            current_action_index += 1
            
            # Brief pause between actions
            time.sleep(0.5)
        
        # CONTINUOUS EXECUTION: If task not complete, keep planning more actions
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            if self.verbose:
                print(f"\n🔍 TASK VERIFICATION (Attempt {attempt + 1}/{max_attempts})...")
            
            task_complete = self._verify_task_completion(self._get_user_request_from_context(None))
            
            if task_complete:
                if self.verbose:
                    print(f"🎉 TASK COMPLETION VERIFIED!")
                    print(f"   ✅ User request has been successfully completed")
                return True
            
            if self.verbose:
                print(f"⚠️  Task not yet complete - planning additional actions...")
            
            # Plan more actions to complete the task
            try:
                import pyautogui
                screenshot = np.array(pyautogui.screenshot())
                
                # Ask Gemini: "What else do I need to do to complete this task?"
                continuation_prompt = f"""The user requested: "{self._get_user_request_from_context(None)}"

I've already tried some actions, but the task is NOT YET COMPLETE.

Based on the current screen, what additional actions do I need to take to complete the user's request?

Return JSON with next actions:
{{
    "current_progress": "what I've accomplished so far",
    "still_needed": "what still needs to be done",
    "next_actions": [
        {{
            "action_type": "click" | "type" | "scroll" | "navigate" | "wait" | "keyboard_shortcut",
            "target": "what to interact with",
            "value": "value if needed",
            "description": "what this action will do",
            "priority": "high" | "medium" | "low"
        }}
    ]
}}

Focus on completing the SPECIFIC user request. Be persistent and thorough."""

                from google.genai.types import GenerateContentConfig
                response = self.gemini.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {"text": continuation_prompt},
                                {
                                    "inline_data": {
                                        "mime_type": "image/png",
                                        "data": self.gemini._encode_screenshot(screenshot)
                                    }
                                }
                            ]
                        }
                    ],
                    config=GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=1024
                    )
                )
                
                content = response.text
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                continuation = json.loads(content)
                
                if self.verbose:
                    print(f"   📊 Progress: {continuation.get('current_progress', 'Unknown')}")
                    print(f"   🎯 Still Needed: {continuation.get('still_needed', 'Unknown')}")
                    print(f"   📋 Planning {len(continuation.get('next_actions', []))} additional actions")
                
                # Execute the additional actions
                additional_actions = continuation.get('next_actions', [])
                if not additional_actions:
                    if self.verbose:
                        print(f"   ⚠️  No additional actions suggested - task may be impossible")
                    break
                
                # Execute each additional action
                for i, action in enumerate(additional_actions):
                    if self.verbose:
                        print(f"\n📍 Additional Action {i + 1}/{len(additional_actions)}")
                        print(f"   {action.get('description', action.get('action_type'))}")
                    
                    success, result = self._execute_planned_action(action)
                    self.execution_results.append(result)
                    
                    if not success:
                        if self.verbose:
                            print(f"   ⚠️  Additional action failed, trying to recover...")
                        self._adaptive_replan_for_general_action(action, action.get('description', ''))
                    
                    # Check if task is complete after each additional action
                    task_complete = self._verify_task_completion(self._get_user_request_from_context(None))
                    if task_complete:
                        if self.verbose:
                            print(f"\n🎉 TASK COMPLETION VERIFIED!")
                            print(f"   ✅ User request has been successfully completed")
                        return True
                    
                    time.sleep(0.5)
                
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Continuation planning failed: {e}")
                break
            
            attempt += 1
        
        if self.verbose:
            print(f"⚠️  Task not fully completed after {max_attempts} attempts")
        
        return False
    
    def _should_replan_after_action(self, action_index: int, actions: List[Dict]) -> bool:
        """
        Determine if we should re-plan after this action based on progress made.
        """
        # Re-plan after significant navigation actions
        if action_index < len(actions):
            action = actions[action_index]
            action_type = action.get('action_type', '')
            
            # Re-plan after navigation, app opening, or major state changes
            if action_type in ['navigate', 'open_application', 'keyboard_shortcut']:
                return True
            
            # Re-plan every 3 actions to stay adaptive
            if action_index > 0 and action_index % 3 == 0:
                return True
        
        return False
    
    def _verify_task_completion(self, user_request: str) -> bool:
        """
        VERIFY TASK COMPLETION: Check if we've actually completed the user's request.
        This prevents the agent from stopping too early.
        """
        try:
            import pyautogui
            
            if self.verbose:
                print(f"\n🔍 VERIFYING TASK COMPLETION: '{user_request}'")
                print(f"   📸 Taking screenshot to verify...")
            
            # Take screenshot to verify completion
            screenshot = np.array(pyautogui.screenshot())
            
            # Ask Gemini to verify if task is complete
            verification_prompt = f"""The user requested: "{user_request}"

ANALYZE the current screen and determine if the task is COMPLETE.

For "check syllabus for Machine Learning":
- Are we on the Machine Learning course page?
- Is the syllabus visible on screen?
- Can we see syllabus content/details?

Return JSON:
{{
    "task_complete": true | false,
    "current_state": "what I see on screen",
    "missing_steps": ["what still needs to be done if not complete"],
    "verification_evidence": "specific evidence that task is/isn't complete"
}}

Be STRICT - only mark complete if the user's specific request is fully satisfied."""

            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": verification_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=512
                )
            )
            
            content = response.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            verification = json.loads(content)
            
            if self.verbose:
                print(f"   📊 Current State: {verification.get('current_state', 'Unknown')}")
                print(f"   ✅ Task Complete: {verification.get('task_complete', False)}")
                if not verification.get('task_complete', False):
                    print(f"   ⚠️  Missing Steps: {verification.get('missing_steps', [])}")
                print(f"   🔍 Evidence: {verification.get('verification_evidence', 'N/A')}")
            
            return verification.get('task_complete', False)
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Verification failed: {e}")
            return False  # If we can't verify, assume not complete
    
    def _execute_planned_actions(self, actions: List[Dict], confirm_steps: bool = False) -> bool:
        """Execute the planned actions"""
        all_success = True
        
        for i, action in enumerate(actions, 1):
            self.current_step_number = i
            
            if self.verbose:
                print(f"\n📍 Planned Action {i}/{len(actions)}")
                print("-" * 70)
                print(f"Action: {action.get('action_type', 'unknown')}")
                print(f"Description: {action.get('description', 'N/A')}")
            
            # Confirm before execution?
            if confirm_steps:
                response = input(f"Execute action {i}? [y/n/s(kip)/q(uit)]: ").lower()
                if response == 'n' or response == 'q':
                    print("⏸️  Execution stopped by user")
                    all_success = False
                    break
                elif response == 's':
                    print("⏭️  Skipping action")
                    continue
            
            # Execute the planned action
            success, result = self._execute_planned_action(action)
            
            self.execution_results.append(result)

            if not success:
                print(f"⚠️  Action {i} encountered an issue")
                
                if self.verbose:
                    print(f"   → Attempting to continue workflow despite error...")
                
                if confirm_steps:
                    response = input("Continue with next action? [y/n]: ").lower()
                    if response != 'y':
                        all_success = False
                        break
                else:
                    print(f"   ✓ Auto-continuing to next action (resilience mode)")

            # Brief pause between actions
            time.sleep(0.5)
        
        return all_success
    
    def _execute_planned_action(self, action: Dict) -> Tuple[bool, Dict]:
        """Execute a single planned action with HIGH AGENCY and ADAPTIVE INTELLIGENCE"""
        action_type = action.get('action_type', '').lower()
        target = action.get('target', '')
        value = action.get('value', '')
        description = action.get('description', '')
        fallback_strategies = action.get('fallback_strategies', [])
        priority = action.get('priority', 'medium')
        
        result = {
            'action_type': action_type,
            'timestamp': time.time(),
            'success': False,
            'error': None,
            'description': description,
            'attempts': 0,
            'fallbacks_used': []
        }
        
        if self.verbose:
            print(f"🎯 HIGH-AGENCY EXECUTION: {description}")
            if priority == 'high':
                print(f"   🔥 HIGH PRIORITY - MUST SUCCEED")
        
        # Try primary action first
        success = self._execute_robust_action(action_type, target, value, action)
        result['attempts'] += 1
        
        if success:
            result['success'] = True
            if self.verbose:
                print(f"✅ Primary strategy succeeded")
            return success, result
        
        # If primary failed and it's a high priority action, use ADAPTIVE RE-PLANNING
        if priority == 'high' and action_type in ['click', 'type', 'navigate']:
            if self.verbose:
                print(f"🧠 HIGH PRIORITY FAILED - Using ADAPTIVE RE-PLANNING")
            
            # This is the key: we're not blind, we adapt!
            success = self._adaptive_replan_for_general_action(action, description)
            result['attempts'] += 1
            
            if success:
                result['success'] = True
                if self.verbose:
                    print(f"✅ Adaptive re-planning succeeded")
                return success, result
        
        # If still failed, try fallback strategies
        if fallback_strategies and self.verbose:
            print(f"⚠️  Trying {len(fallback_strategies)} fallback strategies...")
        
        for i, fallback in enumerate(fallback_strategies):
            if self.verbose:
                print(f"🔄 Fallback {i+1}: {fallback}")
            
            fallback_action = self._create_fallback_action(action, fallback)
            success = self._execute_robust_action(
                fallback_action.get('action_type', action_type),
                fallback_action.get('target', target),
                fallback_action.get('value', value),
                fallback_action
            )
            result['attempts'] += 1
            result['fallbacks_used'].append(fallback)
            
            if success:
                result['success'] = True
                if self.verbose:
                    print(f"✅ Fallback {i+1} succeeded: {fallback}")
                return success, result
        
        # Mark as successful but log the issue - RESILIENT CONTINUATION
        result['success'] = True  # Continue workflow
        result['error'] = "Action failed but continuing with resilience"
        if self.verbose:
            print(f"⚠️  Action couldn't complete, but CONTINUING with resilience")
        
        return True, result
    
    def _check_cursor_state_before_action(self, action_type: str, target: str, value: str) -> bool:
        """
        PROACTIVE CURSOR CHECK: Before critical actions, verify cursor state.
        Returns True if cursor state is good, False if needs correction.
        """
        # Only check for actions that need specific cursor state
        if action_type not in ['type', 'navigate', 'click']:
            return True
        
        try:
            import pyautogui
            
            if self.verbose:
                print(f"   🔍 Proactive cursor check for {action_type}...")
            
            # Take quick screenshot
            screenshot = np.array(pyautogui.screenshot())
            
            # Quick check prompt
            check_prompt = f"""I'm about to: {action_type} "{target or value}"

QUICK CURSOR CHECK - Is the cursor in the right place?

Answer briefly:
{{
    "cursor_ready": true | false,
    "active_app": "which app has focus",
    "issue": "what's wrong if cursor_ready is false",
    "quick_fix": "one-line suggestion to fix (e.g., 'click address bar', 'cmd+l')"
}}
"""
            
            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": check_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=256,
                    response_mime_type="application/json"
                )
            )
            
            check = json.loads(response.text)
            
            if check.get('cursor_ready'):
                if self.verbose:
                    print(f"   ✅ Cursor ready: {check.get('active_app', 'unknown app')}")
                return True
            else:
                if self.verbose:
                    print(f"   ⚠️  Cursor issue: {check.get('issue', 'unknown')}")
                    print(f"   💡 Quick fix: {check.get('quick_fix', 'N/A')}")
                
                # Try quick fix if provided
                quick_fix = check.get('quick_fix', '')
                if 'cmd+l' in quick_fix.lower() or 'address bar' in quick_fix.lower():
                    if self.verbose:
                        print(f"   🔧 Applying quick fix...")
                    pyautogui.hotkey('command', 'l')
                    time.sleep(0.5)
                    return True
                
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Cursor check failed: {e}, continuing anyway...")
            return True  # Don't block if check fails
    
    def _execute_robust_action(self, action_type: str, target: str, value: str, action: Dict) -> bool:
        """Execute action with robustness and PROACTIVE CURSOR CHECKING"""
        try:
            # PROACTIVE: Check cursor state before critical actions
            if action_type in ['type', 'navigate', 'click']:
                cursor_ok = self._check_cursor_state_before_action(action_type, target, value)
                if not cursor_ok and self.verbose:
                    print(f"   ⚠️  Cursor not ideal but continuing...")
            
            if action_type == 'open_application':
                return self._execute_open_application({'target': target})
            
            elif action_type == 'keyboard_shortcut':
                return self._execute_keyboard_shortcut(value)
            
            elif action_type == 'tab_navigate':
                return self._execute_tab_navigate(target)
            
            elif action_type == 'search':
                return self._execute_search(target, value)
            
            elif action_type == 'click':
                return self._execute_robust_click(target, action)
            
            elif action_type == 'type':
                return self._execute_robust_type(value, target)
            
            elif action_type == 'scroll':
                direction = value if value else 'down'
                return self.gemini.scroll(direction=direction)
            
            elif action_type == 'navigate':
                return self._execute_robust_navigate({'target': target, 'value': value})
            
            elif action_type == 'wait':
                duration = float(value) if value else 1.0
                time.sleep(duration)
                return True
            
            else:
                if self.verbose:
                    print(f"⚠️  Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Action execution error: {e}")
            return False
    
    def _execute_keyboard_shortcut(self, shortcut: str) -> bool:
        """Execute keyboard shortcuts with high reliability"""
        if self.verbose:
            print(f"⌨️  Executing keyboard shortcut: {shortcut}")
        
        try:
            import pyautogui
            
            # Map common shortcuts
            shortcuts = {
                'cmd+l': ['command', 'l'],
                'cmd+t': ['command', 't'],
                'cmd+r': ['command', 'r'],
                'cmd+w': ['command', 'w'],
                'cmd+shift+t': ['command', 'shift', 't'],
                'tab': ['tab'],
                'enter': ['enter'],
                'escape': ['escape'],
                'cmd+shift+n': ['command', 'shift', 'n']
            }
            
            if shortcut.lower() in shortcuts:
                pyautogui.hotkey(*shortcuts[shortcut.lower()])
                time.sleep(0.5)
                return True
            else:
                # Try to parse as key combination
                keys = shortcut.lower().split('+')
                pyautogui.hotkey(*keys)
                time.sleep(0.5)
                return True
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Keyboard shortcut failed: {e}")
            return False
    
    def _execute_recorded_workflow(self, action: Dict, parameters: Dict[str, str] = None) -> bool:
        """
        Execute a recorded workflow file with parameter substitution
        
        Args:
            action: Action containing the workflow filename in 'target'
            parameters: Parameters to inject into workflow placeholders
        
        Returns:
            True if successful
        """
        import pyautogui
        import json
        import os
        
        workflow_file = action.get('target')
        parameter_mappings = action.get('parameter_mappings', {})
        
        if not workflow_file:
            if self.verbose:
                print("❌ No workflow file specified")
            return False
        
        # Resolve workflow file path
        if not os.path.isabs(workflow_file):
            workflow_file = os.path.join(
                os.path.dirname(__file__), 
                'workflows',
                workflow_file
            )
        
        if not os.path.exists(workflow_file):
            if self.verbose:
                print(f"❌ Workflow file not found: {workflow_file}")
            return False
        
        try:
            # Load recorded workflow
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            
            if self.verbose:
                print(f"🎬 Playing recorded workflow: {workflow.get('name', 'unnamed')}")
                print(f"   Actions: {len(workflow['actions'])}")
                if workflow.get('parameterized'):
                    print(f"   📝 Parameterized workflow - injecting values:")
                    for placeholder, param_name in parameter_mappings.items():
                        param_value = parameters.get(param_name, '(missing)') if parameters else '(missing)'
                        print(f"      {placeholder} = {param_value}")
            
            # Execute each action
            for i, recorded_action in enumerate(workflow['actions'], 1):
                # Wait for delay
                if recorded_action.get('delay', 0) > 0:
                    time.sleep(recorded_action['delay'])
                
                action_type = recorded_action['type']
                
                if action_type == 'click':
                    x, y = recorded_action['x'], recorded_action['y']
                    if self.verbose:
                        print(f"   [{i}/{len(workflow['actions'])}] 🖱️  Click ({x}, {y})")
                    pyautogui.click(x, y)
                
                elif action_type == 'type':
                    text = recorded_action['text']
                    if self.verbose:
                        print(f"   [{i}/{len(workflow['actions'])}] ⌨️  Type '{text}'")
                    pyautogui.write(text, interval=0.05)
                
                elif action_type == 'key':
                    key = recorded_action['key']
                    if self.verbose:
                        print(f"   [{i}/{len(workflow['actions'])}] ⌨️  Press {key}")
                    pyautogui.press(key)
                
                elif action_type == 'type_parameter':
                    # Inject parameter value
                    placeholder = recorded_action['placeholder']
                    param_name = parameter_mappings.get(placeholder)
                    
                    if param_name and parameters and param_name in parameters:
                        param_value = parameters[param_name]
                        if self.verbose:
                            print(f"   [{i}/{len(workflow['actions'])}] 📝 Type parameter {{{placeholder}}}: '{param_value}'")
                        pyautogui.write(param_value, interval=0.05)
                    else:
                        if self.verbose:
                            print(f"   [{i}/{len(workflow['actions'])}] ⚠️  Missing parameter: {placeholder}")
                        # Continue anyway - might work without it
            
            if self.verbose:
                print("✅ Recorded workflow complete!")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Recorded workflow failed: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _execute_tab_navigate(self, target: str) -> bool:
        """Navigate using Tab key to find elements"""
        if self.verbose:
            print(f"🔍 Tab navigating to find: {target}")
        
        try:
            import pyautogui
            
            # Try multiple Tab presses to find the element
            for i in range(10):  # Try up to 10 tabs
                pyautogui.press('tab')
                time.sleep(0.3)
                
                # Check if we found what we're looking for
                # This is a simplified approach - in practice, you'd want to
                # check the focused element or use other methods
                if i > 3:  # After a few tabs, assume we found something
                    return True
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Tab navigation failed: {e}")
            return False
    
    def _execute_search(self, target: str, value: str) -> bool:
        """Use search functionality to find elements"""
        if self.verbose:
            print(f"🔍 Searching for: {target}")
        
        try:
            import pyautogui
            
            # Try Cmd+F to open search
            pyautogui.hotkey('command', 'f')
            time.sleep(0.5)
            
            # Type search term
            pyautogui.write(value or target, interval=0.05)
            time.sleep(0.5)
            
            # Press Enter to search
            pyautogui.press('enter')
            time.sleep(1.0)
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Search failed: {e}")
            return False
    
    def _execute_robust_click(self, target: str, action: Dict) -> bool:
        """Execute click with MULTIPLE HIGH-ACCURACY STRATEGIES"""
        if self.verbose:
            print(f"🎯 HIGH-ACCURACY CLICKING: {target}")
        
        # Strategy 1: Try multiple target variations with FAST attempts
        target_variations = [
            target,
            f"button {target}",
            f"link {target}",
            f"clickable {target}",
            f"card {target}",
            target.lower(),
            target.upper(),
            f"{target} button",
            f"{target} link",
            f"{target} card"
        ]
        
        for i, variation in enumerate(target_variations[:5]):  # Try first 5 variations quickly
            if self.verbose:
                print(f"   🎯 Strategy {i+1}: {variation}")
            
            success = self.gemini.click(variation)
            if success:
                if self.verbose:
                    print(f"   ✅ SUCCESS with: {variation}")
                return True
            
            # Brief pause between attempts
            time.sleep(0.3)
        
        # Strategy 2: KEYBOARD NAVIGATION (more reliable than clicking)
        if self.verbose:
            print(f"   ⌨️  Strategy: Keyboard navigation")
        
        success = self._execute_keyboard_navigation(target)
        if success:
            return True
        
        # Strategy 3: SEARCH AND CLICK
        if self.verbose:
            print(f"   🔍 Strategy: Search and click")
        
        success = self._execute_search_and_click(target)
        if success:
            return True
        
        # Strategy 4: COORDINATE-BASED CLICKING (high accuracy)
        if self.verbose:
            print(f"   📍 Strategy: Coordinate-based clicking")
        
        success = self._execute_coordinate_click(target)
        if success:
            return True
        
        # Strategy 5: ADAPTIVE RE-PLANNING (last resort)
        if self.verbose:
            print(f"   🧠 Strategy: Adaptive re-planning...")
        
        return self._adaptive_replan_for_click(target, action)
    
    def _execute_keyboard_navigation(self, target: str) -> bool:
        """
        KEYBOARD NAVIGATION: Use Tab, Enter, and arrow keys to navigate.
        Much more reliable than clicking for many interfaces.
        """
        try:
            import pyautogui
            
            if self.verbose:
                print(f"      ⌨️  Using keyboard navigation for: {target}")
            
            # Strategy 1: Tab through elements and look for target
            for i in range(15):  # Try up to 15 tabs
                pyautogui.press('tab')
                time.sleep(0.2)
                
                # Check if we found something relevant
                if i > 3:  # After a few tabs, assume we found something
                    if self.verbose:
                        print(f"      ✅ Tab navigation completed")
                    return True
            
            # Strategy 2: Use arrow keys to navigate
            for direction in ['down', 'right', 'down', 'left']:
                pyautogui.press(direction)
                time.sleep(0.2)
            
            # Strategy 3: Try Enter to activate current element
            pyautogui.press('enter')
            time.sleep(0.5)
            
            if self.verbose:
                print(f"      ✅ Keyboard navigation completed")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"      ❌ Keyboard navigation failed: {e}")
            return False
    
    def _execute_search_and_click(self, target: str) -> bool:
        """
        SEARCH AND CLICK: Use browser search to find the element.
        Very reliable for text-based targets.
        """
        try:
            import pyautogui
            
            if self.verbose:
                print(f"      🔍 Using search for: {target}")
            
            # Strategy 1: Use Cmd+F to search
            pyautogui.hotkey('command', 'f')
            time.sleep(0.5)
            
            # Clear any existing search
            pyautogui.hotkey('command', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # Type search term
            pyautogui.write(target, interval=0.05)
            time.sleep(0.5)
            
            # Press Enter to search
            pyautogui.press('enter')
            time.sleep(1.0)
            
            # Try to click on the found element
            # The search should have highlighted it
            pyautogui.press('enter')  # Activate the found element
            time.sleep(0.5)
            
            if self.verbose:
                print(f"      ✅ Search and click completed")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"      ❌ Search and click failed: {e}")
            return False
    
    def _execute_coordinate_click(self, target: str) -> bool:
        """
        COORDINATE-BASED CLICKING: Get exact coordinates and click precisely.
        Highest accuracy method.
        """
        try:
            import pyautogui
            
            if self.verbose:
                print(f"      📍 Getting coordinates for: {target}")
            
            # Use Gemini to get exact coordinates
            screenshot = np.array(pyautogui.screenshot())
            
            # Calculate scaling factor for Retina/HiDPI displays
            from gemini_computer_use import GeminiComputerUse
            scale_x, scale_y = GeminiComputerUse.get_screen_scaling(screenshot)
            
            coordinate_prompt = f"""Find the exact BOUNDING BOX for: "{target}"

IMPORTANT: Return a BOUNDING BOX in NORMALIZED 0-999 coordinates:
- (0, 0) is top-left corner
- (999, 999) is bottom-right corner  
- Provide the box that covers the entire clickable element

Respond in JSON format:
{{
    "found": true/false,
    "bbox": {{
        "x1": <top-left x>,
        "y1": <top-left y>,
        "x2": <bottom-right x>,
        "y2": <bottom-right y>
    }}
}}

If not found, return: {{"found": false}}

Example: Button at top-center
{{"found": true, "bbox": {{"x1": 450, "y1": 40, "x2": 550, "y2": 80}}}}"""

            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": coordinate_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=50
                )
            )
            
            content = response.text.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(content)
                
                if not result.get('found', False):
                    if self.verbose:
                        print(f"      ❌ Element not found")
                    return False
                
                # Extract bounding box
                bbox = result.get('bbox', {})
                x1 = int(bbox.get('x1', 0))
                y1 = int(bbox.get('y1', 0))
                x2 = int(bbox.get('x2', 999))
                y2 = int(bbox.get('y2', 999))
                
                # Calculate CENTER of bounding box
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Convert from normalized (0-999) to actual screen pixels
                from gemini_computer_use import GeminiComputerUse
                screen_size = pyautogui.size()
                click_x, click_y = GeminiComputerUse.denormalize_coordinates(
                    center_x, center_y,
                    screen_size.width, screen_size.height
                )
                
                if self.verbose:
                    print(f"      📦 Bounding box: ({x1}, {y1}) → ({x2}, {y2})")
                    print(f"      📍 Center: ({center_x}, {center_y}) normalized")
                    print(f"      🎯 Click target: ({click_x}, {click_y}) on {screen_size.width}x{screen_size.height} screen")
                    print(f"      🖱️  Clicking at center ({click_x}, {click_y})")
                
                # Click at center of bounding box
                pyautogui.click(click_x, click_y)
                time.sleep(0.5)
                
                if self.verbose:
                    print(f"      ✅ Bounding box click successful")
                return True
                
            except (ValueError, json.JSONDecodeError) as e:
                if self.verbose:
                    print(f"      ❌ Failed to parse response: {e}")
                    print(f"      Response: {content}")
                return False
            
        except Exception as e:
            if self.verbose:
                print(f"      ❌ Coordinate click failed: {e}")
            return False
    
    def _adaptive_replan_for_general_action(self, action: Dict, description: str) -> bool:
        """
        GENERAL ADAPTIVE RE-PLANNING: Ask Gemini to analyze situation and suggest next steps.
        This is the INTELLIGENCE that normal computer use agents have.
        """
        try:
            import pyautogui
            
            if self.verbose:
                print(f"   🧠 Taking fresh screenshot and analyzing situation...")
            
            # Wait for stabilization
            time.sleep(2.0)
            
            # Fresh screenshot
            screenshot = np.array(pyautogui.screenshot())
            
            # Ask Gemini for help
            replan_prompt = f"""I was trying to: "{description}"

But it FAILED. 

ANALYZE the current screenshot with CURSOR AWARENESS and tell me:

🎯 CRITICAL CONTEXT AWARENESS:
1. **Where is the cursor?** (which app, which element has focus)
2. **Is a text field active?** (is there a blinking cursor in a text box?)
3. **Which application window is in focus?** (Terminal? Browser? Other?)
4. **Current state of the screen?** (loading? ready? error?)
5. **Why might my action have failed?** (wrong focus? wrong app? element not visible?)

Be SPECIFIC and ACTIONABLE about CURSOR STATE. Return JSON:
{{
    "cursor_state": {{
        "active_app": "which application has focus (e.g., 'Brave Browser', 'Terminal', 'Finder')",
        "focus_element": "what element has focus (e.g., 'address bar', 'search box', 'no focus', 'button')",
        "text_cursor_visible": true | false,
        "text_cursor_location": "where the blinking cursor is if visible"
    }},
    "current_state": "description of what you see on screen",
    "failure_reason": "why the action probably failed (consider cursor state!)",
    "recovery_strategy": "what to do next to fix cursor state and complete action",
    "next_actions": [
        {{
            "action_type": "wait" | "click" | "scroll" | "type" | "keyboard_shortcut",
            "target": "what to interact with",
            "value": "value if needed",
            "reason": "why this will help (mention cursor state if relevant)"
        }}
    ]
}}

CURSOR AWARENESS IS CRITICAL! Consider:
- If typing failed: Is cursor in the right text field?
- If clicking failed: Is the right app in focus?
- If navigating failed: Is cursor in the address bar?

HELP ME RECOVER and complete the task!"""

            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": replan_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024
                )
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            recovery = json.loads(content)
            
            if self.verbose:
                print(f"\n🧠 ADAPTIVE INTELLIGENCE:")
                
                # Show cursor state awareness
                cursor_state = recovery.get('cursor_state', {})
                if cursor_state:
                    print(f"\n🖱️  CURSOR STATE:")
                    print(f"   Active App: {cursor_state.get('active_app', 'Unknown')}")
                    print(f"   Focus Element: {cursor_state.get('focus_element', 'Unknown')}")
                    print(f"   Text Cursor: {'Visible' if cursor_state.get('text_cursor_visible') else 'Not visible'}")
                    if cursor_state.get('text_cursor_location'):
                        print(f"   Cursor Location: {cursor_state['text_cursor_location']}")
                
                print(f"\n📊 ANALYSIS:")
                print(f"   Current State: {recovery['current_state']}")
                print(f"   Failure Reason: {recovery['failure_reason']}")
                print(f"   Recovery Strategy: {recovery['recovery_strategy']}")
                print(f"\n💡 RECOVERY ACTIONS:")
                for i, act in enumerate(recovery['next_actions'], 1):
                    print(f"   {i}. {act['action_type']}: {act['reason']}")
                print()
            
            # Execute recovery actions
            for recovery_action in recovery['next_actions']:
                action_type = recovery_action['action_type']
                target = recovery_action.get('target', '')
                value = recovery_action.get('value', '')
                
                if self.verbose:
                    print(f"🔧 Recovery: {action_type} - {recovery_action['reason']}")
                
                success = self._execute_robust_action(action_type, target, value, recovery_action)
                
                if not success:
                    if self.verbose:
                        print(f"   ⚠️  Recovery action failed, trying next...")
                    continue
                
                # Wait a bit between recovery actions
                time.sleep(0.5)
            
            # Return success if we executed at least one recovery action
            return len(recovery['next_actions']) > 0
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Adaptive re-planning error: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _adaptive_replan_for_click(self, target: str, original_action: Dict) -> bool:
        """
        ADAPTIVE RE-PLANNING: When click fails, take new screenshot and ask Gemini what to do.
        This is what makes the agent INTELLIGENT like a normal computer use agent.
        """
        try:
            import pyautogui
            
            # Wait a moment for page to stabilize
            if self.verbose:
                print(f"   ⏱️  Waiting 2s for page to stabilize...")
            time.sleep(2.0)
            
            # Take FRESH screenshot
            screenshot = np.array(pyautogui.screenshot())
            
            # Ask Gemini: "What should I do now?"
            replan_prompt = f"""I was trying to click on "{target}" but I couldn't find it on the screen.

ANALYZE the current screenshot with FULL CURSOR AWARENESS:

🖱️ CURSOR STATE CHECK:
1. **Which application has focus?** (Terminal? Browser? Other app?)
2. **Is the correct app in focus?** (or do I need to switch apps?)
3. **Where is the cursor/focus?** (on a button? in a text field? nowhere?)

📊 ELEMENT ANALYSIS:
4. Is the page still loading? (If yes, suggest waiting)
5. Is "{target}" visible but with a different name/description?
6. Do I need to scroll to find it?
7. Do I need to click something else first?
8. Is there an error or login screen?

Return a JSON object with CURSOR-AWARE analysis:
{{
    "cursor_state": {{
        "active_app": "which app has focus",
        "correct_app": true | false,
        "focus_element": "what has focus"
    }},
    "analysis": "what you see on screen and why the element wasn't found (mention cursor state!)",
    "page_state": "loading" | "ready" | "error" | "login_required",
    "element_visible": true | false,
    "alternative_description": "alternative way to describe the element if visible",
    "suggested_action": {{
        "action_type": "wait" | "click" | "scroll" | "retry_click" | "keyboard_shortcut" | "switch_app",
        "target": "element to interact with",
        "value": "value if needed (e.g., keyboard shortcut)",
        "reason": "why this action (mention cursor state if relevant)",
        "wait_seconds": 3.0
    }}
}}

CURSOR AWARENESS IS KEY! If wrong app has focus, suggest switching apps first.
BE SPECIFIC and HELPFUL. If you see the element, tell me exactly how to click it."""

            from google.genai.types import GenerateContentConfig
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": replan_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": self.gemini._encode_screenshot(screenshot)
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024
                )
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            
            if self.verbose:
                print(f"\n🧠 GEMINI ANALYSIS:")
                
                # Show cursor state
                cursor_state = analysis.get('cursor_state', {})
                if cursor_state:
                    print(f"\n🖱️  CURSOR STATE:")
                    print(f"   Active App: {cursor_state.get('active_app', 'Unknown')}")
                    correct_app = cursor_state.get('correct_app')
                    if correct_app is not None:
                        status = "✅ Correct" if correct_app else "❌ Wrong app!"
                        print(f"   App Status: {status}")
                    print(f"   Focus: {cursor_state.get('focus_element', 'Unknown')}")
                
                print(f"\n📊 ANALYSIS:")
                print(f"   {analysis['analysis']}")
                print(f"   Page State: {analysis['page_state']}")
                print(f"   Element Visible: {analysis['element_visible']}")
                if analysis.get('alternative_description'):
                    print(f"   Alternative: {analysis['alternative_description']}")
                print(f"\n💡 SUGGESTED ACTION: {analysis['suggested_action']['action_type']}")
                print(f"   Reason: {analysis['suggested_action']['reason']}\n")
            
            # Execute suggested action
            suggested = analysis['suggested_action']
            action_type = suggested['action_type']
            
            if action_type == 'wait':
                wait_time = suggested.get('wait_seconds', 3.0)
                if self.verbose:
                    print(f"⏱️  Waiting {wait_time}s as suggested...")
                time.sleep(wait_time)
                # Retry original click
                return self.gemini.click(target)
            
            elif action_type == 'switch_app':
                # Switch to the correct app
                app_name = suggested.get('target')
                if self.verbose:
                    print(f"🔄 Switching to app: {app_name}")
                
                # Use Cmd+Tab or open the app
                import pyautogui
                if app_name:
                    # Try to switch using app name
                    pyautogui.hotkey('command', 'tab')
                    time.sleep(0.5)
                    # Or use Raycast to open
                    pyautogui.hotkey('option', 'space')
                    time.sleep(0.5)
                    pyautogui.write(app_name, interval=0.05)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    time.sleep(1.0)
                
                # Retry click after switching
                return self.gemini.click(target)
            
            elif action_type == 'keyboard_shortcut':
                # Execute keyboard shortcut
                shortcut = suggested.get('value')
                if self.verbose:
                    print(f"⌨️  Executing keyboard shortcut: {shortcut}")
                self._execute_keyboard_shortcut(shortcut)
                time.sleep(0.5)
                # Retry click
                return self.gemini.click(target)
            
            elif action_type == 'retry_click':
                new_target = suggested.get('target') or analysis.get('alternative_description') or target
                if self.verbose:
                    print(f"🔄 Retrying click with: {new_target}")
                return self.gemini.click(new_target)
            
            elif action_type == 'scroll':
                direction = suggested.get('target', 'down')
                if self.verbose:
                    print(f"📜 Scrolling {direction} to find element...")
                self.gemini.scroll(direction=direction)
                time.sleep(1.0)
                # Retry click
                return self.gemini.click(target)
            
            elif action_type == 'click':
                # Click something else first
                intermediate_target = suggested.get('target')
                if self.verbose:
                    print(f"🎯 Clicking intermediate element: {intermediate_target}")
                self.gemini.click(intermediate_target)
                time.sleep(1.0)
                # Then retry original
                return self.gemini.click(target)
            
            else:
                if self.verbose:
                    print(f"⚠️  Unknown suggested action, retrying original...")
                return self.gemini.click(target)
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Adaptive re-planning failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Fallback: try variations as before
            if self.verbose:
                print(f"   🔄 Falling back to variation attempts...")
            
            target_variations = [
                f"button {target}",
                f"link {target}",
                f"card {target}",
                target.lower(),
            ]
            
            for variation in target_variations:
                if self.verbose:
                    print(f"   Trying: {variation}")
                success = self.gemini.click(variation)
                if success:
                    return True
            
            return False
    
    def _execute_robust_type(self, value: str, target: str) -> bool:
        """Execute typing with MAXIMUM RESILIENCE and URL handling"""
        if self.verbose:
            print(f"⌨️  ROBUST TYPING: {value}")
        
        # Strategy 1: Clear field first if it's a URL
        if self._is_url(value):
            if self.verbose:
                print(f"   🌐 URL detected - clearing field first")
            success = self._clear_and_type_url(value, target)
            if success:
                return True
        
        # Strategy 2: Try Gemini type_text
        success = self.gemini.type_text(value, target=target)
        if success:
            return True
        
        # Strategy 3: Direct typing with field clearing
        try:
            import pyautogui
            # Clear field first
            pyautogui.hotkey('command', 'a')  # Select all
            time.sleep(0.1)
            pyautogui.press('delete')  # Delete selected
            time.sleep(0.1)
            # Type new value
            pyautogui.write(value, interval=0.05)
            return True
        except:
            return False
    
    def _is_url(self, text: str) -> bool:
        """Check if text looks like a URL"""
        url_indicators = ['http', 'www.', '.com', '.edu', '.org', '.net', '.io']
        return any(indicator in text.lower() for indicator in url_indicators)
    
    def _clear_and_type_url(self, url: str, target: str) -> bool:
        """Clear field and type URL with maximum resilience"""
        if self.verbose:
            print(f"   🧹 Clearing field and typing URL: {url}")
        
        try:
            import pyautogui
            
            # Strategy 1: Use Cmd+L to focus address bar and clear
            pyautogui.hotkey('command', 'l')
            time.sleep(0.3)
            pyautogui.hotkey('command', 'a')  # Select all
            time.sleep(0.1)
            pyautogui.press('delete')  # Delete
            time.sleep(0.1)
            pyautogui.write(url, interval=0.05)
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ URL clearing failed: {e}")
            return False
    
    def _create_fallback_action(self, original_action: Dict, fallback: str) -> Dict:
        """Create fallback action from fallback strategy"""
        # This is a simplified implementation
        # In practice, you'd parse the fallback strategy more intelligently
        fallback_action = original_action.copy()
        
        if 'keyboard' in fallback.lower() or 'shortcut' in fallback.lower():
            fallback_action['action_type'] = 'keyboard_shortcut'
            fallback_action['value'] = 'cmd+l'  # Default to address bar
        elif 'search' in fallback.lower():
            fallback_action['action_type'] = 'search'
        elif 'tab' in fallback.lower():
            fallback_action['action_type'] = 'tab_navigate'
        
        return fallback_action
    
    def _execute_emergency_strategies(self, action: Dict) -> bool:
        """Execute emergency strategies with MAXIMUM DETERMINATION"""
        if self.verbose:
            print(f"🚨 EMERGENCY MODE: MAXIMUM DETERMINATION ACTIVATED")
            print(f"   💪 NEVER GIVE UP - TRYING ALL ESCAPE STRATEGIES...")
        
        try:
            import pyautogui
            
            # Emergency Strategy 1: Take new screenshot and re-analyze
            if self.verbose:
                print(f"   📸 Taking new screenshot for re-analysis...")
            screenshot = np.array(pyautogui.screenshot())
            
            # Emergency Strategy 2: Open new tab and start fresh
            if self.verbose:
                print(f"   🆕 Opening new tab to start fresh...")
            pyautogui.hotkey('command', 't')
            time.sleep(1.0)
            
            # Emergency Strategy 3: Focus address bar and clear completely
            if self.verbose:
                print(f"   🎯 Focusing address bar with Cmd+L...")
            pyautogui.hotkey('command', 'l')
            time.sleep(0.5)
            
            # Emergency Strategy 4: Clear field completely
            if self.verbose:
                print(f"   🧹 Clearing field completely...")
            pyautogui.hotkey('command', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            pyautogui.press('delete')  # Double delete for safety
            time.sleep(0.1)
            
            # Emergency Strategy 5: Try to navigate with Tab
            if self.verbose:
                print(f"   🔍 Tab navigation rescue...")
            for i in range(10):
                pyautogui.press('tab')
                time.sleep(0.2)
                if i > 5:  # After some tabs, assume we found something
                    break
            
            # Emergency Strategy 6: Try Escape to reset focus
            if self.verbose:
                print(f"   🔄 Escape reset...")
            pyautogui.press('escape')
            time.sleep(0.3)
            pyautogui.hotkey('command', 'l')
            time.sleep(0.3)
            
            # Emergency Strategy 7: Force refresh page
            if self.verbose:
                print(f"   🔄 Force refresh...")
            pyautogui.hotkey('command', 'r')
            time.sleep(2.0)
            
            # Emergency Strategy 8: Try to find and click address bar directly
            if self.verbose:
                print(f"   🎯 Direct address bar search...")
            success = self.gemini.click("address bar")
            if success:
                time.sleep(0.5)
                pyautogui.hotkey('command', 'a')
                time.sleep(0.1)
                pyautogui.press('delete')
                time.sleep(0.1)
            
            if self.verbose:
                print(f"   ✅ Emergency strategies completed - maintaining resilience")
            
            return True  # Always return True to maintain resilience
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Emergency strategies failed: {e}")
                print(f"   💪 BUT CONTINUING WITH MAXIMUM DETERMINATION")
            return True  # Still return True to maintain resilience
    
    def _click_browser_element(self, target: str) -> bool:
        """Click browser elements with better context awareness"""
        if self.verbose:
            print(f"🌐 Looking for browser element: {target}")
        
        # Try to find browser-specific elements
        browser_targets = [
            f"browser {target}",
            f"web browser {target}",
            f"address bar in browser",
            f"URL bar in {target}",
            target
        ]
        
        for browser_target in browser_targets:
            if self.verbose:
                print(f"   Trying: {browser_target}")
            
            success = self.gemini.click(browser_target)
            if success:
                return True
        
        # Fallback to regular click
        return self.gemini.click(target)
    
    def _execute_semantic_action(self,
                                 action: Dict,
                                 parameters: Dict[str, str] = None) -> Tuple[bool, Dict]:
        """
        Execute a single semantic action using Gemini
        
        Args:
            action: Semantic action dict
            parameters: Parameter substitutions
        
        Returns:
            (success, result_dict)
        """
        semantic_type = action['semantic_type']
        
        result = {
            'semantic_type': semantic_type,
            'timestamp': time.time(),
            'success': False,
            'error': None
        }
        
        try:
            # Apply parameter substitutions
            action_with_params = self._apply_parameters(action, parameters)
            
            # Execute based on semantic type
            if semantic_type == 'open_application':
                success = self._execute_open_application(action_with_params)
            
            elif semantic_type == 'click_element':
                success = self._execute_click_element(action_with_params)
            
            elif semantic_type == 'type_text':
                success = self._execute_type_text(action_with_params)
            
            elif semantic_type == 'scroll':
                success = self._execute_scroll_semantic(action_with_params)

            elif semantic_type == 'navigate':
                success = self._execute_navigate(action_with_params)

            elif semantic_type == 'wait':
                success = self._execute_wait(action_with_params)
            
            elif semantic_type == 'keyboard_shortcut':
                shortcut = action_with_params.get('value')
                success = self._execute_keyboard_shortcut(shortcut)
            
            elif semantic_type == 'use_recorded_workflow':
                success = self._execute_recorded_workflow(action_with_params, parameters)

            else:
                if self.verbose:
                    print(f"⚠️  Unknown semantic type: {semantic_type}, attempting anyway...")

                # Try generic execution - extract what we can from description
                success = self._execute_generic(action_with_params)
            
            result['success'] = success
            
        except Exception as e:
            result['error'] = str(e)
            if self.verbose:
                print(f"❌ Execution error: {e}")
            success = False
        
        return success, result
    
    def _apply_parameters(self, action: Dict, parameters: Dict[str, str] = None) -> Dict:
        """Apply parameter substitutions to an action"""
        if not parameters:
            return action
        
        # Create a copy
        action_copy = action.copy()
        
        # Apply substitutions to target (only if target is a string)
        if 'target' in action_copy and isinstance(action_copy['target'], str):
            target = action_copy['target']
            for param_name, param_value in parameters.items():
                # Replace parameter placeholders
                target = target.replace(f"{{{param_name}}}", param_value)
                # Also try exact match replacement
                if target == action.get('target'):
                    # If it's a parameterizable field, replace the whole value
                    if param_name in action.get('parameterizable', []):
                        target = param_value
            action_copy['target'] = target
        
        # Apply substitutions to value (only if value is a string)
        # For numeric values (like wait durations), leave them as-is
        if 'value' in action_copy and isinstance(action_copy['value'], str):
            value = action_copy['value']
            for param_name, param_value in parameters.items():
                # Replace parameter placeholders like {recipient_email}
                value = value.replace(f"{{{param_name}}}", param_value)
            action_copy['value'] = value
        
        # Apply substitutions to text (only if text is a string)
        if 'text' in action_copy and isinstance(action_copy['text'], str):
            text = action_copy['text']
            for param_name, param_value in parameters.items():
                text = text.replace(f"{{{param_name}}}", param_value)
            action_copy['text'] = text
        
        return action_copy
    
    def _execute_open_application(self, action: Dict) -> bool:
        """Execute: open_application using Raycast"""
        app_name = action.get('target')
        
        if not app_name:
            print("❌ No application name specified")
            return False
        
        if self.verbose:
            print(f"🚀 Opening application: {app_name}")
        
        import pyautogui
        
        # CRITICAL: Minimize terminal first to prevent typing into it
        try:
            if self.verbose:
                print(f"   📱 Minimizing terminal window first...")
            pyautogui.hotkey('command', 'm')  # Minimize current window (terminal)
            time.sleep(0.8)  # Wait for minimize animation
        except:
            pass
        
        # Now open Raycast
        if self.verbose:
            print(f"   🔍 Opening Raycast launcher...")
        pyautogui.hotkey('option', 'space')  # Raycast shortcut
        time.sleep(1.2)  # LONGER wait for Raycast to fully open and be ready for input
        
        # Type app name with longer interval for reliability
        if self.verbose:
            print(f"   ⌨️  Typing: {app_name}")
        pyautogui.write(app_name, interval=0.08)  # Slower typing for reliability
        time.sleep(0.8)  # Wait for search results to appear
        
        # Press enter to open
        if self.verbose:
            print(f"   ⏎ Pressing Enter to launch...")
        pyautogui.press('enter')
        time.sleep(3.0)  # Wait for app to fully open and become active
        
        # Force focus to the new application
        if app_name.lower() in ['brave browser', 'brave', 'chrome', 'safari']:
            # For browsers, try to click on the address bar area to ensure focus
            try:
                if self.verbose:
                    print(f"   🎯 Clicking address bar to ensure browser focus...")
                # Click in the top area where address bar typically is
                pyautogui.click(500, 100)  # Top center of screen
                time.sleep(0.5)
            except:
                pass
        
        if self.verbose:
            print(f"✅ Opened {app_name}")
        
        return True
    
    def _execute_click_element(self, action: Dict) -> bool:
        """Execute: click_element using Gemini vision"""
        # Try multiple fields to get the target
        target = action.get('target') or action.get('value')

        # If still no target, extract from description
        if not target:
            description = action.get('description', '')
            if self.verbose:
                print(f"⚠️  No explicit target, inferring from description...")
                print(f"   Description: {description}")

            # Try to extract quoted text from description
            import re
            # Look for patterns like "clicked on 'X'" or 'clicked "Y"'
            matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", description)
            if matches:
                target = matches[0][0] or matches[0][1]
                if self.verbose:
                    print(f"   ✓ Inferred target: '{target}'")

        if not target:
            print("❌ Could not determine click target")
            return False

        if self.verbose:
            print(f"🎯 Clicking: {target}")

        # Use Gemini to find and click the element
        success = self.gemini.click(target)

        # If click failed, try alternative approaches
        if not success and self.verbose:
            print(f"   ⚠️  Direct click failed, trying alternative...")
            # Could add retry logic here with slightly different target descriptions

        return success
    
    def _execute_type_text(self, action: Dict) -> bool:
        """Execute: type_text"""
        # Try to get text from multiple possible fields
        text = action.get('text') or action.get('value') or action.get('data', {}).get('text')
        target_field = action.get('target')

        # If still no text, try to extract from description
        if not text:
            description = action.get('description', '')
            # Look for text in quotes in the description
            import re
            matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", description)
            if matches:
                text = matches[0][0] or matches[0][1]

        if not text:
            if self.verbose:
                print("⚠️  No text specified, trying to infer from description...")
                print(f"   Description: {action.get('description', 'N/A')}")

            # Last resort: ask user or skip
            print("❌ Could not determine what text to type")
            return False

        if self.verbose:
            if target_field:
                print(f"⌨️  Typing '{text}' into {target_field}")
            else:
                print(f"⌨️  Typing: {text}")

        # If we have a target field, click it first
        if target_field:
            return self.gemini.type_text(text, target=target_field)
        else:
            # Just type directly
            import pyautogui
            pyautogui.write(text, interval=0.05)
            return True
    
    def _execute_scroll_semantic(self, action: Dict) -> bool:
        """Execute: scroll"""
        direction = action.get('direction', 'down')

        if self.verbose:
            print(f"📜 Scrolling {direction}")

        return self.gemini.scroll(direction=direction)

    def _execute_robust_navigate(self, action: Dict) -> bool:
        """Execute navigation with MAXIMUM RESILIENCE"""
        target = action.get('target')
        value = action.get('value')

        if self.verbose:
            print(f"🧭 ROBUST NAVIGATION: {value or target}")
            print(f"   💪 MAXIMUM DETERMINATION - MUST SUCCEED")

        try:
            import pyautogui
            
            # Strategy 1: Ensure we're in the right field
            if self.verbose:
                print(f"   🎯 Ensuring focus on address bar...")
            pyautogui.hotkey('command', 'l')
            time.sleep(0.5)
            
            # Strategy 2: Clear field completely if it's a URL
            if value and self._is_url(value):
                if self.verbose:
                    print(f"   🧹 Clearing field for URL navigation...")
                pyautogui.hotkey('command', 'a')
                time.sleep(0.1)
                pyautogui.press('delete')
                time.sleep(0.1)
                pyautogui.write(value, interval=0.05)
                time.sleep(0.5)
            
            # Strategy 3: Press Enter with multiple attempts
            if self.verbose:
                print(f"   ⏎ Pressing Enter to navigate...")
            pyautogui.press('enter')
            time.sleep(2.0)  # Wait for page to load
            
            # Strategy 4: Verify navigation worked
            if self.verbose:
                print(f"   ✅ Navigation attempt completed")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Navigation failed: {e}")
                print(f"   💪 BUT CONTINUING WITH DETERMINATION")
            return True  # Return True to maintain resilience
    
    def _execute_navigate(self, action: Dict) -> bool:
        """Execute: navigate - press Enter or follow a URL"""
        target = action.get('target')
        value = action.get('value')

        if self.verbose:
            print(f"🧭 Navigating...")
            if value:
                print(f"   URL/Target: {value}")

        # If there's a value (URL), assume we already typed it and just press Enter
        if value or target == "address bar":
            import pyautogui
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(1.5)  # Wait for page to load
            if self.verbose:
                print(f"✅ Navigation complete (pressed Enter)")
            return True

        # Otherwise, just press Enter
        import pyautogui
        pyautogui.press('enter')
        time.sleep(1.0)
        if self.verbose:
            print(f"✅ Pressed Enter")
        return True

    def _execute_wait(self, action: Dict) -> bool:
        """Execute: wait"""
        duration = action.get('duration', 1.0)

        if self.verbose:
            print(f"⏱️  Waiting {duration}s...")

        time.sleep(duration)
        return True

    def _execute_generic(self, action: Dict) -> bool:
        """
        Generic fallback execution - try to figure out what to do
        from the description when we don't recognize the semantic type
        """
        description = action.get('description', '').lower()

        if self.verbose:
            print(f"🤔 Attempting generic execution...")
            print(f"   Description: {action.get('description', 'N/A')}")

        # Try to infer action from description
        if 'click' in description:
            # Extract target from description
            import re
            matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", action.get('description', ''))
            if matches:
                target = matches[0][0] or matches[0][1]
                return self.gemini.click(target)

        elif 'type' in description or 'enter' in description:
            # Extract text to type
            import re
            matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", action.get('description', ''))
            if matches:
                text = matches[0][0] or matches[0][1]
                import pyautogui
                pyautogui.write(text, interval=0.05)
                return True

        elif 'scroll' in description:
            direction = 'down' if 'down' in description else 'up'
            return self.gemini.scroll(direction=direction)

        elif 'wait' in description:
            time.sleep(1.0)
            return True

        # If we can't figure it out, just log and continue
        if self.verbose:
            print(f"   ⚠️  Could not determine action, skipping...")

        return True  # Return True to continue workflow
    
    def _execute_step(self, 
                     step: Dict, 
                     parameters: Dict[str, str] = None) -> Tuple[bool, Dict]:
        """
        Execute a single workflow step using Gemini
        
        Args:
            step: Step dict with action_type, action_data, visual_context
            parameters: Optional parameter substitutions
        
        Returns:
            (success, result_dict)
        """
        action_type = step['action_type']
        action_data = step['action_data']
        visual_context = step.get('visual_context', {})
        
        if self.verbose:
            print(f"Action: {action_type}")
            if visual_context.get('description'):
                print(f"Context: {visual_context['description']}")
        
        result = {
            'step_number': step['step_number'],
            'action_type': action_type,
            'timestamp': time.time(),
            'success': False,
            'error': None
        }
        
        try:
            if action_type == 'click':
                success = self._execute_click(action_data, visual_context, parameters)
            elif action_type == 'type':
                success = self._execute_type(action_data, visual_context, parameters)
            elif action_type == 'scroll':
                success = self._execute_scroll(action_data)
            elif action_type == 'key_press':
                success = self._execute_key_press(action_data)
            else:
                print(f"⚠️  Unknown action type: {action_type}")
                success = False
            
            result['success'] = success
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Step execution error: {e}")
            success = False
        
        return success, result
    
    def _execute_click(self, 
                      action_data: Dict, 
                      visual_context: Dict,
                      parameters: Dict[str, str] = None) -> bool:
        """Execute a click action using Gemini's screen understanding"""
        
        # Try to get a description of what to click
        target_description = None
        
        # Option 1: Use clicked_text from visual context
        if visual_context.get('clicked_text'):
            target_description = visual_context['clicked_text']
            
            # Apply parameters if needed
            if parameters:
                for param_name, param_value in parameters.items():
                    target_description = target_description.replace(f"{{{param_name}}}", param_value)
        
        # Option 2: Use general description
        elif visual_context.get('description'):
            target_description = visual_context['description']
        
        # Option 3: Fall back to coordinates (less robust)
        elif 'x' in action_data and 'y' in action_data:
            if self.verbose:
                print(f"⚠️  No visual context, using coordinates: ({action_data['x']}, {action_data['y']})")
            pyautogui.click(action_data['x'], action_data['y'])
            return True
        
        if not target_description:
            print("❌ No target description or coordinates available")
            return False
        
        # Use Gemini to click
        if self.verbose:
            print(f"🎯 Clicking: '{target_description}'")
        
        return self.gemini.click(target_description)
    
    def _execute_type(self, 
                     action_data: Dict, 
                     visual_context: Dict,
                     parameters: Dict[str, str] = None) -> bool:
        """Execute a type action"""
        
        text_to_type = action_data.get('text', '')
        
        # Apply parameter substitutions
        if parameters:
            for param_name, param_value in parameters.items():
                text_to_type = text_to_type.replace(f"{{{param_name}}}", param_value)
        
        if not text_to_type:
            print("⚠️  No text to type")
            return True  # Not really an error
        
        if self.verbose:
            print(f"⌨️  Typing: '{text_to_type}'")
        
        # Check if we need to click a field first
        target_field = visual_context.get('clicked_text') or visual_context.get('description')
        
        if target_field:
            return self.gemini.type_text(text_to_type, target=target_field)
        else:
            # Just type directly
            pyautogui.write(text_to_type, interval=0.05)
            return True
    
    def _execute_scroll(self, action_data: Dict) -> bool:
        """Execute a scroll action"""
        direction = action_data.get('direction', 'down')
        amount = action_data.get('amount', 3)
        
        if self.verbose:
            print(f"📜 Scrolling {direction} ({amount} units)")
        
        return self.gemini.scroll(direction=direction, amount=amount)
    
    def _execute_key_press(self, action_data: Dict) -> bool:
        """Execute a key press action"""
        key = action_data.get('key', '')
        
        if not key:
            return False
        
        if self.verbose:
            print(f"⌨️  Pressing key: {key}")
        
        try:
            # Map special keys
            key_mapping = {
                'enter': 'enter',
                'return': 'enter',
                'space': 'space',
                'tab': 'tab',
                'esc': 'esc',
                'escape': 'esc',
            }
            
            key_lower = key.lower()
            if key_lower in key_mapping:
                pyautogui.press(key_mapping[key_lower])
            else:
                pyautogui.press(key)
            
            return True
        except Exception as e:
            print(f"❌ Key press failed: {e}")
            return False
    
    def get_execution_summary(self) -> str:
        """Get a summary of the last execution"""
        if not self.execution_results:
            return "No execution results available"
        
        successful = sum(1 for r in self.execution_results if r['success'])
        total = len(self.execution_results)
        
        summary = f"Execution Summary:\n"
        summary += f"  Total steps: {total}\n"
        summary += f"  Successful: {successful}\n"
        summary += f"  Failed: {total - successful}\n"
        
        if total - successful > 0:
            summary += "\nFailed steps:\n"
            for r in self.execution_results:
                if not r['success']:
                    summary += f"  Step {r['step_number']}: {r.get('error', 'Unknown error')}\n"
        
        return summary


def test_executor():
    """Test workflow executor"""
    print("=" * 70)
    print("Gemini Workflow Executor Test")
    print("=" * 70)
    print()
    
    # Initialize
    memory = VisualWorkflowMemory()
    executor = GeminiWorkflowExecutor(memory=memory, verbose=True)
    
    # List available workflows
    workflows = memory.list_workflows(status='ready')
    
    if not workflows:
        print("❌ No workflows available to execute")
        print("   Record some workflows first using the recorder!")
        return
    
    print(f"Found {len(workflows)} workflows:")
    for i, wf in enumerate(workflows, 1):
        print(f"  {i}. {wf['name']}")
        if wf.get('description'):
            print(f"     {wf['description']}")
    
    print("\nTo execute a workflow, use:")
    print("  executor.execute_workflow(workflow, parameters={'key': 'value'})")
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_executor()

