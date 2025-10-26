# Workflow Templates System

## Overview

The Workflow Templates system provides **hardcoded, pre-defined workflows** that Gemini can use immediately without requiring prior recording. These templates represent common computer tasks (like sending emails, opening browsers, etc.) in a format that the Gemini Workflow Executor can directly execute.

## Architecture

### Components

1. **`workflow_templates.py`**: Contains all hardcoded template definitions
2. **`GeminiWorkflowExecutor`**: Automatically loads and merges templates with learned workflows
3. **Semantic Action Format**: Standardized structure for all workflow steps

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│         Workflow Templates (workflow_templates.py)      │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Hardcoded Templates                               │  │
│  │ • send email via gmail                            │  │
│  │ • open browser and navigate to url               │  │
│  │ • search on google                                │  │
│  │ • etc...                                          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│       GeminiWorkflowExecutor._load_all_workflows()      │
│                                                           │
│  1. Load learned workflows from memory                   │
│  2. Merge with hardcoded templates                       │
│  3. Learned workflows override templates if conflict     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               GeminiComputerUse System Prompt            │
│                                                           │
│  All workflows (templates + learned) are included        │
│  in the system prompt for Gemini to reference            │
└─────────────────────────────────────────────────────────┘
```

## Semantic Action Format

Each workflow template is a list of semantic actions with this structure:

```python
{
    "step_number": 1,                          # Sequential step number
    "semantic_type": "open_application",       # Type of action
    "description": "Open Brave Browser",       # Human-readable description
    "target": "Brave Browser",                 # What to interact with
    "value": None,                             # Value for type/wait actions
    "timestamp_seconds": 0.0,                  # Relative timestamp
    "confidence": 1.0,                         # Confidence score (0.0-1.0)
    "is_parameterizable": False,               # Can this be parameterized?
    "parameter_name": None                     # Parameter name if applicable
}
```

### Semantic Types

- **`open_application`**: Launch an application using Raycast/Spotlight
- **`click_element`**: Click on a UI element by description
- **`type_text`**: Type text into a field
- **`keyboard_shortcut`**: Execute a keyboard shortcut (e.g., "cmd+t")
- **`navigate`**: Navigate to URL (press Enter in address bar)
- **`scroll`**: Scroll up/down on page
- **`wait`**: Wait for specified duration

## Available Templates

### 1. Send Email via Gmail

**Intention**: `"send email via gmail"`

**Steps**: 15 steps

**Parameters**:
- `recipient_email`: Email address of recipient
- `email_subject`: Subject line
- `email_body`: Email message content

**Workflow**:
1. Open Brave Browser
2. Open new tab (Cmd+T)
3. Focus address bar (Cmd+L)
4. Navigate to gmail.com
5. Click Compose
6. Fill in recipient, subject, body
7. Click Send

### 2. Open Browser and Navigate to URL

**Intention**: `"open browser and navigate to url"`

**Steps**: 7 steps

**Parameters**:
- `url`: Target URL

**Workflow**:
1. Open Brave Browser
2. Open new tab
3. Focus address bar
4. Type URL
5. Navigate

### 3. Search on Google

**Intention**: `"search on google"`

**Steps**: 4 steps

**Parameters**:
- `search_query`: Search terms

**Workflow**:
1. Focus address bar (Cmd+L)
2. Type search query
3. Press Enter
4. Wait for results

### 4. Open Application

**Intention**: `"open application"`

**Steps**: 2 steps

**Parameters**:
- `app_name`: Name of application to open

**Workflow**:
1. Open app via Raycast (Option+Space)
2. Wait for app to open

### 5. Find Text on Page

**Intention**: `"find text on page"`

**Steps**: 3 steps

**Parameters**:
- `search_term`: Text to find

**Workflow**:
1. Open find (Cmd+F)
2. Type search term
3. Press Enter

### 6. Open New Tab

**Intention**: `"open new tab"`

**Steps**: 2 steps

**Workflow**:
1. Press Cmd+T
2. Focus address bar (Cmd+L)

### 7. Close Current Tab

**Intention**: `"close current tab"`

**Steps**: 1 step

**Workflow**:
1. Press Cmd+W

### 8. Refresh Page

**Intention**: `"refresh page"`

**Steps**: 2 steps

**Workflow**:
1. Press Cmd+R
2. Wait for reload

## Usage

### Automatic Loading

Templates are automatically loaded when you initialize `GeminiWorkflowExecutor`:

```python
from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

# Templates are automatically loaded and merged
memory = VisualWorkflowMemory()
executor = GeminiWorkflowExecutor(memory=memory)

# Templates are now available alongside learned workflows
```

### Executing a Template

```python
# Get workflow by intention
actions = executor.get_workflow_by_intention("send email via gmail")

# Execute with parameters
executor.execute_workflow(
    workflow={'semantic_actions': actions},
    parameters={
        'recipient_email': 'user@example.com',
        'email_subject': 'Hello!',
        'email_body': 'This is a test email.'
    }
)
```

### Programmatic Access

```python
from workflow_templates import (
    get_all_templates,
    get_template,
    list_available_templates
)

# List all available templates
templates = list_available_templates()
# ['send email via gmail', 'search on google', ...]

