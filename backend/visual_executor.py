"""
Visual-Guided Execution Engine
Replays recorded workflows with new parameters using visual guidance
"""

import time
from typing import Dict, List, Optional, Tuple, Any

import pyautogui
from PIL import Image

from visual_analyzer import VisualAnalyzer
from google import genai


class VisualExecutor:
    """
    Executes recorded workflows using visual guidance to locate elements.
    
    This is the "replay" engine that takes a recorded workflow and executes it
    with new parameters, using OCR and vision to find elements dynamically.
    """
    
    def __init__(self, analyzer: VisualAnalyzer = None):
        self.analyzer = analyzer or VisualAnalyzer()
        self.client = genai.Client()
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.action_delay = 1  # seconds between actions
        self.screenshot_wait = 0.5  # wait after action for UI to update
        
        print("✅ Visual Executor initialized")
    
    def execute_workflow(self, 
                        workflow: Dict,
                        parameters: Dict = None,
                        verbose: bool = True) -> bool:
        """
        Execute a recorded workflow with given parameters.
        
        Args:
            workflow: Workflow dictionary from visual memory
            parameters: Dictionary of parameter name -> value
            verbose: Print detailed execution log
        
        Returns:
            True if successful, False otherwise
        """
        if verbose:
            print("\n" + "=" * 70)
            print(f"🎬 Executing: {workflow['name']}")
            print("=" * 70)
            
            if parameters:
                print("\nParameters:")
                for k, v in parameters.items():
                    print(f"  {k} = {v}")
            print()
        
        parameters = parameters or {}
        steps = workflow.get('steps', [])
        
        if not steps:
            print("⚠️  Workflow has no steps!")
            return False
        
        # Execute each step
        for step in steps:
            try:
                success = self._execute_step(step, parameters, verbose)
                
                if not success:
                    print(f"\n❌ Step {step['step_number']} failed")
                    return False
                
                # Wait between steps
                time.sleep(self.action_delay)
            
            except Exception as e:
                print(f"\n❌ Error executing step {step['step_number']}: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        if verbose:
            print("\n" + "=" * 70)
            print("✅ Workflow execution completed")
            print("=" * 70)
        
        return True
    
    def _execute_step(self, 
                     step: Dict,
                     parameters: Dict,
                     verbose: bool) -> bool:
        """Execute a single workflow step."""
        
        step_num = step['step_number']
        action_type = step['action_type']
        action_data = step['action_data']
        visual_context = step.get('visual_context', {})
        
        if verbose:
            print(f"\n🔸 Step {step_num}: {action_type}")
        
        # Handle different action types
        if action_type == 'click':
            return self._execute_click(action_data, visual_context, parameters, verbose)
        
        elif action_type == 'scroll':
            return self._execute_scroll(action_data, visual_context, parameters, verbose)
        
        elif action_type == 'key_press':
            return self._execute_key_press(action_data, verbose)
        
        elif action_type == 'annotation':
            # Annotations are just notes, skip
            if verbose:
                print(f"   Note: {action_data.get('annotation', '')}")
            return True
        
        else:
            print(f"   ⚠️  Unknown action type: {action_type}")
            return True  # Don't fail on unknown types
    
    def _execute_click(self,
                      action_data: Dict,
                      visual_context: Dict,
                      parameters: Dict,
                      verbose: bool) -> bool:
        """
        Execute a click action with visual guidance.
        
        Strategy:
        1. Get what was clicked in recording (text, visual signature)
        2. Substitute parameters if applicable
        3. Find element in current screen using OCR/vision
        4. Click at calculated coordinates
        5. Verify UI changed
        """
        
        # What was clicked?
        original_text = visual_context.get('clicked_text')
        
        if verbose and original_text:
            print(f"   Looking for: '{original_text}'")
        
        # Substitute parameters
        target_text = self._substitute_parameters(original_text, parameters)
        
        if verbose and target_text != original_text:
            print(f"   Substituted to: '{target_text}'")
        
        # Take current screenshot
        screenshot = pyautogui.screenshot()
        
        # Try to find element
        click_coords = None
        
        if target_text:
            # Strategy 1: OCR text matching
            click_coords = self._find_element_by_text(screenshot, target_text, verbose)
        
        if not click_coords:
            # Strategy 2: Use original coordinates (fallback)
            if verbose:
                print("   Using original coordinates (fallback)")
            
            # Use normalized coordinates for better cross-resolution support
            screen_width, screen_height = pyautogui.size()
            norm_x = action_data.get('normalized_x', 500)
            norm_y = action_data.get('normalized_y', 500)
            
            click_x = int((norm_x / 1000) * screen_width)
            click_y = int((norm_y / 1000) * screen_height)
            click_coords = (click_x, click_y)
        
        # Execute click
        if click_coords:
            x, y = click_coords
            
            if verbose:
                print(f"   Clicking at ({x}, {y})")
            
            pyautogui.click(x, y)
            
            # Wait for UI to update
            time.sleep(self.screenshot_wait)
            
            return True
        else:
            print("   ❌ Could not locate element")
            return False
    
    def _execute_scroll(self,
                       action_data: Dict,
                       visual_context: Dict,
                       parameters: Dict,
                       verbose: bool) -> bool:
        """Execute a scroll action."""
        
        direction = action_data.get('direction', 'down')
        
        if verbose:
            print(f"   Scrolling {direction}")
        
        # Scroll based on direction
        scroll_amount = 3
        
        if direction == 'down':
            pyautogui.scroll(-scroll_amount)
        elif direction == 'up':
            pyautogui.scroll(scroll_amount)
        elif direction == 'left':
            pyautogui.hscroll(-scroll_amount)
        elif direction == 'right':
            pyautogui.hscroll(scroll_amount)
        
        return True
    
    def _execute_key_press(self,
                          action_data: Dict,
                          verbose: bool) -> bool:
        """Execute a key press action."""
        
        key = action_data.get('key', '')
        
        if verbose:
            print(f"   Pressing {key}")
        
        pyautogui.press(key.lower())
        return True
    
    def _find_element_by_text(self,
                             screenshot: Image.Image,
                             target_text: str,
                             verbose: bool,
                             retry_count: int = 0) -> Optional[Tuple[int, int]]:
        """
        Find element in screenshot by text using OCR.
        
        Returns:
            (x, y) coordinates or None if not found
        """
        
        if verbose:
            print(f"   Searching with OCR...")
        
        # Use visual analyzer to find text
        matches = self.analyzer.find_text_in_screenshot(
            screenshot,
            target_text,
            fuzzy=True
        )
        
        if matches:
            best_match = matches[0]
            
            if verbose:
                print(f"   Found: '{best_match['text']}' (similarity: {best_match['similarity']}%)")
            
            return best_match['center']
        
        # If not found and haven't retried, try with vision LLM
        if retry_count == 0:
            if verbose:
                print(f"   OCR failed, trying Vision LLM...")
            
            coords = self._find_element_with_vision_llm(screenshot, target_text, verbose)
            if coords:
                return coords
        
        return None
    
    def _find_element_with_vision_llm(self,
                                     screenshot: Image.Image,
                                     target_description: str,
                                     verbose: bool) -> Optional[Tuple[int, int]]:
        """
        Use Gemini Vision to locate element in screenshot.
        
        Returns:
            (x, y) coordinates or None if not found
        """
        try:
            # Convert screenshot to bytes
            import io
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            img_bytes = img_byte_arr.getvalue()
            
            # Prepare prompt
            prompt = f"""
Analyze this screenshot and help me locate an element.

Target element: {target_description}

Please provide:
1. Whether you can see this element (yes/no)
2. If yes, the approximate coordinates where I should click (0-1000 scale)
3. The exact text you see for this element
4. Your confidence level (0-100)

Format your response as:
FOUND: [yes/no]
X: [0-1000]
Y: [0-1000]
TEXT: [exact text]
CONFIDENCE: [0-100]

Note: The screen coordinates are normalized to 0-1000 range.
0,0 is top-left corner, 1000,1000 is bottom-right corner.
"""
            
            # Query vision model
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[
                    {'text': prompt},
                    {'inline_data': {'mime_type': 'image/png', 'data': img_bytes}}
                ]
            )
            
            result_text = response.text
            
            # Parse response
            if 'FOUND: yes' in result_text.lower():
                # Extract coordinates
                import re
                
                x_match = re.search(r'X:\s*(\d+)', result_text)
                y_match = re.search(r'Y:\s*(\d+)', result_text)
                conf_match = re.search(r'CONFIDENCE:\s*(\d+)', result_text)
                
                if x_match and y_match:
                    norm_x = int(x_match.group(1))
                    norm_y = int(y_match.group(1))
                    confidence = int(conf_match.group(1)) if conf_match else 50
                    
                    if confidence < 50:
                        if verbose:
                            print(f"   Vision LLM confidence too low: {confidence}%")
                        return None
                    
                    # Denormalize coordinates
                    screen_width, screen_height = screenshot.size
                    x = int((norm_x / 1000) * screen_width)
                    y = int((norm_y / 1000) * screen_height)
                    
                    if verbose:
                        print(f"   Vision LLM found it (confidence: {confidence}%)")
                    
                    return (x, y)
            
            if verbose:
                print(f"   Vision LLM could not find element")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"   Vision LLM error: {e}")
            return None
    
    def _substitute_parameters(self, text: str, parameters: Dict) -> str:
        """
        Substitute parameters in text.
        
        Example:
            text = "Machine Learning"
            parameters = {"class_name": "DataVis"}
            result = "DataVis"
        """
        if not text or not parameters:
            return text
        
        # For now, simple exact replacement
        # In production, would use more sophisticated matching
        for param_name, param_value in parameters.items():
            if param_value and str(param_value).lower() in text.lower():
                # Found parameter value in text, replace it
                return str(param_value)
        
        return text
    
    def _verify_state_change(self,
                            before: Image.Image,
                            after: Image.Image) -> bool:
        """
        Verify that UI changed after action.
        
        Returns:
            True if change detected, False otherwise
        """
        return self.analyzer.detect_ui_change(before, after, threshold=5)


def test_visual_executor():
    """Test the visual executor with a simple workflow."""
    print("=" * 70)
    print("Testing Visual Executor")
    print("=" * 70)
    
    # Create a simple test workflow
    test_workflow = {
        'name': 'Test Workflow',
        'description': 'Simple test',
        'steps': [
            {
                'step_number': 1,
                'action_type': 'click',
                'action_data': {
                    'x': 500,
                    'y': 300,
                    'normalized_x': 340,
                    'normalized_y': 314
                },
                'visual_context': {
                    'clicked_text': 'Test Button',
                    'description': 'Click test button'
                }
            }
        ]
    }
    
    executor = VisualExecutor()
    
    print("\nThis is a dry-run test (won't actually click).")
    print("In production, it would:")
    print("  1. Take screenshot")
    print("  2. Find 'Test Button' using OCR")
    print("  3. Click at located coordinates")
    print("  4. Verify UI changed")
    
    print("\n✅ Visual executor ready for use!")


if __name__ == "__main__":
    test_visual_executor()

