# 🧠 Intelligent Workflow System

**Learn once, execute many times with natural language prompts**

---

## 🎯 What is This?

An intelligent automation system that:
1. **Learns** by watching you perform tasks
2. **Understands** what you want from natural language prompts
3. **Adapts** workflows to new contexts automatically
4. **Executes** using Gemini 2.5 Flash's vision capabilities

### The Magic

```
You do it once → System learns → You can repeat it forever
```

**Examples:**
- Close one Jira ticket → Close any Jira ticket
- Fill one job application → Fill 100 job applications
- Download one Canvas assignment → Download all Canvas assignments

---

## 🏗️ Architecture

### Core Components

1. **`intelligent_workflow_system.py`** - Main orchestrator
   - Takes user prompts
   - Finds similar workflows
   - Extracts parameters
   - Executes with adaptation

2. **`semantic_workflow_matcher.py`** - Similarity matching
   - Uses sentence embeddings (all-MiniLM-L6-v2)
   - Falls back to Gemini LLM if embeddings unavailable
   - Finds workflows similar to user prompts

3. **`gemini_workflow_executor.py`** - Execution engine
   - Uses Gemini 2.5 Flash for screen understanding
   - Adapts workflows to new screen layouts
   - Handles variations automatically

4. **`gemini_computer_use.py`** - Vision-based interaction
   - Native screen understanding
   - Accurate clicking without OCR
   - Robust to UI changes

5. **`visual_memory.py`** - Workflow storage
   - Stores steps with before/after screenshots
   - Metadata: name, description, tags
   - Usage tracking

---

## 🚀 Quick Start

### Installation

```bash
# 1. Install dependencies
cd backend
pip install -r requirements_fast.txt

# 2. (Optional) Install for semantic matching
pip install sentence-transformers

# 3. Set API key
export GOOGLE_API_KEY='your_key_here'
```

### Usage

#### **Option 1: Interactive Mode** (Recommended)

```bash
./start_fast_computer_use.sh
# Choose option 1: Intelligent Workflow System
```

Or directly:
```bash
cd backend
python workflow_cli.py
```

#### **Option 2: Command Line**

```bash
# List workflows
python workflow_cli.py list

# Execute workflow
python workflow_cli.py execute "Close Jira ticket ABC-123"

# Record new workflow
python workflow_cli.py record "My Workflow Name"
```

#### **Option 3: Python API**

```python
from intelligent_workflow_system import IntelligentWorkflowSystem

# Initialize
system = IntelligentWorkflowSystem()

# List workflows
system.list_workflows()

# Execute from prompt
system.execute_from_prompt("Close Jira ticket ABC-123")

# Record new workflow
system.record_workflow("Close Jira Ticket", 
                       description="Close any Jira ticket")
# ... perform actions ...
system.stop_recording()
```

---

## 📖 Complete Workflow

### 1. Record a Workflow

```python
from intelligent_workflow_system import IntelligentWorkflowSystem

system = IntelligentWorkflowSystem()

# Start recording
workflow_id = system.record_workflow(
    "Close Jira Ticket",
    description="Close a Jira ticket with comments"
)

# Now perform your workflow:
# 1. Open Jira
# 2. Search for ticket "BUG-123"
# 3. Click "Close"
# 4. Add comment
# 5. Submit

# Stop recording
system.stop_recording()
```

### 2. Execute with Different Parameters

```python
# Close a different ticket
system.execute_from_prompt("Close Jira ticket BUG-456")

# System will:
# ✓ Find your "Close Jira Ticket" workflow
# ✓ Extract parameter: ticket = "BUG-456"
# ✓ Adapt workflow to current screen
# ✓ Execute steps with new ticket number
```

### 3. Execute Multiple Times

```python
tickets = ["BUG-456", "BUG-789", "BUG-101"]

for ticket in tickets:
    system.execute_from_prompt(f"Close Jira ticket {ticket}")
```

---

## 🎓 How It Works

### Phase 1: Learning

```
User performs task
       ↓
WorkflowRecorder captures:
  - Screenshots (before/after each action)
  - Action types (click, type, scroll)
  - Visual context (what was clicked, typed)
  - Coordinates (normalized)
       ↓
Stored in VisualWorkflowMemory
```

### Phase 2: Matching

```
User prompt: "Close Jira ticket ABC"
       ↓
SemanticWorkflowMatcher:
  - Embeds prompt → vector
  - Compares to all workflows → similarities
  - Returns top matches
       ↓
Best match: "Close Jira Ticket" (similarity: 0.89)
```

### Phase 3: Parameter Extraction

```
Prompt: "Close Jira ticket ABC"
Workflow: "Close Jira Ticket"
       ↓
Gemini LLM analyzes:
  "What parameters does user want?"
       ↓
Extracted: {"ticket": "ABC"}
```

### Phase 4: Execution

```
For each step in workflow:
  1. Gemini looks at current screen
  2. Finds element (e.g., "ticket search box")
  3. Adapts if layout changed
  4. Executes action (click, type, etc.)
  5. Verifies success
```

---

## 🎯 Use Cases

### 1. Repetitive Web Tasks

**Record once:**
- Fill out a job application
- Submit an expense report
- Post to social media

