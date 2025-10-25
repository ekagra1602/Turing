"""
Recording Post-Processor
Processes recorded video + events to generate actionable workflows
"""

import cv2
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import numpy as np
from PIL import Image

from visual_analyzer import VisualAnalyzer
from visual_memory import VisualWorkflowMemory


@dataclass
class ProcessedAction:
    """A processed action with visual analysis"""
    step_number: int
    timestamp: float
    event_type: str
    event_data: Dict[str, Any]
    
    # Visual analysis
    screenshot_before: Optional[Image.Image]
    screenshot_after: Optional[Image.Image]
    clicked_text: Optional[str] = None
    clicked_element_type: Optional[str] = None
    nearby_elements: Optional[List[str]] = None
    ui_changed: bool = False
    
    # Semantic understanding
    action_description: Optional[str] = None
    verification: Optional[str] = None
    wait_condition: Optional[str] = None
    
    def to_dict(self):
        result = asdict(self)
        # Remove Image objects (too large for JSON)
        result.pop('screenshot_before', None)
        result.pop('screenshot_after', None)
        return result


class RecordingProcessor:
    """
    Process recorded workflows into actionable automation scripts.
    
    This is where the magic happens:
    1. Load video and events
    2. Extract frames at action timestamps  
    3. Run OCR/Vision analysis
    4. Understand what each action accomplished
    5. Generate finite automata-style action log
    """
    
    def __init__(self):
        self.analyzer = VisualAnalyzer(use_easyocr=True)
        self.memory = VisualWorkflowMemory()
        
        # Timing configuration
        self.before_offset = 0.05  # 50ms before action
        self.after_offset = 0.20   # 200ms after action
        
        print("✅ Recording Processor initialized")
    
    def process_recording(self,
                         recording_id: str,
                         show_progress: bool = True) -> str:
        """
        Process a recording into a workflow.
        
        Args:
            recording_id: ID of recording to process
            show_progress: Print progress updates
        
        Returns:
            workflow_id: ID of created workflow
        """
        if show_progress:
            print("\n" + "=" * 70)
            print("📹 PROCESSING RECORDING")
            print("=" * 70)
        
        # Load recording
        recording_path = Path("backend/recordings") / recording_id
        
        if not recording_path.exists():
            raise ValueError(f"Recording {recording_id} not found at {recording_path}")
        
        # Load metadata
        with open(recording_path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Load events
        with open(recording_path / "events.json", 'r') as f:
            events_data = json.load(f)
        
        if show_progress:
            print(f"\n📋 Recording: {metadata['name']}")
            print(f"   Duration: {events_data['duration']:.1f}s")
            print(f"   Events: {events_data['event_count']}")
        
        # Load video
        video_path = str(recording_path / "screen_recording.mp4")
        video = cv2.VideoCapture(video_path)
        
        if not video.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        fps = video.get(cv2.CAP_PROP_FPS)
        
        if show_progress:
            print(f"   FPS: {fps}")
            print("\n🔍 Analyzing actions...")
        
        # Process each event
        processed_actions: List[ProcessedAction] = []
        
        for i, event in enumerate(events_data['events'], 1):
            if show_progress:
                print(f"\n  Step {i}/{len(events_data['events'])}: {event['event_type']}")
            
            processed = self._process_event(
                event=event,
                step_number=i,
                video=video,
                fps=fps,
                show_progress=show_progress
            )
            
            processed_actions.append(processed)
        
        video.release()
        
        # Save screenshots
        if show_progress:
            print("\n💾 Saving screenshots...")
        
        screenshots_dir = recording_path / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        
        for action in processed_actions:
            step_id = f"step_{action.step_number:03d}"
            
            if action.screenshot_before:
                before_path = screenshots_dir / f"{step_id}_before.png"
                action.screenshot_before.save(before_path)
            
            if action.screenshot_after:
                after_path = screenshots_dir / f"{step_id}_after.png"
                action.screenshot_after.save(after_path)
        
        # Generate action log
        if show_progress:
            print("\n📝 Generating action log...")
        
        action_log = self._generate_action_log(processed_actions)
        
        # Save action log (human-readable)
        action_log_path = recording_path / "action_log.txt"
        with open(action_log_path, 'w') as f:
            f.write(action_log)
        
        if show_progress:
            print("\n📄 Action Log:")
            print("=" * 70)
            print(action_log)
            print("=" * 70)
        
        # Create workflow in memory system
        if show_progress:
            print("\n💾 Creating workflow...")
        
        workflow_id = self._create_workflow(
            metadata=metadata,
            processed_actions=processed_actions,
            recording_path=recording_path
        )
        
        # Save processed data
        processed_data = {
            'recording_id': recording_id,
            'workflow_id': workflow_id,
            'actions': [action.to_dict() for action in processed_actions],
            'action_log': action_log
        }
        
        with open(recording_path / "processed.json", 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        if show_progress:
            print(f"\n✅ Processing complete!")
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Action log: {action_log_path}")
        
        return workflow_id
    
    def _process_event(self,
                      event: Dict,
                      step_number: int,
                      video: cv2.VideoCapture,
                      fps: float,
                      show_progress: bool) -> ProcessedAction:
        """Process a single event with visual analysis"""
        
        timestamp = event['timestamp']
        event_type = event['event_type']
        event_data = event['data']
        
        # Extract frames
        frame_before = self._extract_frame(video, timestamp - self.before_offset, fps)
        frame_after = self._extract_frame(video, timestamp + self.after_offset, fps)
        
        # Convert to PIL Images
        screenshot_before = None
        screenshot_after = None
        
        if frame_before is not None:
            screenshot_before = Image.fromarray(cv2.cvtColor(frame_before, cv2.COLOR_BGR2RGB))
        
        if frame_after is not None:
            screenshot_after = Image.fromarray(cv2.cvtColor(frame_after, cv2.COLOR_BGR2RGB))
        
        # Analyze action
        clicked_text = None
        clicked_element_type = None
        nearby_elements = None
        ui_changed = False
        
        if event_type == 'click' and screenshot_before:
            # Analyze what was clicked
            click_x = event_data['x']
            click_y = event_data['y']
            
            if show_progress:
                print(f"     Analyzing click at ({click_x}, {click_y})...")
            
            context = self.analyzer.analyze_click_context(
                screenshot=screenshot_before,
                click_x=click_x,
                click_y=click_y,
                radius=100
            )
            
            clicked_text = context.get('clicked_text')
            nearby_elements = [item['text'] for item in context.get('nearby_text', [])[:3]]
            
            # Classify element type
            if clicked_text:
                clicked_element_type = self._classify_element(clicked_text)
            
            if show_progress and clicked_text:
                print(f"     ✓ Found: '{clicked_text}' ({clicked_element_type})")
            
            # Check if UI changed
            if screenshot_after:
                ui_changed = self.analyzer.detect_ui_change(
                    screenshot_before,
                    screenshot_after,
                    threshold=5
                )
                
                if show_progress:
                    print(f"     UI changed: {ui_changed}")
        
        # Generate action description
        action_description = self._generate_action_description(
            event_type=event_type,
            event_data=event_data,
            clicked_text=clicked_text,
            clicked_element_type=clicked_element_type
        )
        
        # Determine verification and wait conditions
        verification, wait_condition = self._determine_verification(
            event_type=event_type,
            ui_changed=ui_changed,
            clicked_element_type=clicked_element_type,
            screenshot_after=screenshot_after
        )
        
        return ProcessedAction(
            step_number=step_number,
            timestamp=timestamp,
            event_type=event_type,
            event_data=event_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            clicked_text=clicked_text,
            clicked_element_type=clicked_element_type,
            nearby_elements=nearby_elements,
            ui_changed=ui_changed,
            action_description=action_description,
            verification=verification,
            wait_condition=wait_condition
        )
    
    def _extract_frame(self,
                      video: cv2.VideoCapture,
                      timestamp: float,
                      fps: float) -> Optional[np.ndarray]:
        """Extract frame at specific timestamp"""
        frame_number = int(timestamp * fps)
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = video.read()
        if ret:
            return frame
        return None
    
    def _classify_element(self, text: str) -> str:
        """Classify UI element type based on text"""
        text_lower = text.lower()
        
        # Common button words
        button_words = ['submit', 'cancel', 'ok', 'save', 'delete', 'add', 'remove', 
                       'edit', 'update', 'create', 'confirm', 'apply', 'close', 'done']
        
        if any(word in text_lower for word in button_words):
            return 'button'
        
        # Link indicators
        if 'http' in text_lower or 'www' in text_lower or '.com' in text_lower:
            return 'link'
        
        # Navigation/tab
        if len(text.split()) <= 2 and text[0].isupper():
            return 'navigation'
        
        return 'element'
    
    def _generate_action_description(self,
                                    event_type: str,
                                    event_data: Dict,
                                    clicked_text: Optional[str],
                                    clicked_element_type: Optional[str]) -> str:
        """Generate human-readable action description"""
        
        if event_type == 'click':
            if clicked_text:
                return f"Click on '{clicked_text}'"
            else:
                return f"Click at ({event_data['x']}, {event_data['y']})"
        
        elif event_type == 'type':
            text = event_data.get('text', '')
            return f"Type '{text}'"
        
        elif event_type == 'scroll':
            direction = event_data.get('direction', 'down')
            return f"Scroll {direction}"
        
        elif event_type == 'key_press':
            key = event_data.get('key', '')
            return f"Press {key.upper()}"
        
        return f"{event_type}"
    
    def _determine_verification(self,
                               event_type: str,
                               ui_changed: bool,
                               clicked_element_type: Optional[str],
                               screenshot_after: Optional[Image.Image]) -> Tuple[Optional[str], Optional[str]]:
        """Determine verification and wait conditions for action"""
        
        verification = None
        wait_condition = None
        
        if event_type == 'click':
            if ui_changed:
                if clicked_element_type == 'navigation' or clicked_element_type == 'link':
                    wait_condition = "wait for page to load"
                    verification = "page loaded successfully"
                elif clicked_element_type == 'button':
                    wait_condition = "wait for action to complete"
                else:
                    wait_condition = "wait for UI update"
            
            # Try to extract verification from after screenshot
            if screenshot_after and not verification:
                # Could use OCR here to detect success messages, page titles, etc.
                pass
        
        return verification, wait_condition
    
    def _generate_action_log(self, actions: List[ProcessedAction]) -> str:
        """Generate finite automata-style action log"""
        
        log_lines = []
        log_lines.append("WORKFLOW ACTION LOG")
        log_lines.append("=" * 70)
        log_lines.append("")
        
        for action in actions:
            step_line = f"{action.step_number}. {action.action_description}"
            
            # Add wait condition
            if action.wait_condition:
                step_line += f", {action.wait_condition}"
            
            # Add verification
            if action.verification:
                step_line += f" and ensure {action.verification}"
            
            log_lines.append(step_line)
        
        log_lines.append("")
        log_lines.append("=" * 70)
        
        return "\n".join(log_lines)
    
    def _create_workflow(self,
                        metadata: Dict,
                        processed_actions: List[ProcessedAction],
                        recording_path: Path) -> str:
        """Create workflow in memory system"""
        
        # Create workflow
        workflow_id = self.memory.create_workflow(
            name=metadata['name'],
            description=metadata.get('description', ''),
            tags=['recorded', 'video']
        )
        
        # Add each step
        for action in processed_actions:
            action_type = action.event_type
            action_data = action.event_data.copy()
            
            # Add normalized coordinates for clicks
            if action_type == 'click':
                # Assume 1920x1080 for normalization (can get from video)
                action_data['normalized_x'] = int((action_data['x'] / 1920) * 1000)
                action_data['normalized_y'] = int((action_data['y'] / 1080) * 1000)
            
            # Build visual context
            visual_context = {
                'clicked_text': action.clicked_text,
                'clicked_element_type': action.clicked_element_type,
                'nearby_elements': action.nearby_elements,
                'action_description': action.action_description,
                'verification': action.verification,
                'wait_condition': action.wait_condition
            }
            
            # Add step (screenshots already saved)
            self.memory.add_step(
                workflow_id=workflow_id,
                action_type=action_type,
                action_data=action_data,
                screenshot_before=action.screenshot_before,
                screenshot_after=action.screenshot_after,
                visual_context=visual_context
            )
        
        # Finalize workflow
        self.memory.finalize_workflow(workflow_id, parameters=[])
        
        return workflow_id


def test_processor():
    """Test the processor with a recording"""
    print("=" * 70)
    print("Recording Processor Test")
    print("=" * 70)
    print()
    
    # List available recordings
    recordings_dir = Path("backend/recordings")
    
    if not recordings_dir.exists():
        print("No recordings directory found!")
        return
    
    recordings = [d for d in recordings_dir.iterdir() if d.is_dir()]
    
    if not recordings:
        print("No recordings found!")
        print("Record a workflow first using recording_overlay.py")
        return
    
    print("Available recordings:")
    for i, rec in enumerate(recordings, 1):
        # Load metadata
        metadata_path = rec / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"  {i}. {metadata['name']} (ID: {rec.name})")
    
    print()
    choice = input("Select recording to process (number): ").strip()
    
    try:
        idx = int(choice) - 1
        recording_id = recordings[idx].name
    except (ValueError, IndexError):
        print("Invalid selection!")
        return
    
    # Process recording
    processor = RecordingProcessor()
    workflow_id = processor.process_recording(recording_id, show_progress=True)
    
    print(f"\n✅ Processing complete!")
    print(f"   Workflow ID: {workflow_id}")


if __name__ == "__main__":
    test_processor()

