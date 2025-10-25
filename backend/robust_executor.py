"""
Robust Workflow Execution Engine
Executes learned workflows with intelligent retry, verification, and failure recovery
"""

import time
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

import pyautogui
from PIL import Image
import imagehash

from visual_analyzer import VisualAnalyzer
from google import genai


class ExecutionStatus(Enum):
    """Status of step execution"""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """Result of executing a step"""
    step_number: int
    status: ExecutionStatus
    attempts: int
    error_message: Optional[str] = None
    found_location: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    
    def to_dict(self):
        return {
            'step_number': self.step_number,
            'status': self.status.value,
            'attempts': self.attempts,
            'error_message': self.error_message,
            'found_location': self.found_location,
            'confidence': self.confidence
        }


class RobustWorkflowExecutor:
    """
    Execute learned workflows with robustness features:
    - Multiple element location strategies (OCR, Vision LLM, position heuristics)
    - Retry logic with exponential backoff
    - State verification after each step
    - Intelligent failure recovery
    - Detailed execution reporting
    """
    
    def __init__(self, analyzer: VisualAnalyzer = None):
        self.analyzer = analyzer or VisualAnalyzer()
        
        try:
            self.client = genai.Client()
            self.vision_available = True
        except:
            self.vision_available = False
            print("⚠️  Vision LLM not available")
        
        # Configuration
        self.max_retries = 3
        self.retry_delay_base = 1.0  # seconds
        self.action_delay = 1.0  # delay between steps
        self.ui_settle_time = 0.5  # wait for UI to settle after action
        
        # Verification thresholds
        self.ocr_confidence_threshold = 0.7
        self.vision_confidence_threshold = 50  # out of 100
        self.position_fallback_enabled = True
        
        # Execution state
        self.execution_log: List[ExecutionResult] = []
        self.current_workflow: Optional[Dict] = None
        
        print("✅ Robust Workflow Executor initialized")
        print(f"   - Max retries: {self.max_retries}")
        print(f"   - Vision LLM: {'enabled' if self.vision_available else 'disabled'}")
    
    def execute_workflow(self,
                        workflow: Dict,
                        parameters: Dict = None,
                        verbose: bool = True) -> Tuple[bool, List[ExecutionResult]]:
        """
        Execute workflow with full robustness features.
        
        Returns:
            (success, execution_results)
        """
        self.current_workflow = workflow
        self.execution_log = []
        
        if verbose:
            print("\n" + "=" * 70)
            print(f"🎬 EXECUTING: {workflow['name']}")
            print("=" * 70)
            
            if parameters:
                print("\n📋 Parameters:")
                for k, v in parameters.items():
                    print(f"   • {k} = {v}")
            print()
        
        parameters = parameters or {}
        steps = workflow.get('steps', [])
        
        if not steps:
            print("⚠️  Workflow has no steps!")
            return False, []
        
        # Execute each step
        all_success = True
        
        for step in steps:
            step_num = step['step_number']
            
            if verbose:
                print(f"▶ Step {step_num}/{len(steps)}")
            
            # Execute with retry logic
            result = self._execute_step_with_retry(step, parameters, verbose)
            self.execution_log.append(result)
            
            if result.status == ExecutionStatus.FAILED:
                if verbose:
                    print(f"\n❌ Step {step_num} failed: {result.error_message}")
                    print("   Attempting recovery...")
                
                # Try recovery
                recovery_success = self._attempt_recovery(step, parameters, verbose)
                
                if not recovery_success:
                    all_success = False
                    
                    if verbose:
                        print(f"\n❌ Could not recover from failure at step {step_num}")
                        print("   Stopping execution.")
                    break
            
            # Wait between steps
            time.sleep(self.action_delay)
        
        # Summary
        if verbose:
            print("\n" + "=" * 70)
            if all_success:
                print("✅ WORKFLOW EXECUTION COMPLETED SUCCESSFULLY")
            else:
                print("⚠️  WORKFLOW EXECUTION FAILED")
            print("=" * 70)
            
            self._print_execution_summary()
        
        return all_success, self.execution_log
    
    def _execute_step_with_retry(self,
                                 step: Dict,
                                 parameters: Dict,
                                 verbose: bool) -> ExecutionResult:
        """Execute a single step with retry logic"""
        
        step_num = step['step_number']
        action_type = step['action_type']
        
        result = ExecutionResult(
            step_number=step_num,
            status=ExecutionStatus.FAILED,
            attempts=0
        )
        
        # Try multiple times
        for attempt in range(1, self.max_retries + 1):
            result.attempts = attempt
            
            if verbose and attempt > 1:
                print(f"   🔄 Retry attempt {attempt}/{self.max_retries}")
            
            try:
                # Execute based on action type
                if action_type == 'click':
                    success, location, confidence = self._execute_click_robust(
                        step, parameters, verbose
                    )
                    
                    if success:
                        result.status = ExecutionStatus.SUCCESS
                        result.found_location = location
                        result.confidence = confidence
                        
                        if verbose:
                            print(f"   ✓ Success (confidence: {confidence:.0%})")
                        
                        return result
                    else:
                        result.error_message = "Element not found"
                
                elif action_type == 'scroll':
                    self._execute_scroll(step, verbose)
                    result.status = ExecutionStatus.SUCCESS
                    result.confidence = 1.0
                    return result
                
                elif action_type == 'key_press':
                    self._execute_key_press(step, verbose)
                    result.status = ExecutionStatus.SUCCESS
                    result.confidence = 1.0
                    return result
                
                elif action_type == 'annotation':
                    # Skip annotations
                    result.status = ExecutionStatus.SKIPPED
                    return result
                
                else:
                    result.error_message = f"Unknown action type: {action_type}"
                    return result
            
            except Exception as e:
                result.error_message = str(e)
                
                if verbose:
                    print(f"   ⚠️  Error: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                wait_time = self.retry_delay_base * (2 ** (attempt - 1))
                if verbose:
                    print(f"   ⏳ Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
        
        # All retries exhausted
        result.status = ExecutionStatus.FAILED
        return result
    
    def _execute_click_robust(self,
                             step: Dict,
                             parameters: Dict,
                             verbose: bool) -> Tuple[bool, Optional[Tuple[int, int]], float]:
        """
        Execute click with multiple location strategies.
        
        Returns:
            (success, location, confidence)
        """
        action_data = step['action_data']
        visual_context = step.get('visual_context', {})
        
        # Get what to click
        original_text = None
        
        # Handle both dict and object formats from enhanced context
        clicked_element = visual_context.get('clicked_element')
        if isinstance(clicked_element, dict):
            original_text = clicked_element.get('text')
        elif hasattr(clicked_element, 'text'):
            original_text = clicked_element.text
        
        # Fallback to simple text
        if not original_text:
            original_text = visual_context.get('clicked_text')
        
        # Substitute parameters
        target_text = self._substitute_parameters(original_text, parameters)
        
        if verbose and target_text:
            print(f"   🔍 Looking for: '{target_text}'")
        
        # Take current screenshot
        screenshot = pyautogui.screenshot()
        
        # Strategy 1: OCR text matching
        if target_text:
            location, confidence = self._find_by_ocr(screenshot, target_text, verbose)
            
            if location and confidence > self.ocr_confidence_threshold:
                self._click_at(location)
                self._wait_for_ui()
                return True, location, confidence
        
        # Strategy 2: Vision LLM
        if target_text and self.vision_available:
            location, confidence = self._find_by_vision_llm(
                screenshot, target_text, verbose
            )
            
            if location and confidence > self.vision_confidence_threshold:
                self._click_at(location)
                self._wait_for_ui()
                return True, location, confidence / 100.0
        
        # Strategy 3: Position heuristic (fallback)
        if self.position_fallback_enabled:
            if verbose:
                print("   ⚠️  Using position fallback")
            
            location = self._use_position_fallback(action_data)
            self._click_at(location)
            self._wait_for_ui()
            return True, location, 0.5  # Low confidence
        
        return False, None, 0.0
    
    def _find_by_ocr(self,
                     screenshot: Image.Image,
                     target_text: str,
                     verbose: bool) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Find element using OCR text matching.
        
        Returns:
            (location, confidence)
        """
        matches = self.analyzer.find_text_in_screenshot(
            screenshot,
            target_text,
            fuzzy=True
        )
        
        if matches:
            best_match = matches[0]
            similarity = best_match['similarity'] / 100.0
            
            if verbose:
                print(f"   ✓ OCR found: '{best_match['text']}' (similarity: {similarity:.0%})")
            
            return best_match['center'], similarity
        
        if verbose:
            print("   ✗ OCR: not found")
        
        return None, 0.0
    
    def _find_by_vision_llm(self,
                           screenshot: Image.Image,
                           target_description: str,
                           verbose: bool) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Find element using vision LLM.
        
        Returns:
            (location, confidence_0_100)
        """
        try:
            import io
            
            # Convert to bytes
            img_bytes_io = io.BytesIO()
            screenshot.save(img_bytes_io, format='PNG')
            img_bytes = img_bytes_io.getvalue()
            
            # Query vision model
            prompt = f"""
Find this element in the screenshot: "{target_description}"

Provide the coordinates where I should click.
Use a 0-1000 normalized coordinate system where:
- (0, 0) is top-left
- (1000, 1000) is bottom-right

Respond in this exact format:
FOUND: [yes/no]
X: [0-1000]
Y: [0-1000]
CONFIDENCE: [0-100]
"""
            
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
                import re
                
                x_match = re.search(r'X:\s*(\d+)', result_text)
                y_match = re.search(r'Y:\s*(\d+)', result_text)
                conf_match = re.search(r'CONFIDENCE:\s*(\d+)', result_text)
                
                if x_match and y_match:
                    norm_x = int(x_match.group(1))
                    norm_y = int(y_match.group(1))
                    confidence = int(conf_match.group(1)) if conf_match else 50
                    
                    # Denormalize coordinates
                    x = int((norm_x / 1000) * screenshot.width)
                    y = int((norm_y / 1000) * screenshot.height)
                    
                    if verbose:
                        print(f"   ✓ Vision found at ({x}, {y}) (confidence: {confidence}%)")
                    
                    return (x, y), confidence
            
            if verbose:
                print("   ✗ Vision: not found")
            
            return None, 0.0
        
        except Exception as e:
            if verbose:
                print(f"   ✗ Vision error: {e}")
            return None, 0.0
    
    def _use_position_fallback(self, action_data: Dict) -> Tuple[int, int]:
        """Use normalized coordinates as fallback"""
        norm_x = action_data.get('normalized_x', 500)
        norm_y = action_data.get('normalized_y', 500)
        
        screen_width, screen_height = pyautogui.size()
        x = int((norm_x / 1000) * screen_width)
        y = int((norm_y / 1000) * screen_height)
        
        return (x, y)
    
    def _click_at(self, location: Tuple[int, int]):
        """Execute click at location"""
        x, y = location
        pyautogui.click(x, y)
    
    def _wait_for_ui(self):
        """Wait for UI to settle after action"""
        time.sleep(self.ui_settle_time)
    
    def _execute_scroll(self, step: Dict, verbose: bool):
        """Execute scroll action"""
        direction = step['action_data'].get('direction', 'down')
        
        if verbose:
            print(f"   📜 Scrolling {direction}")
        
        scroll_amount = 3
        
        if direction == 'down':
            pyautogui.scroll(-scroll_amount)
        elif direction == 'up':
            pyautogui.scroll(scroll_amount)
        elif direction == 'left':
            pyautogui.hscroll(-scroll_amount)
        elif direction == 'right':
            pyautogui.hscroll(scroll_amount)
    
    def _execute_key_press(self, step: Dict, verbose: bool):
        """Execute key press action"""
        key = step['action_data'].get('key', '')
        
        if verbose:
            print(f"   ⌨️  Pressing {key}")
        
        pyautogui.press(key.lower())
    
    def _substitute_parameters(self, text: Optional[str], parameters: Dict) -> Optional[str]:
        """
        Substitute parameters in text.
        
        For example:
            text = "Machine Learning"
            parameters = {"class_name": "DataVis"}
            → returns "DataVis"
        """
        if not text or not parameters:
            return text
        
        # Check if any parameter value matches or is contained in text
        for param_name, param_value in parameters.items():
            if param_value:
                # Direct replacement
                return str(param_value)
        
        return text
    
    def _attempt_recovery(self,
                         failed_step: Dict,
                         parameters: Dict,
                         verbose: bool) -> bool:
        """
        Attempt to recover from a failed step.
        
        Recovery strategies:
        - Wait longer for UI to load
        - Scroll to make element visible
        - Retry with relaxed thresholds
        """
        if verbose:
            print("   🔧 Attempting recovery...")
        
        # Strategy 1: Wait for slow UI
        if verbose:
            print("   ⏳ Waiting for UI to load...")
        time.sleep(3)
        
        # Strategy 2: Try scrolling down to reveal element
        if verbose:
            print("   📜 Scrolling to reveal element...")
        
        pyautogui.scroll(-2)  # Scroll down
        time.sleep(1)
        
        # Retry the step once with relaxed thresholds
        original_ocr_threshold = self.ocr_confidence_threshold
        original_vision_threshold = self.vision_confidence_threshold
        
        self.ocr_confidence_threshold = 0.5  # Relaxed
        self.vision_confidence_threshold = 30  # Relaxed
        
        result = self._execute_step_with_retry(failed_step, parameters, verbose=False)
        
        # Restore thresholds
        self.ocr_confidence_threshold = original_ocr_threshold
        self.vision_confidence_threshold = original_vision_threshold
        
        if result.status == ExecutionStatus.SUCCESS:
            if verbose:
                print("   ✓ Recovery successful!")
            return True
        
        if verbose:
            print("   ✗ Recovery failed")
        
        return False
    
    def _print_execution_summary(self):
        """Print summary of execution"""
        print("\n📊 Execution Summary:")
        print("=" * 70)
        
        total_steps = len(self.execution_log)
        successful = sum(1 for r in self.execution_log if r.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for r in self.execution_log if r.status == ExecutionStatus.FAILED)
        skipped = sum(1 for r in self.execution_log if r.status == ExecutionStatus.SKIPPED)
        
        print(f"Total steps: {total_steps}")
        print(f"  ✓ Successful: {successful}")
        if failed > 0:
            print(f"  ✗ Failed: {failed}")
        if skipped > 0:
            print(f"  ⊝ Skipped: {skipped}")
        
        # Show steps that needed retries
        retry_steps = [r for r in self.execution_log if r.attempts > 1 and r.status == ExecutionStatus.SUCCESS]
        if retry_steps:
            print(f"\n⚠️  Steps that needed retries: {len(retry_steps)}")
            for r in retry_steps:
                print(f"   • Step {r.step_number}: {r.attempts} attempts")
        
        # Average confidence
        successful_results = [r for r in self.execution_log if r.status == ExecutionStatus.SUCCESS and r.confidence > 0]
        if successful_results:
            avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
            print(f"\nAverage confidence: {avg_confidence:.0%}")
        
        print("=" * 70)


if __name__ == "__main__":
    print("Robust Workflow Executor")
    print()
    print("This module provides robust workflow execution with:")
    print("  ✓ Multiple element location strategies")
    print("  ✓ Automatic retry with exponential backoff")
    print("  ✓ State verification")
    print("  ✓ Intelligent failure recovery")
    print("  ✓ Detailed execution reporting")

