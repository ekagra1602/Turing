#!/usr/bin/env python3
"""
AgentFlow PRO - Professional-Grade Learn-by-Observation System
The most advanced conversational computer control agent with true learning capabilities
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from google import genai

from agent_interface import AgentMemory
from visual_memory import VisualWorkflowMemory
from enhanced_recorder import EnhancedWorkflowRecorder
from enhanced_context_system import SemanticWorkflowMatcher, EnhancedContextExtractor
from robust_executor import RobustWorkflowExecutor
from visual_analyzer import VisualAnalyzer


class AgentFlowPro:
    """
    Professional-grade AI agent with learn-by-observation capabilities.
    
    This is the CalHacks demo-ready version with all advanced features:
    - 🎥 Rich visual context extraction during recording
    - 🧠 Semantic workflow matching with embeddings
    - 🎯 Real-time parameter detection
    - 🔄 Robust execution with retry and recovery
    - 📊 Detailed execution analytics
    """
    
    def __init__(self):
        # Check API key
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("GOOGLE_API_KEY not set. Export it first!")
        
        self.client = genai.Client()
        
        # Core components
        self.memory = AgentMemory()
        self.visual_memory = VisualWorkflowMemory()
        
        # Enhanced components
        self.analyzer = VisualAnalyzer(use_easyocr=True)
        self.context_extractor = EnhancedContextExtractor(
            visual_analyzer=self.analyzer,
            use_embeddings=True
        )
        self.recorder = EnhancedWorkflowRecorder(memory=self.visual_memory)
        self.executor = RobustWorkflowExecutor(analyzer=self.analyzer)
        self.matcher = SemanticWorkflowMatcher(context_extractor=self.context_extractor)
        
        # Statistics
        self.stats = {
            'workflows_recorded': 0,
            'workflows_executed': 0,
            'total_steps_executed': 0,
            'success_rate': 0.0
        }
        
        self._show_startup_banner()
    
    def _show_startup_banner(self):
        """Show impressive startup banner"""
        print("\n" + "=" * 70)
        print("🚀 AgentFlow PRO - Professional Edition")
        print("=" * 70)
        print()
        print("✨ Advanced Features Enabled:")
        print("   ✓ Visual context extraction with OCR")
        print("   ✓ Semantic workflow matching")
        print("   ✓ Real-time parameter detection")
        print("   ✓ Robust execution with retry logic")
        print("   ✓ Intelligent failure recovery")
        
        if self.context_extractor.use_embeddings:
            print("   ✓ Semantic embeddings for smart matching")
        
        print()
        
        # Show existing workflows
        workflows = self.visual_memory.list_workflows(status='ready')
        if workflows:
            print(f"📚 {len(workflows)} learned workflow(s) available")
        else:
            print("📚 No workflows learned yet - start by recording!")
        
        print("=" * 70)
    
    def record(self):
        """Start recording mode"""
        print("\n" + "=" * 70)
        print("🎥 RECORD NEW WORKFLOW")
        print("=" * 70)
        print()
        
        workflow_name = input("Workflow name: ").strip()
        if not workflow_name:
            print("❌ Name required!")
            return
        
        description = input("Description: ").strip()
        
        tags_input = input("Tags (comma-separated): ").strip()
        tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
        
        print()
        input("Press Enter when ready to start recording...")
        
        workflow_id = self.recorder.start_recording(
            workflow_name=workflow_name,
            description=description,
            tags=tags
        )
        
        self.stats['workflows_recorded'] += 1
        return workflow_id
    
    def stop_recording(self):
        """Stop current recording"""
        workflow_id = self.recorder.stop_recording()
        
        if workflow_id:
            print(f"\n✅ Workflow saved! ID: {workflow_id}")
        
        return workflow_id
    
    def list_workflows(self):
        """List all learned workflows"""
        workflows = self.visual_memory.list_workflows(status='ready')
        
        if not workflows:
            print("\n📚 No learned workflows yet.")
            print("   Use 'record' to teach me a new workflow!")
            return
        
        print("\n" + "=" * 70)
        print("📚 LEARNED WORKFLOWS")
        print("=" * 70)
        
        for i, wf in enumerate(workflows, 1):
            print(f"\n{i}. {wf['name']}")
            print(f"   {wf.get('description', 'No description')}")
            print(f"   • Steps: {wf['steps_count']}")
            print(f"   • Used: {wf.get('use_count', 0)} times")
            
            if wf.get('parameters'):
                param_names = [p['name'] for p in wf['parameters']]
                print(f"   • Parameters: {', '.join(param_names)}")
            
            if wf.get('tags'):
                print(f"   • Tags: {', '.join(wf['tags'])}")
        
        print("=" * 70)
    
    def execute_request(self, user_request: str):
        """
        Execute a user request by matching to learned workflow or falling back to AI.
        """
        print("\n" + "=" * 70)
        print(f"💭 REQUEST: {user_request}")
        print("=" * 70)
        
        # Try to match to learned workflow
        print("\n🔍 Searching for matching workflow...")
        
        workflows = self.visual_memory.list_workflows(status='ready')
        
        if workflows:
            workflow, confidence, params = self.matcher.find_best_match(
                user_request=user_request,
                workflows=workflows,
                threshold=0.6
            )
            
            if workflow and confidence > 0.6:
                print(f"\n✨ MATCH FOUND!")
                print(f"   Workflow: {workflow['name']}")
                print(f"   Confidence: {confidence:.0%}")
                
                if params:
                    print(f"   Parameters:")
                    for k, v in params.items():
                        print(f"      • {k} = {v}")
                
                # Confirm with user
                confirm = input("\n   Execute this workflow? [Y/n]: ").strip().lower()
                
                if confirm != 'n':
                    return self._execute_learned_workflow(workflow, params)
                else:
                    print("   Execution cancelled.")
                    return False
            else:
                print(f"   No confident match (best: {confidence:.0%})")
        
        # Fallback to AI execution
        print("\n🤖 No matching workflow found.")
        print("   Using AI direct execution mode...")
        
        return self._execute_with_ai(user_request)
    
    def _execute_learned_workflow(self,
                                  workflow: Dict,
                                  parameters: Dict) -> bool:
        """
        Execute a learned workflow with robust execution engine.
        """
        print("\n" + "=" * 70)
        print(f"🎬 EXECUTING LEARNED WORKFLOW")
        print("=" * 70)
        print(f"\nWorkflow: {workflow['name']}")
        print(f"Steps: {workflow['steps_count']}")
        
        if parameters:
            print("\nParameters:")
            for k, v in parameters.items():
                print(f"  • {k} = {v}")
        
        # Countdown
        print("\n⚠️  Starting execution in 3 seconds...")
        print("DON'T TOUCH YOUR MOUSE OR KEYBOARD!")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🤖 AI is now controlling your screen...")
        print("=" * 70)
        
        # Execute with robust executor
        success, results = self.executor.execute_workflow(
            workflow=workflow,
            parameters=parameters,
            verbose=True
        )
        
        # Update stats
        self.stats['workflows_executed'] += 1
        self.stats['total_steps_executed'] += len(results)
        
        successful_steps = sum(1 for r in results if r.status.value == 'success')
        if results:
            self.stats['success_rate'] = successful_steps / len(results)
        
        # Update usage count
        if success:
            self.visual_memory.increment_usage(workflow['workflow_id'])
        
        return success
    
    def _execute_with_ai(self, user_request: str) -> bool:
        """
        Fallback to direct AI execution (from original agent_interface).
        """
        from computer_use_simple import execute_computer_task
        
        try:
            # Plan the task
            print("\n🧠 Planning...")
            
            plan_prompt = f"""
