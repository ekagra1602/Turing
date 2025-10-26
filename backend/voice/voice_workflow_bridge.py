#!/usr/bin/env python3
"""
Voice Workflow Bridge - Connects Voice Agent to AgentFlow Desktop Automation

This module bridges the voice interface with the main AgentFlow workflow execution system.
It allows voice commands to trigger desktop automation workflows.
"""

import asyncio
import logging
import os
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Add parent directory to path to import AgentFlow modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from intelligent_workflow_system import IntelligentWorkflowSystem
    from visual_memory import VisualWorkflowMemory
    from semantic_workflow_matcher import SemanticWorkflowMatcher
except ImportError as e:
    print(f"Warning: Could not import AgentFlow modules: {e}")
    print("Voice workflow integration will be limited")

logger = logging.getLogger("voice-workflow-bridge")


class VoiceWorkflowBridge:
    """
    Bridge between voice commands and AgentFlow workflow execution.
    
    This class handles:
    1. Parsing voice commands for workflow triggers
    2. Executing workflows through the AgentFlow system
    3. Providing status feedback to the voice agent
    4. Managing workflow execution state
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.system: Optional[IntelligentWorkflowSystem] = None
        self.memory: Optional[VisualWorkflowMemory] = None
        self.matcher: Optional[SemanticWorkflowMatcher] = None
        self.is_executing = False
        self.last_execution_result = None
        
        # Initialize AgentFlow system
        self._initialize_system()
        
        # Voice command patterns for workflow execution
        self.execution_triggers = [
            "execute", "run", "do", "perform", "start", "launch", "begin",
            "send", "open", "create", "fill", "submit", "close", "navigate"
        ]
        
        # Recording mode triggers
        self.recording_triggers = [
            "remember", "watch", "learn", "record", "observe", "teach",
            "show you", "demonstrate", "capture"
        ]
    
    def _initialize_system(self):
        """Initialize the AgentFlow workflow system"""
        try:
            if self.verbose:
                print("🔗 Initializing AgentFlow Voice Workflow Bridge...")
            
            # Initialize the intelligent workflow system
            self.system = IntelligentWorkflowSystem(verbose=False, use_snowflake=True)
            self.memory = self.system.memory
            self.matcher = self.system.matcher
            
            if self.verbose:
                print("✅ AgentFlow system connected")
                workflows = self.memory.list_workflows(status='ready')
                print(f"   📚 {len(workflows)} workflows available")
                
        except Exception as e:
            logger.error(f"Failed to initialize AgentFlow system: {e}")
            if self.verbose:
                print(f"⚠️  AgentFlow system not available: {e}")
            self.system = None
    
    def is_workflow_command(self, text: str) -> Tuple[bool, str]:
        """
        Determine if the voice command is requesting workflow execution.
        
        Args:
            text: Transcribed speech text
            
        Returns:
            Tuple of (is_workflow_command, command_type)
            command_type: 'execute', 'record', or 'unknown'
        """
        text_lower = text.lower().strip()
        
        # Check for recording triggers first (more specific)
        for trigger in self.recording_triggers:
            if trigger in text_lower:
                return True, 'record'
        
        # Check for execution triggers (but exclude general conversation)
        execution_found = False
        for trigger in self.execution_triggers:
            if trigger in text_lower:
                execution_found = True
                break
        
        # Only return execute if it's clearly a workflow command
        if execution_found:
            # Check for general conversation patterns that shouldn't trigger workflows
            general_patterns = [
                "how are you", "what's the weather", "tell me a joke", 
                "how do you", "what can you", "what do you", "who are you",
                "good morning", "good afternoon", "good evening", "hello", "hi"
            ]
            
            for pattern in general_patterns:
                if pattern in text_lower:
                    return False, 'unknown'
            
            return True, 'execute'
        
        return False, 'unknown'
    
    async def execute_workflow_from_voice(self, voice_command: str) -> Dict:
        """
        Execute a workflow based on voice command.
        
        Args:
            voice_command: The transcribed voice command
            
        Returns:
            Dict with execution result and status
        """
        if not self.system:
            return {
                'success': False,
                'error': 'AgentFlow system not available',
                'message': 'Sorry, I cannot execute workflows right now. The AgentFlow system is not connected.'
            }
        
        if self.is_executing:
            return {
                'success': False,
                'error': 'Already executing',
                'message': 'I am already executing a workflow. Please wait for it to complete.'
            }
        
        try:
            self.is_executing = True
            
            if self.verbose:
                print(f"\n🎤 VOICE COMMAND: {voice_command}")
                print("🔄 Executing workflow...")
            
            # Execute the workflow in a separate thread to avoid blocking
            result = await self._execute_workflow_async(voice_command)
            
            self.last_execution_result = result
            
            if result['success']:
                message = f"I've executed your request: {voice_command}"
                if result.get('workflow_name'):
                    message += f" using the {result['workflow_name']} workflow"
            else:
                message = f"I couldn't execute that request. {result.get('error', 'Unknown error')}"
            
            return {
                'success': result['success'],
                'message': message,
                'workflow_name': result.get('workflow_name'),
                'error': result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow from voice: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Sorry, there was an error executing your request: {e}"
            }
        finally:
            self.is_executing = False
    
    async def _execute_workflow_async(self, voice_command: str) -> Dict:
        """Execute workflow asynchronously"""
        loop = asyncio.get_event_loop()
        
        def execute_sync():
            try:
                # Use the intelligent workflow system to execute
                success = self.system.execute_from_prompt(
                    voice_command, 
                    auto_execute=True, 
                    confirm_steps=False
                )
                
                # Try to get workflow name from the system
                workflow_name = None
                if hasattr(self.system, 'last_executed_workflow'):
                    workflow_name = self.system.last_executed_workflow
                
                return {
                    'success': success,
                    'workflow_name': workflow_name,
                    'command': voice_command
                }
                
            except Exception as e:
                logger.error(f"Workflow execution error: {e}")
                return {
                    'success': False,
                'error': str(e),
                    'command': voice_command
                }
        
        # Run in thread pool to avoid blocking
        result = await loop.run_in_executor(None, execute_sync)
        return result
    
    def get_available_workflows(self) -> List[Dict]:
        """Get list of available workflows for voice commands"""
        if not self.memory:
            return []
        
        try:
            workflows = self.memory.list_workflows(status='ready')
            return [
                {
                    'name': wf['name'],
                    'description': wf.get('description', 'No description'),
                    'steps_count': wf['steps_count'],
                    'tags': wf.get('tags', [])
                }
                for wf in workflows
            ]
        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
            return []
    
    def get_execution_status(self) -> Dict:
        """Get current execution status"""
        return {
            'is_executing': self.is_executing,
            'last_result': self.last_execution_result,
            'system_available': self.system is not None,
            'workflows_count': len(self.get_available_workflows())
        }
    
    def prepare_recording_mode(self) -> Dict:
        """
        Prepare for workflow recording mode.
        This would integrate with the recorder system.
        """
        if not self.system:
            return {
                'success': False,
                'message': 'AgentFlow system not available for recording'
            }
        
        # TODO: Integrate with recorder.py
        # For now, return a placeholder response
        return {
            'success': True,
            'message': 'I am ready to watch and learn your workflow. Please start demonstrating the steps you want me to remember.',
            'recording_mode': True
        }


# Global bridge instance
voice_bridge = None

def get_voice_bridge() -> VoiceWorkflowBridge:
    """Get the global voice workflow bridge instance"""
    global voice_bridge
    if voice_bridge is None:
        voice_bridge = VoiceWorkflowBridge(verbose=True)
    return voice_bridge


if __name__ == "__main__":
    # Test the bridge
    print("Testing Voice Workflow Bridge...")
    
    bridge = VoiceWorkflowBridge()
    
    # Test workflow detection
    test_commands = [
        "Hey AgentFlow, remember what I'm going to do now",
        "Send an email to John",
        "Open my Canvas class",
        "How are you doing today?",
        "Execute the workflow for closing tickets"
    ]
    
    for cmd in test_commands:
        is_workflow, cmd_type = bridge.is_workflow_command(cmd)
        print(f"'{cmd}' -> {is_workflow}, {cmd_type}")
    
    # Show available workflows
    workflows = bridge.get_available_workflows()
    print(f"\nAvailable workflows: {len(workflows)}")
    for wf in workflows[:3]:  # Show first 3
        print(f"  • {wf['name']}: {wf['description']}")
