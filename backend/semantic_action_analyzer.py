"""
Semantic Action Analyzer
Transforms raw recorded actions into semantic, generalizable instructions

This is the "brain" that watches what you do and understands the INTENT,
not just the mechanical actions.

Example transformation:
    Raw: key_press('c'), key_press('h'), key_press('r'), key_press('o'), key_press('m'), key_press('e'), key_press(enter)
    Semantic: open_application("Chrome")
    
    Raw: click(450, 320)
    Semantic: click_element("Machine Learning", type="course_link", context="Canvas dashboard")
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import base64
import io

from google import genai
from google.genai.types import GenerateContentConfig

from visual_memory import VisualWorkflowMemory


class SemanticActionAnalyzer:
    """
    Analyzes recorded workflows and converts raw actions into semantic understanding.
    
    This enables:
    - "Open Chrome" instead of "press cmd+space, type c-h-r-o-m-e, press enter"
    - "Click Machine Learning course" instead of "click at (450, 320)"
    - Parameter detection: "course_name" can be substituted later
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize semantic analyzer
        
        Args:
            verbose: Print detailed analysis logs
        """
        self.verbose = verbose
        
        # Initialize Gemini
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash-exp"
        
        if self.verbose:
            print("✅ Semantic Action Analyzer initialized")
            print(f"   Model: {self.model}")
    
    def analyze_workflow(self, 
                        workflow_id: str,
                        memory: VisualWorkflowMemory) -> Dict[str, Any]:
        """
        Analyze a recorded workflow and generate semantic actions
        
        Args:
            workflow_id: ID of recorded workflow
            memory: VisualWorkflowMemory instance
        
        Returns:
            Dict with semantic actions and identified parameters
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("🧠 SEMANTIC ANALYSIS")
            print("=" * 70)
        
        # Load workflow
        workflow = memory.get_workflow(workflow_id)
        raw_steps = workflow.get('steps', [])
        
        if not raw_steps:
            print("⚠️  No steps to analyze")
            return {'semantic_actions': [], 'parameters': []}
        
        if self.verbose:
            print(f"\n📊 Analyzing {len(raw_steps)} raw actions...")
        
        # Group consecutive actions
        action_groups = self._group_actions(raw_steps)
        
        if self.verbose:
            print(f"   Grouped into {len(action_groups)} logical actions")
        
        # Analyze each group with visual context
        semantic_actions = []
        workflow_dir = memory.storage_dir / workflow_id
        
        for i, group in enumerate(action_groups, 1):
            if self.verbose:
                print(f"\n🔍 Analyzing action group {i}/{len(action_groups)}...")
            
            semantic_action = self._analyze_action_group(
                group=group,
                workflow_dir=workflow_dir,
                group_number=i
            )
            
            if semantic_action:
                semantic_actions.append(semantic_action)
                
                if self.verbose:
                    print(f"   ✓ {semantic_action['semantic_type']}: {semantic_action.get('description', 'N/A')}")
        
        # Identify parameters across all actions
        if self.verbose:
            print("\n🎯 Identifying parameters...")
        
        parameters = self._identify_parameters(semantic_actions)
        
        if parameters:
            if self.verbose:
                print(f"   ✓ Found {len(parameters)} parameter(s):")
                for param in parameters:
                    print(f"     - {param['name']}: {param['example_value']}")
        else:
            if self.verbose:
                print("   No parameters identified")
        
        return {
            'semantic_actions': semantic_actions,
            'parameters': parameters
        }
    
    def _group_actions(self, raw_steps: List[Dict]) -> List[List[Dict]]:
        """
        Group consecutive raw actions into logical units
        
        Examples:
        - Multiple key_presses → "typing text"
        - Click → "clicking element"
        - Scroll → "scrolling"
        """
        groups = []
        current_group = []
        current_type = None
        
        for step in raw_steps:
            action_type = step['action_type']
            
            # Group consecutive key_presses together (typing)
            if action_type == 'key_press':
                if current_type == 'key_press':
                    current_group.append(step)
                else:
                    if current_group:
                        groups.append(current_group)
                    current_group = [step]
                    current_type = 'key_press'
            
            # Clicks and scrolls are individual actions
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []
                    current_type = None
                
                groups.append([step])
        
        # Add last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _analyze_action_group(self,
                             group: List[Dict],
                             workflow_dir: Path,
                             group_number: int) -> Optional[Dict]:
        """
        Analyze a group of actions and determine semantic meaning
        
        Args:
            group: List of raw action steps
            workflow_dir: Directory containing workflow data
            group_number: Sequential number of this group
        
        Returns:
            Semantic action dict
        """
        if not group:
            return None
        
        first_step = group[0]
        action_type = first_step['action_type']
        
        # Load screenshots for visual context
        screenshot_before = None
        screenshot_after = None
        
        try:
            if first_step.get('screenshot_before'):
                img_path = workflow_dir / "steps" / first_step['screenshot_before']
                if img_path.exists():
                    screenshot_before = Image.open(img_path)
            
            last_step = group[-1]
            if last_step.get('screenshot_after'):
                img_path = workflow_dir / "steps" / last_step['screenshot_after']
                if img_path.exists():
                    screenshot_after = Image.open(img_path)
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not load screenshots: {e}")
        
        # Analyze based on action type
        if action_type == 'key_press':
            return self._analyze_typing_sequence(group, screenshot_before, screenshot_after)
        elif action_type == 'click':
            return self._analyze_click(first_step, screenshot_before, screenshot_after)
        elif action_type == 'scroll':
            return self._analyze_scroll(first_step)
        else:
            # Unknown action type
            return {
                'semantic_type': 'unknown',
                'raw_action_type': action_type,
                'description': f"Unknown action: {action_type}"
            }
    
    def _analyze_typing_sequence(self,
                                 steps: List[Dict],
                                 screenshot_before: Optional[Image.Image],
                                 screenshot_after: Optional[Image.Image]) -> Dict:
        """
        Analyze a sequence of key presses to understand intent
        
        Could be:
        - Opening an application (cmd+space, type app name, enter)
        - Typing text into a field
        - Keyboard shortcuts
        """
        # Extract keys pressed
        keys = []
        for step in steps:
            key = step['action_data'].get('key', '')
            keys.append(key)
        
        # Reconstruct typed text
        typed_text = self._reconstruct_text_from_keys(keys)
        
        # Check if it's an app launch pattern
        # macOS: cmd+space (or alt+space), type app name, enter
        if len(steps) >= 3:
            first_keys = [steps[0]['action_data'].get('key'), steps[1]['action_data'].get('key')]
            last_key = steps[-1]['action_data'].get('key')
            
            # Check for spotlight pattern
            if ('alt' in first_keys or 'cmd' in first_keys) and 'space' in first_keys and 'enter' in last_key:
                # Extract app name (everything between space and enter)
                app_name_keys = [s['action_data'].get('key') for s in steps[2:-1]]
                app_name = ''.join(app_name_keys)
                
                return {
                    'semantic_type': 'open_application',
                    'method': 'spotlight',
                    'target': app_name,
                    'description': f"Open application: {app_name}",
                    'parameterizable': ['target'],
                    'raw_steps': [s['step_number'] for s in steps]
                }
        
        # Otherwise, it's just typing text
        # Use Gemini to understand context if we have screenshots
        if screenshot_before and screenshot_after and typed_text:
            context = self._get_typing_context_from_gemini(
                typed_text=typed_text,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after
            )
            
            if context:
                return {
                    'semantic_type': 'type_text',
                    'text': typed_text,
                    'target': context.get('target_field', 'unknown field'),
                    'description': context.get('description', f"Type: {typed_text}"),
                    'parameterizable': ['text'],
                    'raw_steps': [s['step_number'] for s in steps]
                }
        
        # Fallback
        return {
            'semantic_type': 'type_text',
            'text': typed_text,
            'description': f"Type text: {typed_text}",
            'parameterizable': ['text'] if typed_text else [],
            'raw_steps': [s['step_number'] for s in steps]
        }
    
    def _analyze_click(self,
                      step: Dict,
                      screenshot_before: Optional[Image.Image],
                      screenshot_after: Optional[Image.Image]) -> Dict:
        """
        Analyze a click action to understand what was clicked
        
        Uses Gemini to identify the clicked element from screenshots
        """
        action_data = step['action_data']
        x = action_data.get('x')
        y = action_data.get('y')
        
        if screenshot_before:
            # Use Gemini to identify what's at the click location
            element_info = self._identify_clicked_element_with_gemini(
                screenshot=screenshot_before,
                x=x,
                y=y
            )
            
            if element_info:
                return {
                    'semantic_type': 'click_element',
                    'target': element_info['element_name'],
                    'element_type': element_info.get('element_type', 'unknown'),
                    'description': element_info.get('description', f"Click: {element_info['element_name']}"),
                    'coordinates': {'x': x, 'y': y},  # Keep for reference
                    'parameterizable': element_info.get('parameterizable', []),
                    'raw_steps': [step['step_number']]
                }
        
        # Fallback
        return {
            'semantic_type': 'click_element',
            'target': f"element at ({x}, {y})",
            'coordinates': {'x': x, 'y': y},
            'description': f"Click at coordinates ({x}, {y})",
            'parameterizable': [],
            'raw_steps': [step['step_number']]
        }
    
    def _analyze_scroll(self, step: Dict) -> Dict:
        """Analyze a scroll action"""
        action_data = step['action_data']
        direction = action_data.get('direction', 'down')
        
        return {
            'semantic_type': 'scroll',
            'direction': direction,
            'description': f"Scroll {direction}",
            'parameterizable': [],
            'raw_steps': [step['step_number']]
        }
    
    def _reconstruct_text_from_keys(self, keys: List[str]) -> str:
        """Reconstruct typed text from key sequence"""
        text = []
        
        for key in keys:
            # Skip special keys
            if key.lower() in ['enter', 'tab', 'esc', 'escape', 'backspace', 
                               'delete', 'alt', 'cmd', 'ctrl', 'shift', 'space']:
                continue
            
            # Add regular characters
            if len(key) == 1:
                text.append(key)
        
        return ''.join(text)
    
    def _get_typing_context_from_gemini(self,
                                       typed_text: str,
                                       screenshot_before: Image.Image,
                                       screenshot_after: Image.Image) -> Optional[Dict]:
        """
        Use Gemini to understand the context of typing
        
        Returns:
            Dict with target_field, description, etc.
        """
        try:
            # Encode screenshots
            img_before_b64 = self._encode_image(screenshot_before)
            img_after_b64 = self._encode_image(screenshot_after)
            
            prompt = f"""Analyze these before/after screenshots of a typing action.

Text typed: "{typed_text}"

Please identify:
1. What field was the text typed into? (e.g., "search box", "email field", "title input")
2. What is the purpose of this action? (e.g., "searching for a course", "entering credentials")

Respond in JSON:
{{
    "target_field": "name of the field",
    "description": "brief description of what this accomplishes",
    "field_type": "search/input/textarea/etc"
}}"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/png", "data": img_before_b64}},
                            {"text": "After typing:"},
                            {"inline_data": {"mime_type": "image/png", "data": img_after_b64}}
                        ]
                    }
                ],
                config=GenerateContentConfig(temperature=0.1, max_output_tokens=512)
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Gemini context analysis failed: {e}")
            return None
    
    def _identify_clicked_element_with_gemini(self,
                                             screenshot: Image.Image,
                                             x: int,
                                             y: int) -> Optional[Dict]:
        """
        Use Gemini to identify what element was clicked at coordinates (x, y)
        
        Returns:
            Dict with element_name, element_type, description, parameterizable
        """
        try:
            img_b64 = self._encode_image(screenshot)
            
            # Draw a marker at click location for Gemini to see
            marked_screenshot = screenshot.copy()
            from PIL import ImageDraw
            draw = ImageDraw.Draw(marked_screenshot)
            marker_size = 20
            draw.ellipse(
                [x - marker_size, y - marker_size, x + marker_size, y + marker_size],
                outline='red',
                width=5
            )
            marked_img_b64 = self._encode_image(marked_screenshot)
            
            prompt = f"""A user clicked at coordinates ({x}, {y}) on this screen (marked with red circle).