You are a computer control AI assistant.

User request: "{user_request}"

Based on this request, plan the execution:
- What application should be used?
- What URL (if browser)?
- What are the high-level steps?

Respond in this format:
APPLICATION: [name or "Already Open"]
URL: [url or "N/A"]
WORKFLOW: [brief description]
INSTRUCTIONS:
1. Step 1
2. Step 2
...
PARAMETERS:
param1: value1
"""
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=plan_prompt
            )
            
            plan = response.text
            print(f"\nPlan:\n{plan}\n")
            
            # Countdown
            print("=" * 70)
            print("🚀 AUTO-STARTING IN 5 SECONDS...")
            print("=" * 70)
            print("DON'T TOUCH YOUR MOUSE OR KEYBOARD!")
            print("The AI will take control automatically...")
            print()
            
            for i in range(5, 0, -1):
                print(f"   Starting in {i}...")
                time.sleep(1)
            
            print()
            print("=" * 70)
            print("🤖 AI IS NOW CONTROLLING YOUR SCREEN!")
            print("=" * 70)
            print("Watch the mouse move automatically...")
            print("Press Ctrl+C at any time to stop")
            print("=" * 70)
            print()
            
            # Execute
            result = execute_computer_task(user_request, plan)
            
            if result:
                print("\n" + "=" * 70)
                print("✅ TASK COMPLETED")
                print("=" * 70)
                print(result)
                print("=" * 70)
                return True
            else:
                return False
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def show_stats(self):
        """Show system statistics"""
        print("\n" + "=" * 70)
        print("📊 AGENTFLOW PRO STATISTICS")
        print("=" * 70)
        
        workflows = self.visual_memory.list_workflows(status='ready')
        
        print(f"\n📚 Workflows:")
        print(f"   • Total learned: {len(workflows)}")
        print(f"   • Total recorded: {self.stats['workflows_recorded']}")
        print(f"   • Total executed: {self.stats['workflows_executed']}")
        
        print(f"\n⚙️  Execution:")
        print(f"   • Total steps executed: {self.stats['total_steps_executed']}")
        if self.stats['success_rate'] > 0:
            print(f"   • Success rate: {self.stats['success_rate']:.0%}")
        
        # Most used workflow
        if workflows:
            most_used = max(workflows, key=lambda w: w.get('use_count', 0))
            if most_used.get('use_count', 0) > 0:
                print(f"\n🏆 Most used workflow:")
                print(f"   • {most_used['name']}")
                print(f"   • Used {most_used['use_count']} times")
        
        print("=" * 70)
    
    def interactive_loop(self):
        """Main interactive loop"""
        print("\n" + "=" * 70)
        print("💬 INTERACTIVE MODE")
        print("=" * 70)
        print()
        print("Commands:")
        print("  • 'record' - Record a new workflow")
        print("  • 'stop' - Stop recording")
        print("  • 'list' - Show learned workflows")
        print("  • 'stats' - Show statistics")
        print("  • 'quit' or 'exit' - Exit")
        print()
        print("Or just describe what you want to do:")
        print("  • 'Open my DataVis class on Canvas'")
        print("  • 'Check my calendar'")
        print("  • 'Download the lecture notes'")
        print("=" * 70)
        
        while True:
            try:
                user_input = input("\n💬 ").strip()
                
                if not user_input:
                    continue
                
                # Commands
                cmd_lower = user_input.lower()
                
                if cmd_lower in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using AgentFlow PRO!")
                    break
                
                elif cmd_lower == 'record':
                    self.record()
                
                elif cmd_lower == 'stop':
                    self.stop_recording()
                
                elif cmd_lower == 'list':
                    self.list_workflows()
                
                elif cmd_lower == 'stats':
                    self.show_stats()
                
                elif cmd_lower in ['help', 'h', '?']:
                    print("\nCommands: record, stop, list, stats, quit")
                    print("Or just tell me what to do!")
                
                else:
                    # Execute request
                    self.execute_request(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Use 'quit' to exit properly.")
            
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Main entry point"""
    
    # Check API key
    if "GOOGLE_API_KEY" not in os.environ:
        print("=" * 70)
        print("❌ ERROR: GOOGLE_API_KEY not set")
        print("=" * 70)
        print()
        print("To use AgentFlow PRO, you need a Google Gemini API key.")
        print()
        print("Get one at: https://makersuite.google.com/app/apikey")
        print()
        print("Then set it:")
        print("  export GOOGLE_API_KEY='your_key_here'")
        print()
        sys.exit(1)
    
    try:
        agent = AgentFlowPro()
        agent.interactive_loop()
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

