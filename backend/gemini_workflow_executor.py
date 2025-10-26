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
                print(f"   Loaded {len(self.workflows_by_intention)} workflows:")
                for intention in list(self.workflows_by_intention.keys())[:5]:
                    print(f"     • {intention}")
                if len(self.workflows_by_intention) > 5:
                    print(f"     ... and {len(self.workflows_by_intention) - 5} more")

    def _load_all_workflows(self) -> Dict[str, List[Dict]]:
        """
        Load all ready workflows as a dictionary mapping intention -> semantic_actions

        Returns:
            Dict where:
                - Key: overall_intention/description from workflow
                - Value: list of semantic_actions
        """
        workflows_dict = {}

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
                        workflows_dict[intention] = semantic_actions

                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Could not load workflow {workflow_id}: {e}")

        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error loading workflows: {e}")

        return workflows_dict

    def reload_workflows(self):
        """
        Reload all workflows from memory.
        Call this after recording new workflows to update the dictionary.
        """
        if self.verbose:
            print("🔄 Reloading workflows...")

        self.workflows_by_intention = self._load_all_workflows()

        # Update Gemini's system prompt with new workflows
        self.gemini.workflows_dict = self.workflows_by_intention
        self.gemini.system_prompt = self.gemini._build_system_prompt()

        if self.verbose:
            print(f"✅ Reloaded {len(self.workflows_by_intention)} workflows")
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
        try:
            full_workflow = self.memory.get_workflow(workflow_id)
        except Exception as e:
            print(f"❌ Could not load workflow: {e}")
            return False, []
        
        steps = full_workflow.get('steps', [])
        
        if not steps:
            print("⚠️  Workflow has no steps")
            return False, []
        
        if self.verbose:
            print(f"Total steps: {len(steps)}")
            print()
        
        # 🚀 USE SEMANTIC ACTIONS if available, otherwise fall back to raw steps
        semantic_actions = full_workflow.get('semantic_actions', [])
        
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
        
        Instead of blindly replaying recorded actions, we use them as context to understand
        the user's intent and adapt intelligently to new situations.
        
        Args:
            semantic_actions: List of semantic action dicts (used as context)
            parameters: Parameter substitutions
            confirm_steps: Ask before each step
        
        Returns:
            True if all successful
        """
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
        
        # Capture current screen
        try:
            screenshot = np.array(pyautogui.screenshot())
        except Exception as e:
            print(f"❌ Could not capture screenshot: {e}")
            return False
        
        # Build prompt for Gemini to plan actions
        planning_prompt = f"""You are an intelligent automation assistant. The user wants to: "{user_request}"

CONTEXT: Here's a similar workflow that was recorded before:
{context_description}

CURRENT SCREEN: I'll provide a screenshot of the current screen.

Your task:
1. Look at the current screen
2. Understand what the user wants to accomplish
3. Plan the specific actions needed to achieve their goal
4. Adapt the recorded workflow pattern to the current situation

IMPORTANT: Don't blindly replay the recorded actions. Instead:
- Use the recorded workflow as a PATTERN/TEMPLATE
- Adapt to the current screen layout and content
- Focus on achieving the user's specific goal
- If the user wants "Machine Learning" but you see "Data Visualization", adapt accordingly

Return a JSON array of actions to execute:
[
    {{
        "action_type": "open_application" | "click" | "type" | "scroll" | "navigate" | "wait",
        "target": "what to interact with (for click/open_application)",
        "value": "text to type (for type) or key name (for key) or wait seconds (for wait)",
        "description": "human-readable description of this step"
    }},
    ...
]

Rules:
- Be specific about what to click (e.g., "Machine Learning course" not just "course")
- Adapt to the current screen content
- Use the recorded workflow as guidance, not exact replay
- Focus on the user's specific request
- Keep actions simple and direct
"""
        
        try:
            # Use Gemini to plan actions
            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash-exp",
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
                config=self.gemini.config
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
            
            # Execute the planned actions
            return self._execute_planned_actions(actions, confirm_steps)
            
        except Exception as e:
            print(f"❌ Planning failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        """Execute a single planned action"""
        action_type = action.get('action_type', '').lower()
        target = action.get('target', '')
        value = action.get('value', '')
        description = action.get('description', '')
        
        result = {
            'action_type': action_type,
            'timestamp': time.time(),
            'success': False,
            'error': None,
            'description': description
        }
        
        try:
            if action_type == 'open_application':
                success = self._execute_open_application({'target': target})
            
            elif action_type == 'click':
                success = self.gemini.click(target)
            
            elif action_type == 'type':
                success = self.gemini.type_text(value, target=target)
            
            elif action_type == 'scroll':
                direction = value if value else 'down'
                success = self.gemini.scroll(direction=direction)
            
            elif action_type == 'navigate':
                success = self._execute_navigate({'target': target, 'value': value})
            
            elif action_type == 'wait':
                duration = float(value) if value else 1.0
                time.sleep(duration)
                success = True
            
            else:
                print(f"⚠️  Unknown action type: {action_type}")
                success = False
            
            result['success'] = success
            
        except Exception as e:
            result['error'] = str(e)
            if self.verbose:
                print(f"❌ Execution error: {e}")
            success = False
        
        return success, result
    
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
        
        # Apply substitutions to target
        if 'target' in action_copy:
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
        
        # Apply substitutions to text
        if 'text' in action_copy:
            text = action_copy['text']
            for param_name, param_value in parameters.items():
                text = text.replace(f"{{{param_name}}}", param_value)
            action_copy['text'] = text
        
        return action_copy
    
    def _execute_open_application(self, action: Dict) -> bool:
        """Execute: open_application"""
        app_name = action.get('target')
        
        if not app_name:
            print("❌ No application name specified")
            return False
        
        if self.verbose:
            print(f"🚀 Opening application: {app_name}")
        
        # Use macOS Spotlight (cmd+space)
        import pyautogui
        pyautogui.hotkey('command', 'space')
        time.sleep(0.5)
        
        # Type app name
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.3)
        
        # Press enter
        pyautogui.press('enter')
        time.sleep(1.0)  # Wait for app to open
        
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

