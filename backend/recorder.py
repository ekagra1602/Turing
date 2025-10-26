"""
Workflow Recorder - Learn by Observation
Monitors user actions and captures visual context for workflow learning
"""

import time
import threading
from typing import Callable, Optional
from pathlib import Path
from datetime import datetime

import pyautogui
from PIL import Image
from pynput import mouse, keyboard

from visual_memory import VisualWorkflowMemory


class WorkflowRecorder:
    """
    Records user actions with visual context to learn workflows.
    
    Usage:
        recorder = WorkflowRecorder()
        workflow_id = recorder.start_recording("Open Canvas Class")
        # User performs actions...
        recorder.stop_recording()
    """
    
    def __init__(self, memory: VisualWorkflowMemory = None):
        self.memory = memory or VisualWorkflowMemory()
        
        self.is_recording = False
        self.workflow_id = None
        self.workflow_name = None
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # State tracking
        self.last_screenshot = None
        self.last_action_time = 0
        self.action_buffer = []
        
        # Configuration
        self.min_action_interval = 0.5  # Minimum seconds between actions
        self.screenshot_on_action = True
        self.track_mouse_moves = False  # Usually too noisy
        
        print("✅ Workflow Recorder initialized")
    
    def start_recording(self, workflow_name: str, description: str = "", tags: list = None):
        """
        Start recording a new workflow.
        
        Args:
            workflow_name: Name for this workflow
            description: Description of what this workflow does
            tags: Optional tags for categorization
        
        Returns:
            workflow_id: ID of the created workflow
        """
        if self.is_recording:
            print("⚠️  Already recording. Stop current recording first.")
            return None
        
        # Create workflow in memory
        self.workflow_id = self.memory.create_workflow(
            name=workflow_name,
            description=description,
            tags=tags or []
        )
        self.workflow_name = workflow_name
        
        # Take initial screenshot
        self.last_screenshot = self._capture_screenshot()
        
        # Start listeners
        self._start_listeners()
        
        self.is_recording = True
        self.last_action_time = time.time()
        
        return self.workflow_id
    
    def stop_recording(self):
        """Stop recording and finalize the workflow."""
        if not self.is_recording:
            print("⚠️  Not currently recording.")
            return None
        
        self.is_recording = False
        
        # Stop listeners
        self._stop_listeners()
        
        # Process any remaining buffered actions
        self._flush_buffer()
        
        # Finalize workflow
        print("\n" + "=" * 70)
        print(f"⏹  STOPPED RECORDING: {self.workflow_name}")
        print("=" * 70)
        
        # Get workflow data
        workflow_data = self.memory.get_workflow(self.workflow_id)
        steps_count = workflow_data['steps_count']
        print(f"\nRecorded {steps_count} raw steps")
        
        # Simple VLM analysis - just get overall intention
        print("\n🧠 Understanding workflow...")
        
        try:
            intention = self._analyze_with_vlm()
            print(f"   ✓ Goal: {intention}")
            
            # Save workflow with intention
            self.memory.finalize_workflow(
                self.workflow_id,
                parameters=[],
                semantic_actions=[{
                    'overall_intention': intention,
                    'steps_count': steps_count
                }]
            )
            print(f"\n✅ Workflow saved!")
            
        except Exception as e:
            print(f"⚠️  Analysis skipped: {e}")
            # Still save workflow
            self.memory.finalize_workflow(self.workflow_id)
            print(f"\n✅ Workflow saved (without analysis)!")
        
        workflow_id = self.workflow_id
        self.workflow_id = None
        self.workflow_name = None
        
        return workflow_id
    
    def _start_listeners(self):
        """Start mouse and keyboard listeners."""
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
        """Stop all listeners."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def _capture_screenshot(self) -> Image.Image:
        """Capture current screen state."""
        return pyautogui.screenshot()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if not self.is_recording or not self.workflow_id:
            return
        
        # Only record button press (not release)
        if not pressed:
            return
        
        # Debounce - avoid recording too frequently
        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return
        
        self.last_action_time = current_time
        
        # Capture action
        screenshot_before = self.last_screenshot
        time.sleep(0.1)  # Small delay for UI to update
        screenshot_after = self._capture_screenshot()
        
        # Get screen size for normalization
        screen_width, screen_height = pyautogui.size()
        
        # Record the action
        action_data = {
            'x': x,
            'y': y,
            'button': str(button),
            'normalized_x': int((x / screen_width) * 1000),
            'normalized_y': int((y / screen_height) * 1000),
            'timestamp': current_time
        }
        
        # Add visual context (basic for now, will enhance with OCR later)
        visual_context = {
            'description': f"Click at ({x}, {y})",
            'screen_size': (screen_width, screen_height)
        }
        
        # Add step to workflow
        self.memory.add_step(
            workflow_id=self.workflow_id,
            action_type='click',
            action_data=action_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            visual_context=visual_context
        )
        
        # Update last screenshot
        self.last_screenshot = screenshot_after
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events."""
        if not self.is_recording or not self.workflow_id:
            return
        
        # Debounce
        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return
        
        self.last_action_time = current_time
        
        # Capture state
        screenshot_before = self.last_screenshot
        time.sleep(0.1)
        screenshot_after = self._capture_screenshot()
        
        # Determine scroll direction
        if dy > 0:
            direction = 'up'
        elif dy < 0:
            direction = 'down'
        elif dx > 0:
            direction = 'right'
        else:
            direction = 'left'
        
        action_data = {
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'direction': direction,
            'timestamp': current_time
        }
        
        visual_context = {
            'description': f"Scroll {direction} at ({x}, {y})"
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
        """Handle keyboard events."""
        if not self.is_recording or not self.workflow_id:
            return
        
        # For now, we'll track special keys and shortcuts
        # Full keyboard logging would be privacy-invasive
        
        # Track special keys: Enter, Tab, Escape, etc.
        special_keys = [
            keyboard.Key.enter,
            keyboard.Key.tab,
            keyboard.Key.esc,
            keyboard.Key.backspace,
            keyboard.Key.delete
        ]
        
        if key in special_keys:
            current_time = time.time()
            if current_time - self.last_action_time < self.min_action_interval:
                return
            
            self.last_action_time = current_time
            
            screenshot_before = self.last_screenshot
            time.sleep(0.1)
            screenshot_after = self._capture_screenshot()
            
            key_name = str(key).replace('Key.', '')
            
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
    
    def _flush_buffer(self):
        """Process any buffered actions."""
        # For future use if we buffer actions for batch processing
        pass
    
    def add_annotation(self, text: str):
        """
        Add a manual annotation/comment to the recording.
        Useful for marking important moments or parameters.
        """
        if not self.is_recording:
            print("⚠️  Not currently recording.")
            return
        
        action_data = {
            'annotation': text,
            'timestamp': time.time()
        }
        
        self.memory.add_step(
            workflow_id=self.workflow_id,
            action_type='annotation',
            action_data=action_data,
            visual_context={'description': f"Annotation: {text}"}
        )
        
        print(f"📝 Annotation added: {text}")
    
    def _analyze_with_vlm(self) -> str:
        """Use Gemini VLM to understand workflow intention from screenshots"""
        import os
        from google import genai
        from google.genai.types import GenerateContentConfig
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Workflow recording"
        
        client = genai.Client(api_key=api_key)
        workflow_dir = self.memory.storage_dir / self.workflow_id / "steps"
        
        # Get first and last screenshots
        screenshots = sorted(workflow_dir.glob("*_after.png"))
        if not screenshots:
            return "Workflow recording"
        
        first_screenshot = screenshots[0]
        last_screenshot = screenshots[-1]
        
        # Load images
        from PIL import Image
        img1 = Image.open(first_screenshot)
        img2 = Image.open(last_screenshot)
        
        # Convert to base64
        import base64
        from io import BytesIO
        
        def img_to_base64(img):
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        
        img1_b64 = img_to_base64(img1)
        img2_b64 = img_to_base64(img2)
        
        # Ask Gemini
        prompt = f"""Analyze these before/after screenshots of a user workflow.

First screenshot: Start of workflow
Last screenshot: End of workflow

Based on what changed, what was the user trying to accomplish? 

Respond with ONE concise sentence (max 8 words) describing the goal.

Examples:
- "Download assignment from Canvas"
- "Search GitHub for React code"
- "Open Twitter and view feed"
- "Navigate to project settings"

Be specific but brief."""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {"role": "user", "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": img1_b64}},
                        {"inline_data": {"mime_type": "image/png", "data": img2_b64}}
                    ]}
                ],
                config=GenerateContentConfig(temperature=0.3, max_output_tokens=30)
            )
            
            intention = response.text.strip().replace('"', '').replace("'", "")
            return intention[:100]
        except:
            return "Workflow recording"


