"""
ADD THIS TO workflow_templates.py AFTER RECORDING YOUR WORKDAY WORKFLOW

Instructions:
1. Record your Workday workflow using: python simple_recorder.py
2. Parameterize it using: python parameterize_workday.py workflows/recorded_workflow_enter_workday_hours_XXXXX.json
3. Copy the snippet below and paste it into workflow_templates.py under the EMAIL WORKFLOWS section
4. Update the filename on line marked with # <<< UPDATE THIS
5. Test it!
"""

# =============================================================================
# ADD TO WORKFLOW_TEMPLATES dict in workflow_templates.py:
# =============================================================================

    "enter workday hours": [
        {
            "step_number": 1,
            "semantic_type": "open_application",
            "description": "Open Brave Browser",
            "target": "Brave Browser",
            "value": None,
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 2,
            "semantic_type": "wait",
            "description": "Wait for browser to fully open",
            "target": None,
            "value": "2.0",
            "timestamp_seconds": 2.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 3,
            "semantic_type": "keyboard_shortcut",
            "description": "Open new tab with Cmd+T",
            "target": None,
            "value": "cmd+t",
            "timestamp_seconds": 2.5,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 4,
            "semantic_type": "keyboard_shortcut",
            "description": "Focus address bar with Cmd+L",
            "target": None,
            "value": "cmd+l",
            "timestamp_seconds": 3.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 5,
            "semantic_type": "type_text",
            "description": "Type Workday URL in address bar",
            "target": "address bar",
            "value": "{workday_url}",
            "timestamp_seconds": 3.5,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "workday_url"
        },
        {
            "step_number": 6,
            "semantic_type": "navigate",
            "description": "Press Enter to navigate to Workday",
            "target": "{workday_url}",
            "value": "{workday_url}",
            "timestamp_seconds": 4.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "workday_url"
        },
        {
            "step_number": 7,
            "semantic_type": "wait",
            "description": "Wait for Workday to load",
            "target": None,
            "value": "3.0",
            "timestamp_seconds": 7.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 8,
            "semantic_type": "use_recorded_workflow",
            "description": "Use recorded workflow for Workday hours entry (parameterized)",
            "target": "recorded_workflow_enter_workday_hours_XXXXXX_parameterized.json",  # <<< UPDATE THIS with your actual filename
            "value": None,
            "timestamp_seconds": 7.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "recorded_workflow_file",
            "parameter_mappings": {
                # Map placeholders in your recorded workflow to template parameters
                # Update these based on what parameters you actually have
                "HOURS": "hours",
                "DATE": "date",
                "PROJECT_CODE": "project_code",
                "NOTES": "notes"
            }
        }
    ],

# =============================================================================
# EXAMPLE USAGE:
# =============================================================================

# Natural language examples that will match this workflow:
# - "enter 8 hours into workday for today"
# - "log 7.5 hours in workday for Monday with project ABC-123"
# - "add 6 hours to workday timesheet"
# - "submit workday hours: 8 hours, project XYZ-456"

# The system will extract:
# - hours (e.g., "8", "7.5", "6")
# - date (e.g., "today", "Monday", "10/26")
# - project_code (e.g., "ABC-123", "XYZ-456")
# - notes (any additional text)

# =============================================================================
# TESTING:
# =============================================================================

# After adding to workflow_templates.py, test with:
# python workflow_cli.py execute "enter 8 hours into workday" --auto
# python workflow_cli.py execute "log 6.5 hours in workday for project ABC-123" --auto

# =============================================================================

