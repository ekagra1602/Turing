# AgentFlow Demo Guide
## Intelligent Workflow Automation System

---

## 🎯 Demo Overview

**What you'll demonstrate:**
1. **Record** a Canvas workflow once (download assignment for ML class)
2. **Execute** it automatically for other classes (Data Mining, Data Visualization)
3. Show the agent **learns intent**, not just clicks

**Time**: 5-10 minutes
**Impact**: Shows programming by demonstration → generalizable automation

---

## 🛠️ Setup (Before Demo)

### 1. Set Environment Variables

```bash
# Required
export GOOGLE_API_KEY='your_gemini_api_key_here'
export SNOWFLAKE_ACCOUNT='your_account'
export SNOWFLAKE_WAREHOUSE='COMPUTE_WH'
export SNOWFLAKE_DATABASE='AGENTFLOW_DB'
export SNOWFLAKE_SCHEMA='PUBLIC'
```

### 2. Install Dependencies

```bash
cd /Users/aryank/Developer/CalHacks2025/agentflow/backend
pip3 install -r requirements_fast.txt
```

### 3. Test System

```bash
cd /Users/aryank/Developer/CalHacks2025/agentflow/backend
python3 -c "from intelligent_workflow_system import IntelligentWorkflowSystem; system = IntelligentWorkflowSystem(); print('✅ System ready!')"
```

---

## 📋 Demo Script: Canvas Assignment Download

### **Phase 1: Recording the Workflow** (3 minutes)

**Setup:**
- Open Terminal
- Have Canvas website ready in browser
- Have 2-3 classes visible on Canvas

**Script:**

```bash
cd /Users/aryank/Developer/CalHacks2025/agentflow/backend
python3 workflow_cli.py
```

**In the CLI:**

```
💬 Your request: record Download Canvas Assignment for ML

# System starts recording...
# YOU SAY: "Now I'll demonstrate downloading an assignment from Canvas"
```

**Perform the workflow naturally:**
1. **Open Browser** (if not open):
   - Press `Cmd+Space`
   - Type "chrome" 
   - Press Enter

2. **Navigate to Canvas**:
   - Click address bar
   - Type "canvas.asu.edu" (or your Canvas URL)
   - Press Enter

3. **Select ML Course**:
   - Click on "Machine Learning" course card/link
   
4. **Go to Assignments**:
   - Click "Assignments" in left sidebar

5. **Download Assignment**:
   - Click on latest assignment (e.g., "Homework 3")
   - Click "Download" or "Submit" button

**Stop Recording:**
```
💬 Your request: stop

# System analyzes workflow...
# 🧠 Analyzing workflow to understand intent...
# ✅ Workflow understood!
#    5 semantic actions
#    1 parameter identified: course_name
```

**What just happened:**
- ✅ System recorded raw clicks/keys
- 🧠 Gemini analyzed and understood: "User wants to download assignment for a course"
- 🎯 Identified parameter: `course_name = "Machine Learning"`
- ☁️ Stored in Snowflake (or local)

---

### **Phase 2: Executing with Different Parameters** (2 minutes)

**YOU SAY:** "Now watch - I can use natural language to do this for ANY class"

**Execute for Data Mining:**
```
💬 Your request: Download Canvas assignment for Data Mining

# System output:
# 🔍 Finding similar workflows...
# ✓ Found 1 similar workflow(s):
# 1. Download Canvas Assignment for ML (similarity: 92%)
# 
# 🎯 Extracting parameters from your request...
# ✓ Extracted parameters:
#    course_name = Data Mining
#
# Execute this workflow? [y/n]: y
#
# 🚀 Executing workflow...
# 📍 Semantic Action 1/5: open_application
#    🚀 Opening application: Chrome
# 📍 Semantic Action 2/5: click_element
#    🎯 Clicking: Data Mining
# ...
# ✅ WORKFLOW COMPLETED SUCCESSFULLY
```

**What just happened:**
- 🔍 Gemini matched your prompt to the recorded workflow
- 🎯 Extracted new parameter: "Data Mining"
- 🎬 Executed using Gemini Computer Use (adapts to current UI!)
- ✨ No coordinates - found "Data Mining" visually

**Execute for another class:**
```
💬 Your request: Download Canvas assignment for Data Visualization

# Same magic happens!
# Works for ANY class on Canvas
```

---

### **Phase 3: Show the Intelligence** (2 minutes)

**YOU SAY:** "Let me show you what's different from traditional automation"

**Show the semantic actions:**
```
💬 Your request: list

# Shows stored workflows with semantic understanding:
# 1. Download Canvas Assignment for ML
#    Description: Navigate to Canvas and download assignment
#    Actions: 5 semantic actions
#    Parameters: course_name
#    Used: 3 times
```

**Explain the difference:**

```
Traditional Automation (brittle):
  Step 1: click(450, 320)      ❌ Breaks if window moves
  Step 2: type('M','a','c'...) ❌ Exact characters
  Step 3: click(780, 450)      ❌ Breaks if UI changes

Our System (intelligent):
  Step 1: open_application("Chrome")     ✅ Any screen size
  Step 2: click_element("Machine Learning") ✅ Finds visually
  Step 3: click_element("Assignments")   ✅ Adapts to UI
```

