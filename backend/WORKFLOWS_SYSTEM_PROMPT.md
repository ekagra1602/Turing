# Workflows in System Prompt

## Overview

ALL workflows are now automatically loaded into the Gemini executor agent's system prompt as a key-value dictionary. The LLM can see all available workflows and automatically match user requests to the appropriate workflow.

## How It Works

### 1. On Initialization

When you create a `GeminiWorkflowExecutor`, it:
- Loads all ready workflows from visual memory
- Creates a dictionary: `{intention: semantic_actions}`
- Passes this dictionary to `GeminiComputerUse`
- Builds a system prompt containing ALL workflows
- Gemini now has complete context of all learned behaviors

```python
executor = GeminiWorkflowExecutor(verbose=True)
# Output:
# ✅ Gemini Computer Use initialized
#    Model: gemini-2.0-flash-exp
#    Loaded 2 workflows into system context
# ✅ Gemini Workflow Executor initialized
#    Loaded 2 workflows:
#      • The user is checking the syllabus for a specific course on Canvas.
#      • The user is navigating the Canvas website to view the syllabus for a specific course.
```

### 2. System Prompt Format

The system prompt includes:
- List of all workflow intentions
- Complete semantic action sequence for each
- Target elements, values, and parameters
- Instructions to match user requests to workflows

Example:
```
# AVAILABLE LEARNED WORKFLOWS

## Workflow: The user is checking the syllabus for a specific course on Canvas.

Semantic Actions:
1. [open_application] User opened Brave Browser using Spotlight search
   Target: Brave Browser
2. [type_text] User typed 'canvas.asu.edu' into the address bar
   Target: address bar
   Value: canvas.asu.edu
3. [navigate] User navigated to the URL entered in the address bar
...
```

### 3. Automatic Matching

The LLM can now:
- See all available workflows in context
- Match user natural language requests to workflows
- Adapt parameters (e.g., different course names)
- Execute the appropriate workflow

## No Fuzzy Matching Logic Needed

Instead of implementing complex fuzzy matching algorithms, we let the LLM do what it's best at:
- Understanding natural language
- Finding semantic matches
- Reasoning about which workflow fits the request

## Implementation

### Files Modified

**gemini_computer_use.py**:
- Added `workflows_dict` parameter to `__init__` (line 36)
- Added `_build_system_prompt()` method (line 73-106)
- System prompt includes all workflows in structured format

**gemini_workflow_executor.py**:
- Loads workflows before initializing Gemini (line 52)
- Passes workflows to GeminiComputerUse (line 55-58)
- Updates system prompt when reloading workflows (line 123-124)

## Benefits

1. **Simple**: No complex matching logic
2. **Reliable**: LLM handles semantic understanding
3. **Flexible**: Works with natural language requests
4. **Demo-Ready**: Optimized for things to work, not perfection
5. **Scalable**: All workflows available at once

## Testing

Run the test to see it in action:

```bash
source venv/bin/activate
python test_workflows_system_prompt.py
```

## Example Usage

```python
from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor

# Initialize (workflows automatically loaded into system prompt)
executor = GeminiWorkflowExecutor(verbose=True)

# Access the workflows dictionary
print(f"Loaded workflows: {len(executor.workflows_by_intention)}")

# View system prompt
print(executor.gemini.system_prompt)

# Gemini can now match any request to available workflows!
```

## Recording New Workflows

After recording a new workflow via the UI:

```python
# Reload workflows to update system prompt
executor.reload_workflows()
# Output:
# 🔄 Reloading workflows...
# ✅ Reloaded 3 workflows
#    System prompt updated
```

The new workflow is immediately available to Gemini in the system context.