**Execute many times:**
```python
system.execute_from_prompt("Fill job application for Google")
system.execute_from_prompt("Fill job application for Meta")
system.execute_from_prompt("Fill job application for Apple")
```

### 2. Data Entry

**Record once:**
- Enter customer data into CRM
- Update spreadsheet from email
- Copy data between systems

**Execute with variations:**
```python
customers = get_customer_list()
for customer in customers:
    system.execute_from_prompt(f"Add customer {customer.name} to CRM")
```

### 3. Testing & QA

**Record once:**
- Complete checkout flow
- Test login process
- Submit form with validations

**Execute repeatedly:**
```python
# Test with different users
for user in test_users:
    system.execute_from_prompt(f"Login as {user.email}")
```

### 4. Content Management

**Record once:**
- Publish blog post
- Upload video to YouTube
- Schedule social media post

**Execute for batch operations:**
```python
posts = get_draft_posts()
for post in posts:
    system.execute_from_prompt(f"Publish blog post: {post.title}")
```

---

## 🔧 Advanced Features

### Workflow Composition

Chain multiple workflows together:

```python
from workflow_composition import WorkflowComposer, CompositionStep

composer = WorkflowComposer(memory)

# Create composition
composer.create_composition(
    name="Process all assignments",
    description="Download and grade all student assignments",
    steps=[
        CompositionStep(
            workflow_id="open-canvas-class",
            workflow_name="Open Canvas Class",
            parameters={"class": "Machine Learning"}
        ),
        CompositionStep(
            workflow_id="download-assignments",
            workflow_name="Download All Assignments",
            parameters={}
        ),
        # Repeat for each class...
    ]
)
```

### Adaptive Learning

System learns from corrections:

```python
from workflow_composition import AdaptiveLearner

learner = AdaptiveLearner(memory)

# If execution fails, record what worked
learner.record_correction(
    workflow_id="close-jira",
    step_number=3,
    what_failed="Button location changed",
    what_worked={"new_coordinates": (150, 200)}
)

# System will adapt future executions
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Workflow matching | < 100ms (embeddings) or ~1s (LLM) |
| Parameter extraction | ~500ms (Gemini) |
| Step execution | ~1-2s per step (Gemini vision) |
| **Total per workflow** | **~5-10s for typical workflow** |

### Comparison

| Method | Speed | Accuracy | Adaptability |
|--------|-------|----------|--------------|
| Hard-coded coordinates | ⚡ Fast | ❌ Breaks often | ❌ None |
| OCR + coordinates | 🐌 Slow | ⚠️  Medium | ⚠️  Limited |
| **Gemini Vision** | ⚡ Fast | ✅ High | ✅ Excellent |

---

## 🐛 Troubleshooting

### "No matching workflows found"

**Solution:** Record a workflow first
```python
system.record_workflow("Your Task Name")
# perform task
system.stop_recording()
```

### "GOOGLE_API_KEY not set"

**Solution:** Set your API key
```bash
export GOOGLE_API_KEY='your_key_here'
```

Get key at: https://aistudio.google.com/apikey

### "Element not found on screen"

**Causes:**
1. Screen layout changed significantly
2. Element not visible (scrolling needed)
3. Wrong application/window

**Solutions:**
- Re-record workflow with current UI
- Add scroll steps to workflow
- Ensure correct application is focused

### "Workflow executing wrong actions"

**Solution:** Improve visual context during recording
- Click directly on intended elements
- Wait for page loads between actions
- Avoid recording during animations

---

## 💡 Best Practices

### Recording Workflows

1. **Be deliberate** - Pause between actions
2. **Use visual cues** - Click on text/buttons (not blank space)
3. **Wait for loads** - Let pages fully load
4. **Name clearly** - Use descriptive workflow names
5. **Add descriptions** - Explain what the workflow does

### Executing Workflows

1. **Test first** - Use `confirm_steps=True` for first run
2. **Handle failures** - Workflows may need adaptation
3. **Batch wisely** - Don't overload systems
4. **Monitor execution** - Watch first few runs

### Organizing Workflows

1. **Use tags** - Categorize workflows
   ```python
   system.record_workflow("Task", tags=["work", "jira"])
   ```

2. **Good names** - Descriptive and searchable
   - ✅ "Close Jira Ticket with Comment"
   - ❌ "jira_workflow_1"

3. **Document parameters** - Note what can be changed
   - Description: "Close any Jira ticket (specify ticket #)"

---

## 🔮 Future Enhancements

- [ ] Multi-application workflows (switch between apps)
- [ ] Conditional logic (if-then-else in workflows)
- [ ] Error recovery (automatic retry with variations)
- [ ] Workflow debugging (step-by-step replay)
- [ ] Sharing workflows (export/import workflow packages)
- [ ] Browser extension (record web workflows easily)

---

## 📚 Additional Resources

- **Gemini Computer Use**: `gemini_computer_use.py`
- **Visual Memory System**: `visual_memory.py`
- **Workflow Recorder**: `recorder.py`
- **Robust Executor**: `robust_executor.py`

---

## 🤝 Contributing

Found a bug? Have an idea? Open an issue or submit a PR!

---

**Built with ❤️ using Gemini 2.5 Flash**