---

## 🎪 Alternative Demo: Jira Ticket Closing

### **If Canvas isn't available, use Jira:**

**Phase 1: Record**
```
💬 Your request: record Close Jira Ticket
```

**Perform:**
1. Open Jira website
2. Search for ticket "BUG-123"
3. Click ticket
4. Click "Close" button
5. Select resolution "Fixed"
6. Click "Confirm"

**Stop:**
```
💬 Your request: stop
```

**Phase 2: Execute**
```
💬 Your request: Close Jira ticket BUG-456
💬 Your request: Close Jira ticket BUG-789
```

---

## 💡 Key Talking Points

### **1. Learning by Demonstration**
- "You don't write code - you just show the agent once"
- "Like training an intern by having them shadow you"

### **2. Semantic Understanding**
- "It understands WHAT you're doing, not just clicks"
- "Gemini analyzes: 'User wants to download assignment for a course'"

### **3. Generalization**
- "Show it once with 'Machine Learning' → works for ANY course"
- "Parameters are automatically identified"

### **4. Adaptability**
- "Uses Gemini Computer Use - finds elements by vision"
- "Works even if Canvas changes UI or screen resolution changes"

### **5. Cloud Storage (if using Snowflake)**
- "Workflows stored in Snowflake"
- "Multiple agents can share workflows"
- "Query: 'Show me all Canvas workflows'"

---

## 🚨 Troubleshooting

### **If recording doesn't start:**
```bash
# Check permissions:
System Preferences → Security & Privacy → Accessibility
→ Grant access to Terminal
```

### **If Gemini can't find elements:**
- Make sure elements are visible on screen
- Use descriptive text: "Download button" not "blue button"
- Ensure GOOGLE_API_KEY is set correctly

### **If no workflows found:**
```bash
# Check if workflow was saved:
cd backend
python3 -c "from visual_memory import VisualWorkflowMemory; m = VisualWorkflowMemory(); print(m.list_workflows())"
```

### **If execution fails:**
- Check if browser/app is open
- Ensure screen is visible (not minimized)
- Try with `confirm_steps=True` to debug step-by-step

---

## 🎬 Demo Flow Summary

1. **Setup** (30 seconds)
   - Open terminal
   - Start workflow_cli.py
   - Have Canvas ready

2. **Record** (2 minutes)
   - Say: "Watch me demonstrate once"
   - Perform workflow naturally
   - Stop recording
   - Show: "System understood the intent"

3. **Execute** (2 minutes)
   - Say: "Now I can do this for any class"
   - Execute with different course
   - Show it working automatically
   - Execute with another course

4. **Explain** (1-2 minutes)
   - Show semantic actions vs raw clicks
   - Explain: learns intent, not coordinates
   - Show Snowflake database (optional)

**Total**: 5-7 minutes

---

## 📊 What Makes This Impressive

### **For Judges:**
- ✅ **Novel approach**: Programming by demonstration
- ✅ **Real-world impact**: 911 dispatchers, support teams, data entry
- ✅ **Technical depth**: Gemini Computer Use, semantic analysis, cloud storage
- ✅ **Scalability**: Works for any repetitive task

### **Use Cases to Mention:**
1. **911 Dispatch**: "Close incident for address X"
2. **Customer Support**: "Reply to ticket X with template Y"
3. **Data Entry**: "Fill form for employee X"
4. **Testing**: "Test checkout flow with product X"
5. **DevOps**: "Deploy service X to environment Y"

---

## 🎯 Success Criteria

**Demo is successful if:**
- ✅ Records workflow without errors
- ✅ Executes with different parameter automatically
- ✅ Shows it's NOT just replaying clicks (explain semantic understanding)
- ✅ Impresses judges with generalization capability

**Bonus points if:**
- ✅ Show Snowflake database query
- ✅ Execute same workflow on different computer (cloud storage!)
- ✅ Show parameter extraction working
- ✅ Compare to traditional automation

---

## 📝 Quick Commands Reference

```bash
# Start CLI
python3 workflow_cli.py

# Record workflow
> record <name>
> (perform actions)
> stop

# Execute workflow
> <natural language prompt>

# List workflows
> list

# Quit
> quit
```

---

## 🎉 After Demo

**If they ask for more details:**
- Show `docs/SEMANTIC_WORKFLOW_SYSTEM.md` for architecture
- Show `docs/SNOWFLAKE_INTEGRATION.md` for cloud storage
- Show `backend/semantic_action_analyzer.py` for how it works

**If they want to try:**
- Give them workflow_cli.py
- Show them how to record their own workflow
- Let them execute it

**If they ask about limitations:**
- Be honest: Works best for web workflows
- Needs clear visual elements
- Requires Gemini API (cost per execution)
- Best for 3-10 step workflows

---

**Good luck with your demo! 🚀**

