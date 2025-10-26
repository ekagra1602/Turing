#!/usr/bin/env python3
"""
Extract structural actions (clicks, tabs, navigation) from a recorded workflow
Removes character-by-character typing so the executor can inject parameters
"""

import json
import sys

def extract_structure(workflow_file: str, output_file: str = None):
    """
    Extract structural actions from a recorded workflow
    
    Keeps:
    - Clicks
    - Tab/Enter keypresses (navigation)
    - Special keys
    
    Removes:
    - Character typing (letters, numbers, symbols)
    
    Adds placeholders for:
    - {RECIPIENT_EMAIL}
    - {SUBJECT}
    - {BODY}
    """
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    print(f"Original workflow: {len(workflow['actions'])} actions")
    print()
    
    structural_actions = []
    skip_mode = False
    last_action_type = None
    
    for i, action in enumerate(workflow['actions']):
        action_type = action['type']
        
        # Always keep clicks
        if action_type == 'click':
            structural_actions.append(action)
            print(f"✓ Keep: Click at ({action['x']}, {action['y']})")
            last_action_type = 'click'
        
        # Keep navigation keys (enter, tab)
        elif action_type == 'key':
            key = action['key']
            if key in ['enter', 'tab', 'space', 'escape']:
                # Add placeholder before enter/tab if we just removed typing
                if last_action_type == 'type_removed':
                    if key == 'enter' and not any(a.get('placeholder') == 'RECIPIENT_EMAIL' for a in structural_actions):
                        # This is after typing recipient email
                        structural_actions.append({
                            'type': 'type_parameter',
                            'placeholder': 'RECIPIENT_EMAIL',
                            'delay': 0.1
                        })
                        print(f"✓ Add: {{RECIPIENT_EMAIL}} placeholder")
                    elif key == 'tab':
                        # Check what field we're in
                        if not any(a.get('placeholder') == 'SUBJECT' for a in structural_actions):
                            structural_actions.append({
                                'type': 'type_parameter',
                                'placeholder': 'SUBJECT',
                                'delay': 0.1
                            })
                            print(f"✓ Add: {{SUBJECT}} placeholder")
                        elif not any(a.get('placeholder') == 'BODY' for a in structural_actions):
                            structural_actions.append({
                                'type': 'type_parameter',
                                'placeholder': 'BODY',
                                'delay': 0.1
                            })
                            print(f"✓ Add: {{BODY}} placeholder")
                
                structural_actions.append(action)
                print(f"✓ Keep: Press {key}")
                last_action_type = 'key'
        
        # Remove character typing (but track it)
        elif action_type == 'type':
            if last_action_type != 'type_removed':
                print(f"✗ Remove: Character typing (will use parameter)")
            last_action_type = 'type_removed'
    
    # Create new workflow
    new_workflow = workflow.copy()
    new_workflow['actions'] = structural_actions
    new_workflow['name'] = workflow['name'] + ' (parameterized)'
    new_workflow['parameterized'] = True
    new_workflow['parameters'] = ['recipient_email', 'email_subject', 'email_body']
    
    # Save
    if not output_file:
        output_file = workflow_file.replace('.json', '_parameterized.json')
    
    with open(output_file, 'w') as f:
        json.dump(new_workflow, f, indent=2)
    
    print()
    print(f"✅ Created parameterized workflow: {output_file}")
    print(f"   Original: {len(workflow['actions'])} actions")
    print(f"   Structural: {len(structural_actions)} actions")
    print()
    print("This workflow now has placeholders for:")
    print("  - {RECIPIENT_EMAIL}")
    print("  - {SUBJECT}")
    print("  - {BODY}")
    print()
    print("The executor will inject actual values at runtime.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_structure.py <recorded_workflow.json> [output.json]")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    extract_structure(workflow_file, output_file)

