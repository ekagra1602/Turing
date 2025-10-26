# Workflow Templates - Quick Start

## What Are Workflow Templates?

Hardcoded, pre-built workflows that Gemini can use immediately without recording. Think of them as "recipes" for common computer tasks.

## Available Templates (8 total)

| Template | Parameters | Steps |
|----------|-----------|-------|
| **send email via gmail** | recipient_email, email_subject, email_body | 15 |
| **open browser and navigate to url** | url | 7 |
| **search on google** | search_query | 4 |
| **open application** | app_name | 2 |
| **find text on page** | search_term | 3 |
| **open new tab** | - | 2 |
| **close current tab** | - | 1 |
| **refresh page** | - | 2 |

## Quick Usage

### 1. Templates Load Automatically

```python
from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

# Templates automatically included!
executor = GeminiWorkflowExecutor(memory=VisualWorkflowMemory())

# Check what's loaded
print(f"Total workflows: {len(executor.workflows_by_intention)}")
```

### 2. Use a Template

```python
# Get template actions
actions = executor.get_workflow_by_intention("send email via gmail")

# Execute with parameters
executor.execute_workflow(
    workflow={'semantic_actions': actions},
    parameters={
        'recipient_email': 'user@example.com',
        'email_subject': 'Test Email',
        'email_body': 'This is a test.'
    }
)
```

### 3. List Available Templates

```python
from workflow_templates import list_available_templates

templates = list_available_templates()
for template in templates:
    print(f"• {template}")
```

## File Structure

```
backend/
├── workflow_templates.py          # Template definitions
├── gemini_workflow_executor.py    # Auto-loads templates
├── test_workflow_templates.py     # Test suite
└── WORKFLOW_TEMPLATES_QUICK_START.md  # This file

docs/
└── WORKFLOW_TEMPLATES.md          # Full documentation
```

## Testing

```bash
cd backend
python test_workflow_templates.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Total Templates: 8
```

## Adding a New Template

1. Open `workflow_templates.py`
2. Add to `WORKFLOW_TEMPLATES` dict:

```python
"your workflow name": [
    {
        "step_number": 1,
        "semantic_type": "keyboard_shortcut",  # or click_element, type_text, etc.
        "description": "What this step does",
        "target": "What to interact with",
        "value": "{parameter_name}",  # For parameterizable steps
        "timestamp_seconds": 0.0,
        "confidence": 1.0,
        "is_parameterizable": True,
        "parameter_name": "parameter_name"
    },
    # ... more steps ...
]
```

3. Run tests: `python test_workflow_templates.py`

## Template Format Cheat Sheet

### Semantic Types

- `open_application` - Launch app via Raycast
- `click_element` - Click UI element
- `type_text` - Type into field
- `keyboard_shortcut` - Press keyboard shortcut (e.g., "cmd+t")
- `navigate` - Navigate to URL (press Enter)
- `scroll` - Scroll page
- `wait` - Wait for duration

### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `step_number` | ✅ | int | Sequential step number |
| `semantic_type` | ✅ | str | Type of action |
| `description` | ✅ | str | Human-readable description |
| `target` | ⚠️ | str | What to interact with |
| `value` | ⚠️ | str | Text/duration/shortcut value |
| `timestamp_seconds` | ✅ | float | Relative timestamp |
| `confidence` | ✅ | float | 0.0-1.0 confidence score |
| `is_parameterizable` | ✅ | bool | Can be parameterized? |
| `parameter_name` | ⚠️ | str | Parameter name if applicable |

⚠️ = Required for specific semantic types

## Common Keyboard Shortcuts

```python
"cmd+t"      # New tab
"cmd+l"      # Focus address bar
"cmd+w"      # Close tab
"cmd+r"      # Refresh
"cmd+f"      # Find
"cmd+shift+t"  # Reopen closed tab
"option+space" # Raycast launcher
```

## Priority System

When the same workflow exists as both a template and learned workflow:

```
Learned Workflow > Hardcoded Template
```

This lets users override generic templates with their own optimized versions.

## Examples

### Send Email

```python
executor.execute_workflow(
    workflow={'semantic_actions': executor.get_workflow_by_intention("send email via gmail")},
    parameters={
        'recipient_email': 'boss@company.com',
        'email_subject': 'Weekly Report',
        'email_body': 'Completed all tasks this week.'
    }
)
```

### Open Application

```python
executor.execute_workflow(
    workflow={'semantic_actions': executor.get_workflow_by_intention("open application")},
    parameters={'app_name': 'Slack'}
)
```

### Google Search

```python
executor.execute_workflow(
    workflow={'semantic_actions': executor.get_workflow_by_intention("search on google")},
    parameters={'search_query': 'best Python tutorials'}
)
```

## Troubleshooting

**Q: Template not found?**
```python
# Check exact name
from workflow_templates import list_available_templates
print(list_available_templates())
```

**Q: Parameters not working?**
```python
# Check parameter names in template
from workflow_templates import get_template
template = get_template("send email via gmail")
params = [s['parameter_name'] for s in template if s.get('is_parameterizable')]
print(params)  # ['recipient_email', 'email_subject', 'email_body']
```

**Q: How to see template details?**
```python
from workflow_templates import get_template
template = get_template("send email via gmail")
for step in template:
    print(f"{step['step_number']}. {step['description']}")
```

## Next Steps

- 📚 Read full docs: `docs/WORKFLOW_TEMPLATES.md`
- 🧪 Run tests: `python test_workflow_templates.py`
- ➕ Add your own templates to `workflow_templates.py`
- 🎯 Use templates in your workflows!

