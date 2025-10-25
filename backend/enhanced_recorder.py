"""
Enhanced Workflow Recorder with Rich Context Extraction
Records workflows with deep visual and semantic analysis
"""

import time
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

import pyautogui
from PIL import Image
from pynput import mouse, keyboard

from visual_memory import VisualWorkflowMemory
from enhanced_context_system import EnhancedContextExtractor, ActionContext


class EnhancedWorkflowRecorder:
    """
    Enhanced recorder that captures rich context during workflow demonstration.
    
    Key improvements over basic recorder:
    - Real-time OCR and element extraction
    - Automatic parameter detection
    - Semantic understanding of actions
    - Visual signatures for robust replay
    """
    
    def __init__(self, memory: VisualWorkflowMemory = None):
        self.memory = memory or VisualWorkflowMemory()
        self.context_extractor = EnhancedContextExtractor()
        
        self.is_recording = False
        self.workflow_id = None
        self.workflow_name = None
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # State
        self.last_screenshot = None
        self.last_action_time = 0
        self.step_count = 0
        
        # Context accumulation
        self.action_contexts: List[ActionContext] = []
        self.detected_parameters: Dict[str, Any] = {}
        
        # Configuration
        self.min_action_interval = 0.5  # Debounce
        self.analysis_enabled = True  # Enable deep analysis
        
        print("✅ Enhanced Workflow Recorder initialized")
        print("   - Real-time OCR enabled")
        print("   - Parameter detection enabled")
        print("   - Semantic analysis enabled")
    
    def start_recording(self,
                       workflow_name: str,
                       description: str = "",
                       tags: List[str] = None) -> str:
        """
        Start recording with enhanced context extraction.
        """
        if self.is_recording:
            print("⚠️  Already recording!")
            return None
        
        # Create workflow
        self.workflow_id = self.memory.create_workflow(
            name=workflow_name,
            description=description,
            tags=tags or []
        )
        
        self.workflow_name = workflow_name
        self.step_count = 0
        self.action_contexts = []
        self.detected_parameters = {}
        
        # Initial screenshot
        print("\n📸 Capturing initial state...")
        self.last_screenshot = pyautogui.screenshot()
        
        # Start listeners
        self._start_listeners()
        
        self.is_recording = True
        self.last_action_time = time.time()
        
        print("\n" + "=" * 70)
        print(f"🔴 RECORDING: {workflow_name}")
        print("=" * 70)
        print("✨ Enhanced recording mode active")
        print("   - Every action will be deeply analyzed")
        print("   - UI elements will be identified")
        print("   - Parameters will be auto-detected")
        print()
        print("Perform your workflow slowly and deliberately.")
        print("The system will learn from your actions!")
        print()
        print("When done, stop with: recorder.stop_recording()")
        print("=" * 70)
        
        return self.workflow_id
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and analyze the complete workflow.
        """
        if not self.is_recording:
            print("⚠️  Not recording!")
            return None
        
        self.is_recording = False
        self._stop_listeners()
        
        print("\n" + "=" * 70)
        print(f"⏹  STOPPED RECORDING: {self.workflow_name}")
        print("=" * 70)
        print(f"\nRecorded {self.step_count} steps")
        
        # Analyze complete workflow
        print("\n🧠 Analyzing workflow...")
        self._analyze_complete_workflow()
        
        # Show detected parameters
        if self.detected_parameters:
            print("\n📊 Detected Parameters:")
            for param_name, info in self.detected_parameters.items():
                print(f"  • {param_name}")
                print(f"    Example: {info['example']}")
                print(f"    Type: {info['type']}")
                if 'steps' in info:
                    print(f"    Used in steps: {', '.join(map(str, info['steps']))}")
        else:
            print("\n✓ No variable parameters detected (workflow is fully specified)")
        
        # Save parameters to workflow
        param_list = []
        for param_name, info in self.detected_parameters.items():
            param_list.append({
                'name': param_name,
                'type': info['type'],
                'example': info['example'],
                'description': info.get('description', f'Parameter {param_name}'),
                'steps': info.get('steps', [])
            })
        
        self.memory.finalize_workflow(self.workflow_id, parameters=param_list)
        
        print("\n✅ Workflow saved and ready for use!")
        print("=" * 70)
        
        workflow_id = self.workflow_id
        self.workflow_id = None
        self.workflow_name = None
        
        return workflow_id
    
    def _start_listeners(self):
        """Start input listeners"""
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()
    
    def _stop_listeners(self):
        """Stop all listeners"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle click with deep analysis"""
        if not self.is_recording or not pressed:
            return
        
        # Debounce
        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return
        
        self.last_action_time = current_time
        self.step_count += 1
        
        print(f"\n🔸 Step {self.step_count}: Click at ({x}, {y})")
        print("   Analyzing...")
        
        # Capture state
        screenshot_before = self.last_screenshot
        time.sleep(0.15)  # Wait for UI update
        screenshot_after = pyautogui.screenshot()
        
        # Get screen size for normalization
        screen_width, screen_height = pyautogui.size()
        
        # Action data
        action_data = {
            'x': int(x),
            'y': int(y),
            'button': str(button),
            'normalized_x': int((x / screen_width) * 1000),
            'normalized_y': int((y / screen_height) * 1000),
            'timestamp': current_time
        }
        
        # Extract rich context
        if self.analysis_enabled:
            context = self.context_extractor.extract_action_context(
                step_number=self.step_count,
                action_type='click',
                action_data=action_data,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                workflow_id=self.workflow_id
            )
            
            self.action_contexts.append(context)
            
            # Show what was detected
            if context.clicked_element:
                print(f"   ✓ Clicked: '{context.clicked_element.text}'")
                print(f"     Type: {context.clicked_element.element_type}")
                
                if context.is_parameterizable:
                    print(f"     🎯 Parameterizable!")
                    
                    # Track parameter
                    if context.extracted_entities:
                        for param_name, value in context.extracted_entities.items():
                            if param_name not in self.detected_parameters:
                                self.detected_parameters[param_name] = {
                                    'example': value,
                                    'type': 'string',
                                    'steps': []
                                }
                            self.detected_parameters[param_name]['steps'].append(self.step_count)
            
            # Build visual context for storage
            visual_context = context.to_dict()
        else:
            # Fallback to basic context
            visual_context = {
                'description': f"Click at ({x}, {y})",
                'screen_size': (screen_width, screen_height)
            }
        
        # Save to memory
        self.memory.add_step(
            workflow_id=self.workflow_id,
            action_type='click',
            action_data=action_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            visual_context=visual_context
        )
        
        self.last_screenshot = screenshot_after
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle scroll action"""
        if not self.is_recording:
            return
        
        # Debounce
        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return
        
        self.last_action_time = current_time
        self.step_count += 1
        
        # Determine direction
        if dy > 0:
            direction = 'up'
        elif dy < 0:
            direction = 'down'
        elif dx > 0:
            direction = 'right'
        else:
            direction = 'left'
        
        print(f"\n🔸 Step {self.step_count}: Scroll {direction}")
        
        # Capture state
        screenshot_before = self.last_screenshot
        time.sleep(0.1)
        screenshot_after = pyautogui.screenshot()
        
        action_data = {
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'direction': direction,
            'timestamp': current_time
        }
        
        visual_context = {
            'description': f"Scroll {direction}",
            'action_type': 'scroll'
        }
        
        self.memory.add_step(
            workflow_id=self.workflow_id,
            action_type='scroll',
            action_data=action_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            visual_context=visual_context
        )
        
        self.last_screenshot = screenshot_after
    
    def _on_key_press(self, key):
        """Handle keyboard events"""
        if not self.is_recording:
            return
        
        # Only track special keys
        special_keys = [
            keyboard.Key.enter,
            keyboard.Key.tab,
            keyboard.Key.esc,
            keyboard.Key.backspace,
            keyboard.Key.delete
        ]
        
        if key not in special_keys:
            return
        
        # Debounce
        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return
        
        self.last_action_time = current_time
        self.step_count += 1
        
        key_name = str(key).replace('Key.', '')
        print(f"\n🔸 Step {self.step_count}: Press {key_name}")
        
        # Capture state
        screenshot_before = self.last_screenshot
        time.sleep(0.1)
        screenshot_after = pyautogui.screenshot()
        
        action_data = {
            'key': key_name,
            'timestamp': current_time
        }
        
        visual_context = {
            'description': f"Press {key_name}"
        }
        
        self.memory.add_step(
            workflow_id=self.workflow_id,
            action_type='key_press',
            action_data=action_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            visual_context=visual_context
        )
        
        self.last_screenshot = screenshot_after
    
    def _analyze_complete_workflow(self):
        """
        Analyze the complete recorded workflow to extract patterns.
        This is called after recording stops.
        """
        if not self.action_contexts:
            return
        
        # Analyze action sequence patterns
        print("   • Analyzing action sequence...")
        
        # Check for repeating patterns
        # (Could implement pattern mining here)
        
        # Analyze parameter usage across steps
        print("   • Analyzing parameter usage...")
        
        for param_name, info in self.detected_parameters.items():
            # Determine parameter type based on usage
            example = info['example']
            
            if example.isdigit():
                info['type'] = 'number'
            elif any(word in example.lower() for word in ['http', 'www', '.com']):
                info['type'] = 'url'
            else:
                info['type'] = 'string'
            
            # Add description based on context
            if 'class' in param_name:
                info['description'] = 'Name of the class to open'
            elif 'file' in param_name:
                info['description'] = 'Name of the file to interact with'
            elif 'folder' in param_name:
                info['description'] = 'Name of the folder to open'
            else:
                info['description'] = f'Value for {param_name}'
        
        print("   ✓ Analysis complete")
    
    def add_manual_parameter(self, param_name: str, param_value: str, param_type: str = 'string'):
        """
        Manually annotate a parameter during recording.
        
        Usage during recording:
            recorder.add_manual_parameter('class_name', 'Machine Learning')
        """
        if not self.is_recording:
            print("⚠️  Not currently recording")
            return
        
        self.detected_parameters[param_name] = {
            'example': param_value,
            'type': param_type,
            'description': f'User-specified {param_name}',
            'steps': [self.step_count]  # Associate with current step
        }
        
        print(f"📝 Parameter added: {param_name} = '{param_value}'")


def interactive_demo():
    """Interactive demo of enhanced recording"""
    print("=" * 70)
    print("Enhanced Workflow Recording Demo")
    print("=" * 70)
    print()
    print("This will record your actions with deep analysis:")
    print("  ✓ OCR text extraction")
    print("  ✓ UI element identification")
    print("  ✓ Automatic parameter detection")
    print("  ✓ Visual signatures")
    print()
    
    workflow_name = input("Workflow name: ").strip()
    if not workflow_name:
        workflow_name = "Test Workflow"
    
    description = input("Description (optional): ").strip()
    
    print()
    input("Press Enter to start recording...")
    
    recorder = EnhancedWorkflowRecorder()
    workflow_id = recorder.start_recording(workflow_name, description, tags=['test'])
    
    print("\n⏱  Recording for 20 seconds...")
    print("Perform your workflow now!")
    
    time.sleep(20)
    
    workflow_id = recorder.stop_recording()
    
    # Show results
    print("\n" + "=" * 70)
    print("RECORDING COMPLETE")
    print("=" * 70)
    
    workflow = recorder.memory.get_workflow(workflow_id)
    
    print(f"\nWorkflow: {workflow['name']}")
    print(f"Steps: {workflow['steps_count']}")
    
    if workflow.get('parameters'):
        print("\nParameters detected:")
        for param in workflow['parameters']:
            print(f"  • {param['name']}: {param['example']}")
    
    print("\nWorkflow steps:")
    for step in workflow['steps']:
        visual_ctx = step.get('visual_context', {})
        
        if step['action_type'] == 'click':
            clicked_elem = visual_ctx.get('clicked_element')
            if clicked_elem and isinstance(clicked_elem, dict):
                text = clicked_elem.get('text', 'unknown')
                print(f"  {step['step_number']}. Click '{text}'")
            else:
                print(f"  {step['step_number']}. Click")
        elif step['action_type'] == 'scroll':
            direction = step['action_data'].get('direction', '?')
            print(f"  {step['step_number']}. Scroll {direction}")
        else:
            print(f"  {step['step_number']}. {step['action_type']}")
    
    print("\n✅ Demo complete!")
    print(f"Workflow saved with ID: {workflow_id}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        interactive_demo()
    else:
        print("Usage: python enhanced_recorder.py demo")
        print()
        print("Or import and use programmatically:")
        print("  from enhanced_recorder import EnhancedWorkflowRecorder")
        print("  recorder = EnhancedWorkflowRecorder()")
        print("  recorder.start_recording('My Workflow', 'Description')")
        print("  # ... user performs actions ...")
        print("  recorder.stop_recording()")

