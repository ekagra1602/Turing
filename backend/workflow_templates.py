"""
Hardcoded Workflow Templates

Pre-defined workflows for common tasks that Gemini can use immediately
without requiring prior recording. These are fully executable semantic action sequences.

Format: Each template is a dict mapping intention -> semantic_actions list
"""

from typing import Dict, List


# =============================================================================
# WORKFLOW TEMPLATES
# =============================================================================

WORKFLOW_TEMPLATES: Dict[str, List[Dict]] = {
    
    # =========================================================================
    # EMAIL WORKFLOWS
    # =========================================================================
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
            "target": "recorded_workflow_workflow_1761495396_1761495424_parameterized.json",  # <<< UPDATE THIS with your actual filename
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
            }
        }
    ],


    "send email via gmail": [
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
            "description": "Type gmail.com in address bar",
            "target": "address bar",
            "value": "gmail.com",
            "timestamp_seconds": 3.5,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 6,
            "semantic_type": "navigate",
            "description": "Press Enter to navigate to Gmail",
            "target": "gmail.com",
            "value": "gmail.com",
            "timestamp_seconds": 4.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 7,
            "semantic_type": "wait",
            "description": "Wait for Gmail to load",
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
            "description": "Use recorded workflow for Gmail compose (parameterized)",
            "target": "recorded_workflow_send_gmail_email_1761493414_parameterized.json",
            "value": None,
            "timestamp_seconds": 7.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "recorded_workflow_file",
            "parameter_mappings": {
                "RECIPIENT_EMAIL": "recipient_email",
                "SUBJECT": "email_subject", 
                "BODY": "email_body"
            }
        }
    ],
    
    # =========================================================================
    # BROWSER NAVIGATION WORKFLOWS
    # =========================================================================
    
    "open browser and navigate to url": [
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
            "description": "Wait for browser to open",
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
            "description": "Open new tab",
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
            "description": "Focus address bar",
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
            "description": "Type URL in address bar",
            "target": "address bar",
            "value": "{url}",
            "timestamp_seconds": 3.5,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "url"
        },
        {
            "step_number": 6,
            "semantic_type": "navigate",
            "description": "Press Enter to navigate",
            "target": "address bar",
            "value": "{url}",
            "timestamp_seconds": 4.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "url"
        },
        {
            "step_number": 7,
            "semantic_type": "wait",
            "description": "Wait for page to load",
            "target": None,
            "value": "2.0",
            "timestamp_seconds": 6.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ],
    
    "search on google": [
        {
            "step_number": 1,
            "semantic_type": "keyboard_shortcut",
            "description": "Focus address bar with Cmd+L",
            "target": None,
            "value": "cmd+l",
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 2,
            "semantic_type": "type_text",
            "description": "Type search query",
            "target": "address bar",
            "value": "{search_query}",
            "timestamp_seconds": 0.5,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "search_query"
        },
        {
            "step_number": 3,
            "semantic_type": "navigate",
            "description": "Press Enter to search",
            "target": "address bar",
            "value": "{search_query}",
            "timestamp_seconds": 1.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "search_query"
        },
        {
            "step_number": 4,
            "semantic_type": "wait",
            "description": "Wait for search results",
            "target": None,
            "value": "2.0",
            "timestamp_seconds": 3.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ],
    
    # =========================================================================
    # APPLICATION WORKFLOWS  
    # =========================================================================
    
    "open application": [
        {
            "step_number": 1,
            "semantic_type": "open_application",
            "description": "Open application using Raycast",
            "target": "{app_name}",
            "value": None,
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "app_name"
        },
        {
            "step_number": 2,
            "semantic_type": "wait",
            "description": "Wait for application to open",
            "target": None,
            "value": "2.0",
            "timestamp_seconds": 2.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ],
    
    # =========================================================================
    # TEXT SEARCH WORKFLOWS
    # =========================================================================
    
    "find text on page": [
        {
            "step_number": 1,
            "semantic_type": "keyboard_shortcut",
            "description": "Open find with Cmd+F",
            "target": None,
            "value": "cmd+f",
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 2,
            "semantic_type": "type_text",
            "description": "Type search term",
            "target": "find box",
            "value": "{search_term}",
            "timestamp_seconds": 0.5,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "search_term"
        },
        {
            "step_number": 3,
            "semantic_type": "navigate",
            "description": "Press Enter to find",
            "target": "find box",
            "value": "{search_term}",
            "timestamp_seconds": 1.0,
            "confidence": 1.0,
            "is_parameterizable": True,
            "parameter_name": "search_term"
        }
    ],
    
    # =========================================================================
    # TAB MANAGEMENT WORKFLOWS
    # =========================================================================
    
    "open new tab": [
        {
            "step_number": 1,
            "semantic_type": "keyboard_shortcut",
            "description": "Open new tab with Cmd+T",
            "target": None,
            "value": "cmd+t",
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 2,
            "semantic_type": "keyboard_shortcut",
            "description": "Focus address bar with Cmd+L",
            "target": None,
            "value": "cmd+l",
            "timestamp_seconds": 0.5,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ],
    
    "close current tab": [
        {
            "step_number": 1,
            "semantic_type": "keyboard_shortcut",
            "description": "Close tab with Cmd+W",
            "target": None,
            "value": "cmd+w",
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ],
    
    "refresh page": [
        {
            "step_number": 1,
            "semantic_type": "keyboard_shortcut",
            "description": "Refresh page with Cmd+R",
            "target": None,
            "value": "cmd+r",
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        {
            "step_number": 2,
            "semantic_type": "wait",
            "description": "Wait for page to reload",
            "target": None,
            "value": "2.0",
            "timestamp_seconds": 2.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        }
    ]
}


def get_all_templates() -> Dict[str, List[Dict]]:
    """
    Get all hardcoded workflow templates
    
    Returns:
        Dict mapping workflow intention to semantic actions list
    """
    return WORKFLOW_TEMPLATES.copy()


def get_template(intention: str) -> List[Dict]:
    """
    Get a specific workflow template by intention
    
    Args:
        intention: The workflow intention (e.g., "send email via gmail")
    
    Returns:
        List of semantic actions, or empty list if not found
    """
    return WORKFLOW_TEMPLATES.get(intention.lower(), [])


def list_available_templates() -> List[str]:
    """
    List all available template intentions
    
    Returns:
        List of intention strings
    """
    return list(WORKFLOW_TEMPLATES.keys())


def merge_templates_with_learned(learned_workflows: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Merge hardcoded templates with learned workflows
    Learned workflows take precedence if there are conflicts
    
    Args:
        learned_workflows: Dict of learned workflows from memory
    
    Returns:
        Merged dictionary with all workflows
    """
    merged = WORKFLOW_TEMPLATES.copy()
    merged.update(learned_workflows)  # Learned workflows override templates
    return merged

