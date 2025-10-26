#!/usr/bin/env python3
"""
Parameterize Workday Hours Entry Workflow
Extracts structure and adds parameter placeholders for hours entry
"""

import json
import sys
import os

def parameterize_workday_workflow(workflow_file: str):
    """
    Create a parameterized version of Workday hours entry workflow
    
    Expected parameters:
    - HOURS (e.g., "8", "6.5")
    - DATE (optional, e.g., "Monday", "10/26")
    - PROJECT_CODE (optional, e.g., "PROJ-123")
    - NOTES (optional)
    """
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    print(f"Original workflow: {len(workflow['actions'])} actions")
    print()
    print("Analyzing workflow structure...")
    print()
    
    structural_actions = []
    typing_sequence = []
    last_action_type = None
    parameter_count = 0
    
    for i, action in enumerate(workflow['actions']):
        action_type = action['type']
        
        # Keep clicks
        if action_type == 'click':
            # If we were collecting typing, flush it as a parameter
            if typing_sequence:
                parameter_count += 1
                param_name = _guess_parameter_name(parameter_count, typing_sequence)
                structural_actions.append({
                    'type': 'type_parameter',
                    'placeholder': param_name,
                    'delay': 0.1
                })
                print(f"✓ Parameter #{parameter_count}: {{{param_name}}} = '{''.join(typing_sequence)}'")
                typing_sequence = []
            
            structural_actions.append(action)
            print(f"✓ Keep: Click at ({action['x']}, {action['y']})")
            last_action_type = 'click'
        
        # Keep navigation keys
        elif action_type == 'key':
            key = action['key']
            if key in ['enter', 'tab', 'space', 'escape']:
                # Flush typing sequence as parameter
                if typing_sequence:
                    parameter_count += 1
                    param_name = _guess_parameter_name(parameter_count, typing_sequence)
                    structural_actions.append({
                        'type': 'type_parameter',
                        'placeholder': param_name,
                        'delay': 0.1
                    })
                    print(f"✓ Parameter #{parameter_count}: {{{param_name}}} = '{''.join(typing_sequence)}'")
                    typing_sequence = []
                
                structural_actions.append(action)
                print(f"✓ Keep: Press {key}")
                last_action_type = 'key'
        
        # Collect typing characters
        elif action_type == 'type':
            typing_sequence.append(action['text'])
            last_action_type = 'type'
    
    # Flush any remaining typing
    if typing_sequence:
        parameter_count += 1
        param_name = _guess_parameter_name(parameter_count, typing_sequence)
        structural_actions.append({
            'type': 'type_parameter',
            'placeholder': param_name,
            'delay': 0.1
        })
        print(f"✓ Parameter #{parameter_count}: {{{param_name}}} = '{''.join(typing_sequence)}'")
    
    # Create parameterized workflow
    new_workflow = workflow.copy()
    new_workflow['actions'] = structural_actions
    new_workflow['name'] = workflow['name'] + ' (parameterized)'
    new_workflow['parameterized'] = True
    new_workflow['parameters'] = _generate_parameter_list(parameter_count)
    
    # Save
    output_file = workflow_file.replace('.json', '_parameterized.json')
    with open(output_file, 'w') as f:
        json.dump(new_workflow, f, indent=2)
    
    print()
    print(f"✅ Created parameterized workflow: {output_file}")
    print(f"   Original: {len(workflow['actions'])} actions")
    print(f"   Structural: {len(structural_actions)} actions")
    print(f"   Parameters: {parameter_count}")
    print()
    print("Detected parameters:")
    for param in new_workflow['parameters']:
        print(f"  - {param}")
    print()
    print("⚠️  IMPORTANT: Review the parameterized workflow and rename")
    print("   parameters to match your use case (HOURS, DATE, PROJECT_CODE, etc.)")
    print()
    print(f"Edit: {output_file}")
    print()
    
    return output_file

def _guess_parameter_name(param_number: int, typing_sequence: list) -> str:
    """Guess a reasonable parameter name based on typed content"""
    text = ''.join(typing_sequence).lower()
    
    # Check for common patterns
    if text.replace('.', '').replace(':', '').isdigit() or text in ['8', '7.5', '6', '4']:
        return 'HOURS'
    elif 'proj' in text or text.isupper() or '-' in text:
        return 'PROJECT_CODE'
    elif any(day in text for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
        return 'DATE'
    elif '/' in text or '-' in text:
        return 'DATE'
    elif len(text) > 20:
        return 'NOTES'
    else:
        return f'PARAM_{param_number}'

def _generate_parameter_list(param_count: int) -> list:
    """Generate parameter list"""
    # Common Workday parameters
    common_params = ['hours', 'date', 'project_code', 'task', 'notes']
    
    params = []
    for i in range(min(param_count, len(common_params))):
        params.append(common_params[i])
    
    # Add generic params for extras
    for i in range(len(params), param_count):
        params.append(f'param_{i+1}')
    
    return params

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parameterize_workday.py <recorded_workflow.json>")
        print()
        print("This will create a parameterized version suitable for Workday hours entry.")
        print()
        # List available recorded workflows
        workflows_dir = os.path.join(os.path.dirname(__file__), 'workflows')
        if os.path.exists(workflows_dir):
            workday_workflows = [f for f in os.listdir(workflows_dir) 
                                 if 'workday' in f.lower() and f.endswith('.json') 
                                 and 'parameterized' not in f]
            if workday_workflows:
                print("Available Workday recordings:")
                for wf in workday_workflows:
                    print(f"  - {wf}")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    
    # Handle relative paths
    if not os.path.isabs(workflow_file) and not os.path.exists(workflow_file):
        workflows_dir = os.path.join(os.path.dirname(__file__), 'workflows')
        workflow_file = os.path.join(workflows_dir, workflow_file)
    
    if not os.path.exists(workflow_file):
        print(f"❌ Workflow file not found: {workflow_file}")
        sys.exit(1)
    
    output = parameterize_workday_workflow(workflow_file)
    
    print("✅ Next steps:")
    print("1. Review and edit parameter names in the JSON file")
    print("2. Add the workflow template to workflow_templates.py")
    print("3. Test it!")

