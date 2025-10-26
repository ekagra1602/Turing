#!/usr/bin/env python3
"""
Simple Workflow Player
Plays back recorded coordinates and keystrokes with exact precision
"""

import json
import time
import pyautogui
import sys
import os
from typing import Dict, Any


class SimplePlayer:
    """Plays back recorded workflows"""
    
    def __init__(self, workflow_file: str):
        self.workflow_file = workflow_file
        self.workflow = None
        
        # Load workflow
        with open(workflow_file, 'r') as f:
            self.workflow = json.load(f)
        
        print("=" * 70)
        print("▶️  SIMPLE WORKFLOW PLAYER")
        print("=" * 70)
        print()
        print(f"Workflow: {self.workflow['name']}")
        if self.workflow.get('description'):
            print(f"Description: {self.workflow['description']}")
        print(f"Actions: {len(self.workflow['actions'])}")
        print(f"Duration: ~{self.workflow['duration']:.1f}s")
        print()
        
        # Check screen resolution
        current_size = pyautogui.size()
        recorded_size = self.workflow.get('screen_resolution', {})
        
        if recorded_size:
            if (current_size.width != recorded_size['width'] or 
                current_size.height != recorded_size['height']):
                print("⚠️  WARNING: Screen resolution changed!")
                print(f"   Recorded: {recorded_size['width']}x{recorded_size['height']}")
                print(f"   Current:  {current_size.width}x{current_size.height}")
                print("   Coordinates may not be accurate!")
                print()
    
    def play(self, dry_run: bool = False):
        """Play the workflow"""
        if dry_run:
            print("🔍 DRY RUN MODE - No actual clicks/typing")
            print()
        
        print("=" * 70)
        print("🎬 STARTING PLAYBACK")
        print("=" * 70)
        print("You have 3 seconds to focus the correct window...")
        print()
        
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print("\n▶️  Playing workflow...\n")
        
        for i, action in enumerate(self.workflow['actions'], 1):
            # Wait for delay
            if action.get('delay', 0) > 0:
                time.sleep(action['delay'])
            
            # Execute action
            action_type = action['type']
            
            if action_type == 'click':
                x, y = action['x'], action['y']
                print(f"  [{i}/{len(self.workflow['actions'])}] 🖱️  Click at ({x}, {y})")
                if not dry_run:
                    pyautogui.click(x, y)
            
            elif action_type == 'type':
                text = action['text']
                print(f"  [{i}/{len(self.workflow['actions'])}] ⌨️  Type: '{text}'")
                if not dry_run:
                    pyautogui.write(text, interval=0.05)
            
            elif action_type == 'key':
                key = action['key']
                print(f"  [{i}/{len(self.workflow['actions'])}] ⌨️  Press: {key}")
                if not dry_run:
                    if key == 'enter':
                        pyautogui.press('enter')
                    elif key == 'tab':
                        pyautogui.press('tab')
                    elif key == 'space':
                        pyautogui.press('space')
        
        print()
        print("=" * 70)
        print("✅ PLAYBACK COMPLETE")
        print("=" * 70)
        print()
    
    def show_info(self):
        """Show workflow information"""
        print("\nWorkflow Details:")
        print("-" * 70)
        print(json.dumps(self.workflow, indent=2))
        print("-" * 70)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python simple_player.py <workflow_file.json> [--dry-run]")
        print()
        print("Available workflows:")
        workflows_dir = os.path.join(os.path.dirname(__file__), "workflows")
        if os.path.exists(workflows_dir):
            for f in os.listdir(workflows_dir):
                if f.endswith('.json') and 'recorded_workflow' in f:
                    print(f"  - {f}")
        else:
            print("  (No workflows recorded yet)")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    try:
        player = SimplePlayer(workflow_file)
        
        if '--info' in sys.argv:
            player.show_info()
        else:
            player.play(dry_run=dry_run)
    
    except FileNotFoundError:
        print(f"❌ Error: Workflow file not found: {workflow_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