# Get specific template
email_workflow = get_template("send email via gmail")
# Returns list of semantic actions
```

## Adding New Templates

To add a new workflow template:

1. **Edit `workflow_templates.py`**
2. **Add to `WORKFLOW_TEMPLATES` dict**:

```python
WORKFLOW_TEMPLATES: Dict[str, List[Dict]] = {
    # ... existing templates ...
    
    "your new workflow": [
        {
            "step_number": 1,
            "semantic_type": "open_application",
            "description": "Open your app",
            "target": "Your App Name",
            "value": None,
            "timestamp_seconds": 0.0,
            "confidence": 1.0,
            "is_parameterizable": False,
            "parameter_name": None
        },
        # ... more steps ...
    ]
}
```

### Template Design Guidelines

1. **Use descriptive intentions**: Clear, natural language keys
2. **Prefer keyboard shortcuts**: More reliable than mouse clicks
3. **Include wait times**: Allow pages/apps to load
4. **Mark parameters clearly**: Set `is_parameterizable=True` and provide `parameter_name`
5. **Use placeholders**: Use `{parameter_name}` in `value` field for substitution
6. **Test thoroughly**: Run `test_workflow_templates.py` after adding

### Parameter Substitution

For parameterizable steps:

```python
{
    "step_number": 10,
    "semantic_type": "type_text",
    "description": "Type recipient email address",
    "target": "To",
    "value": "{recipient_email}",          # Placeholder
    "is_parameterizable": True,
    "parameter_name": "recipient_email"    # Parameter name
}
```

The executor will automatically replace `{recipient_email}` with the provided parameter value.

## Template vs. Learned Workflows

### Hardcoded Templates

**Pros**:
- ✅ Available immediately (no recording needed)
- ✅ Highly optimized and tested
- ✅ Keyboard-shortcut focused (more reliable)
- ✅ Well-documented with parameters

**Cons**:
- ❌ Generic (not customized to user's environment)
- ❌ Limited to common tasks
- ❌ Requires code changes to update

### Learned Workflows

**Pros**:
- ✅ Customized to user's exact workflow
- ✅ Learns user's specific apps and preferences
- ✅ Can capture complex, unique workflows
- ✅ No coding required

**Cons**:
- ❌ Requires recording session
- ❌ May include unnecessary steps
- ❌ Quality depends on recording

### Priority

When there's a conflict, **learned workflows take precedence** over templates. This allows users to override generic templates with their own optimized versions.

## Testing

Run the test suite:

```bash
cd backend
python test_workflow_templates.py
```

Tests verify:
- ✅ Templates load correctly
- ✅ Structure is valid
- ✅ Integration with executor works
- ✅ Template retrieval works
- ✅ Parameters are properly defined

## Examples

### Example 1: Send Email

```python
executor = GeminiWorkflowExecutor(memory=memory)

# Get the email template
email_actions = executor.get_workflow_by_intention("send email via gmail")

# Execute with specific parameters
executor.execute_workflow(
    workflow={'semantic_actions': email_actions},
    parameters={
        'recipient_email': 'team@company.com',
        'email_subject': 'Weekly Update',
        'email_body': 'Here is this week\'s progress report...'
    }
)
```

### Example 2: Google Search

```python
# Gemini can use templates during natural language execution
executor.execute_workflow_by_request(
    "search for Python tutorials"
)
# Automatically matches "search on google" template
# and substitutes "Python tutorials" as the search query
```

### Example 3: Open Application

```python
# Direct template usage
app_template = executor.get_workflow_by_intention("open application")
executor.execute_workflow(
    workflow={'semantic_actions': app_template},
    parameters={'app_name': 'Slack'}
)
```

## Best Practices

1. **Start with templates**: Use hardcoded templates for common tasks
2. **Learn specific workflows**: Record custom workflows for unique tasks
3. **Combine both**: Let learned workflows override templates when needed
4. **Test regularly**: Run `test_workflow_templates.py` after changes
5. **Document parameters**: Clearly specify what each parameter expects

## Troubleshooting

### Template Not Found

```python
actions = executor.get_workflow_by_intention("my workflow")
# Returns None
```

**Solution**: Check `list_available_templates()` for exact intention string.

### Parameter Not Substituted

```python
# Parameter in template: {email_subject}
# But passing: {'subject': 'Hello'}  # Wrong key!
```

**Solution**: Use exact parameter names from template. Check with `get_template()`.

### Execution Fails

**Common Issues**:
1. App name doesn't match system (e.g., "Brave Browser" vs "Brave")
2. Wait times too short (increase `wait` step values)
3. Element descriptions don't match UI (update `target` fields)

## Future Enhancements

Potential improvements to the template system:

- [ ] Template versioning
- [ ] User-specific template customization
- [ ] Template marketplace/sharing
- [ ] Auto-generation of templates from recorded workflows
- [ ] Template validation and linting
- [ ] Platform-specific templates (Windows, Linux)
- [ ] Browser-specific templates (Chrome, Firefox, Safari)

## See Also

- [Workflow Executor Documentation](./INTELLIGENT_WORKFLOWS.md)
- [Semantic Workflow System](./SEMANTIC_WORKFLOW_SYSTEM.md)
- [Quick Start Guide](../backend/QUICKSTART.md)