Please identify:
1. What element was clicked? (button text, link text, icon name, etc.)
2. What type of element is it? (button, link, icon, menu item, etc.)
3. Is this element likely to be parameterizable? (e.g., "Machine Learning" could be any course name)

Respond in JSON:
{{
    "element_name": "exact text or description of clicked element",
    "element_type": "button/link/icon/menu/etc",
    "description": "what clicking this element does",
    "parameterizable": ["list of parts that could vary, e.g., 'course_name' if it's a course link"],
    "is_dynamic": true/false
}}

Examples:
- Clicking "Machine Learning" course link → element_name: "Machine Learning", parameterizable: ["course_name"]
- Clicking "Submit" button → element_name: "Submit", parameterizable: []
"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/png", "data": marked_img_b64}}
                        ]
                    }
                ],
                config=GenerateContentConfig(temperature=0.1, max_output_tokens=512)
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Gemini element identification failed: {e}")
            return None
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL image to base64"""
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def _identify_parameters(self, semantic_actions: List[Dict]) -> List[Dict]:
        """
        Identify parameters across all actions
        
        Parameters are things that can vary between executions:
        - Course names
        - Ticket IDs
        - File names
        - Search terms
        - etc.
        """
        parameters = []
        seen_params = set()
        
        for action in semantic_actions:
            parameterizable = action.get('parameterizable', [])
            
            for param_hint in parameterizable:
                if param_hint in seen_params:
                    continue
                
                seen_params.add(param_hint)
                
                # Extract example value
                example_value = None
                
                if param_hint == 'target' and action.get('target'):
                    example_value = action['target']
                elif param_hint == 'text' and action.get('text'):
                    example_value = action['text']
                elif param_hint == 'course_name' and action.get('target'):
                    example_value = action['target']
                
                if example_value:
                    parameters.append({
                        'name': param_hint,
                        'example_value': example_value,
                        'type': 'string',
                        'description': f"Parameter: {param_hint}"
                    })
        
        return parameters


def test_semantic_analyzer():
    """Test semantic action analysis"""
    print("=" * 70)
    print("Semantic Action Analyzer Test")
    print("=" * 70)
    print()
    
    analyzer = SemanticActionAnalyzer(verbose=True)
    memory = VisualWorkflowMemory()
    
    # List workflows
    workflows = memory.list_workflows()
    
    if not workflows:
        print("❌ No workflows to analyze")
        print("   Record a workflow first!")
        return
    
    print(f"\nFound {len(workflows)} workflow(s):")
    for i, wf in enumerate(workflows, 1):
        print(f"  {i}. {wf['name']} ({wf['steps_count']} steps)")
    
    # Analyze first workflow
    print("\n" + "=" * 70)
    print("Analyzing first workflow...")
    print("=" * 70)
    
    workflow = workflows[0]
    result = analyzer.analyze_workflow(workflow['workflow_id'], memory)
    
    print("\n" + "=" * 70)
    print("SEMANTIC ACTIONS")
    print("=" * 70)
    
    for action in result['semantic_actions']:
        print(f"\n• {action['semantic_type']}")
        print(f"  Description: {action.get('description', 'N/A')}")
        if action.get('target'):
            print(f"  Target: {action['target']}")
        if action.get('parameterizable'):
            print(f"  Parameterizable: {action['parameterizable']}")
    
    print("\n" + "=" * 70)
    print("IDENTIFIED PARAMETERS")
    print("=" * 70)
    
    for param in result['parameters']:
        print(f"\n• {param['name']}")
        print(f"  Example: {param['example_value']}")
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    test_semantic_analyzer()