def interactive_recording_demo():
    """
    Interactive demo of the recording system.
    """
    print("=" * 70)
    print("AgentFlow - Learn by Observation Demo")
    print("=" * 70)
    print()
    print("This will record your actions for 15 seconds.")
    print("Try clicking around, scrolling, etc.")
    print()
    
    input("Press Enter when ready to start recording...")
    
    recorder = WorkflowRecorder()
    
    # Start recording
    workflow_id = recorder.start_recording(
        workflow_name="Test Workflow",
        description="Testing the recording system",
        tags=["test", "demo"]
    )
    
    # Record for 15 seconds
    time.sleep(15)
    
    # Stop recording
    recorder.stop_recording()
    
    # Show what was recorded
    print("\n" + "=" * 70)
    print("RECORDED WORKFLOW")
    print("=" * 70)
    
    workflow = recorder.memory.get_workflow(workflow_id)
    print(f"\nName: {workflow['name']}")
    print(f"Steps: {len(workflow['steps'])}")
    print("\nAction sequence:")
    for step in workflow['steps']:
        action_type = step['action_type']
        action_data = step['action_data']
        
        if action_type == 'click':
            print(f"  {step['step_number']}. Click at ({action_data['x']}, {action_data['y']})")
        elif action_type == 'scroll':
            print(f"  {step['step_number']}. Scroll {action_data['direction']}")
        elif action_type == 'key_press':
            print(f"  {step['step_number']}. Press {action_data['key']}")
    
    print("\n✅ Recording demo complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        interactive_recording_demo()
    else:
        print("Usage:")
        print("  python recorder.py demo          # Run interactive demo")
        print()
        print("Or import and use programmatically:")
        print("  from recorder import WorkflowRecorder")
        print("  recorder = WorkflowRecorder()")
        print("  recorder.start_recording('My Workflow')")
        print("  # ... user performs actions ...")
        print("  recorder.stop_recording()")
    
def usage():
    """Print usage information"""
    print()
    print("=" * 70)
    print("Workflow Recorder")
    print("=" * 70)
    print()
    print("Usage:")
    print("  python recorder.py demo          # Run interactive demo")
    print()
    print("Or import and use programmatically:")
    print("  from recorder import WorkflowRecorder")
    print("  recorder = WorkflowRecorder()")
    print("  recorder.start_recording('My Workflow')")
    print("  # ... user performs actions ...")
    print("  recorder.stop_recording()")


