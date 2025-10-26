# AgentFlow Voice Integration

**Voice-controlled desktop automation** - Speak to AgentFlow and watch it execute workflows automatically!

## 🎯 What This Does

Transform your voice into desktop automation commands:

- **"Send an email to John"** → AgentFlow automatically executes the email workflow
- **"Open my Canvas class"** → AgentFlow navigates to Canvas and opens your class
- **"Remember what I'm going to do now"** → AgentFlow prepares to learn a new workflow

## 🏗️ Architecture

```
Voice Input → STT (Groq Whisper) → Text Processing → Workflow Detection → AgentFlow Execution → Desktop Actions
     ↓
TTS (ElevenLabs) ← Response Generation ← Execution Status ← Workflow Results
```

## 🚀 Quick Start

### 1. Set Up Voice Agent

```bash
cd backend/voice

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Get API keys (see QUICKSTART.md)
cp .env.example .env.local
# Add your API keys to .env.local
```

### 2. Test Integration

```bash
# Test the voice-workflow integration
python test_voice_integration.py
```

### 3. Start Voice Agent

```bash
# Terminal 1 - Voice Agent
python agent.py dev
```

### 4. Start Frontend

```bash
# Terminal 2 - Voice UI
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and start talking!

## 🎤 Voice Commands

### Execution Commands
AgentFlow automatically detects and executes workflows:

- **"Send an email to [person]"**
- **"Open my Canvas class"**
- **"Execute the workflow for [task]"**
- **"Run the [workflow name]"**
- **"Do the [action] workflow"**

### Recording Commands
Prepare AgentFlow to learn new workflows:

- **"Remember what I'm going to do now"**
- **"Watch me do this"**
- **"Learn this workflow"**
- **"Show you how to [action]"**

### General Commands
Normal conversation:

- **"How are you doing?"**
- **"What workflows do you know?"**
- **"What can you help me with?"**

## 🔧 How It Works

### 1. Voice Processing Pipeline

```python
# Voice input → Text
stt = groq.STT(model="whisper-large-v3-turbo")

# Text → Intent Detection
is_workflow, cmd_type = bridge.is_workflow_command(text)

# Intent → Action
if cmd_type == 'execute':
    result = await bridge.execute_workflow_from_voice(text)
```

### 2. Workflow Execution

```python
# Bridge connects voice to AgentFlow
class VoiceWorkflowBridge:
    def execute_workflow_from_voice(self, command):
        # Use AgentFlow's intelligent system
        success = self.system.execute_from_prompt(
            command, 
            auto_execute=True, 
            confirm_steps=False
        )
        return success
```

### 3. Custom Agent Class

```python
class WorkflowAwareAgent(Agent):
    async def on_user_message(self, message):
        # Detect workflow commands
        is_workflow, cmd_type = self.workflow_bridge.is_workflow_command(message)
        
        if is_workflow and cmd_type == 'execute':
            # Execute workflow asynchronously
            await self.say("Got it! I'll execute that for you right away.")
            asyncio.create_task(self._execute_workflow_async(message))
```

## 📁 File Structure

```
backend/voice/
├── agent.py                    # Enhanced voice agent with workflow integration
├── voice_workflow_bridge.py    # Bridge between voice and AgentFlow system
├── test_voice_integration.py   # Integration tests
├── frontend/                   # Voice UI (unchanged)
│   ├── app/page.tsx
│   ├── components/VoiceOrb.tsx
│   └── ...
└── requirements.txt            # Dependencies
```

## 🔌 Integration Points

### VoiceWorkflowBridge

The bridge connects the voice system to AgentFlow:

```python
bridge = VoiceWorkflowBridge()

# Detect workflow commands
is_workflow, cmd_type = bridge.is_workflow_command("Send email to John")

# Execute workflows
result = await bridge.execute_workflow_from_voice("Send email to John")

# Get available workflows
workflows = bridge.get_available_workflows()
```

### WorkflowAwareAgent

Custom agent that intercepts voice commands:

```python
class WorkflowAwareAgent(Agent):
    def __init__(self, instructions, workflow_bridge):
        super().__init__(instructions)
        self.workflow_bridge = workflow_bridge
    
    async def on_user_message(self, message):
        # Process workflow commands before normal conversation
        if self.workflow_bridge.is_workflow_command(message):
            # Execute workflow
        else:
            # Normal conversation
```

## 🧪 Testing

### Run Integration Tests

```bash
python test_voice_integration.py
```

### Test Voice Commands

1. Start the voice agent: `python agent.py dev`
2. Start the frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000
4. Click the voice orb
5. Try these commands:
   - "Send an email to John"
   - "Open my Canvas class"
   - "Remember what I'm going to do now"

### Expected Behavior

- **Execution commands**: Agent acknowledges → Executes workflow → Confirms completion
- **Recording commands**: Agent prepares for learning mode
- **General commands**: Normal conversation

## 🐛 Troubleshooting

### Voice Agent Won't Start

```bash
# Check API keys
python test_apis.py

# Check integration
python test_voice_integration.py
```

### Workflows Not Executing

1. Verify AgentFlow system is available:
   ```bash
   cd ..  # Go to backend/
   python workflow_cli.py list
   ```

2. Check workflow bridge initialization:
   ```bash
   python test_voice_integration.py
   ```

### No Voice Response

- Check microphone permissions
- Verify speakers/headphones working
- Look for errors in browser console
- Ensure backend agent is running

## 🎨 Customization

### Add New Voice Commands

Edit `voice_workflow_bridge.py`:

```python
# Add new execution triggers
self.execution_triggers = [
    "execute", "run", "do", "perform", "start", "launch", "begin",
    "send", "open", "create", "fill", "submit", "close", "navigate",
    "your_new_trigger"  # Add here
]
```

### Change Agent Personality

Edit `agent.py`:

```python
AGENT_INSTRUCTIONS = """You are AgentFlow, a helpful voice AI assistant...

# Modify the personality here
You have a sense of humor and are curious about what users are teaching you.
You're also enthusiastic about automation and love helping users be more productive.
"""
```

### Custom Workflow Detection

Override the detection logic:

```python
def is_workflow_command(self, text: str) -> Tuple[bool, str]:
    # Add custom detection logic
    if "my_custom_pattern" in text.lower():
        return True, 'execute'
    
    # Use default detection
    return self._default_detection(text)
```

## 🚀 Next Steps

### Enhanced Features

1. **Visual Feedback**: Show workflow execution progress in the voice UI
2. **Parameter Extraction**: Parse parameters from voice commands
3. **Workflow Suggestions**: Suggest workflows based on context
4. **Multi-step Workflows**: Handle complex multi-step voice commands

### Integration Ideas

1. **Calendar Integration**: "Schedule a meeting with John tomorrow"
2. **File Operations**: "Create a document called project proposal"
3. **System Control**: "Open my development environment"
4. **Web Automation**: "Search for Python tutorials on YouTube"

## 📚 Resources

- **Voice System**: [QUICKSTART.md](./QUICKSTART.md)
- **AgentFlow System**: [../README.md](../README.md)
- **Workflow Templates**: [../WORKFLOW_TEMPLATES.md](../WORKFLOW_TEMPLATES.md)
- **Desktop Overlay**: [frontend/ELECTRON.md](./frontend/ELECTRON.md)

---

**Made for CalHacks 2025** 🚀

*Voice-controlled desktop automation - the future is here!*
