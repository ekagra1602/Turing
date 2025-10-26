#!/usr/bin/env python3
"""
AgentFlow VIDEO - Video-Based Learn-by-Observation System
Records screen video + events, processes with post-analysis for maximum accuracy
"""

import os
import sys
import time
import tkinter as tk
from pathlib import Path
from typing import Optional

from google import genai

from recording_overlay import RecordingOverlay
from recording_processor import RecordingProcessor
from visual_memory import VisualWorkflowMemory
from robust_executor import RobustWorkflowExecutor
from visual_analyzer import VisualAnalyzer
from enhanced_context_system import SemanticWorkflowMatcher, EnhancedContextExtractor


class AgentFlowVideo:
    """
    Video-based learning system with post-processing.
    
    Architecture:
    1. Record: GUI overlay → Video + Events
    2. Process: Post-analysis → Screenshots + OCR + Action Log
    3. Execute: Robust executor → Replay with new parameters
    
    This approach is far more robust than real-time processing because:
    - Can't miss actions (video has everything)
    - Can reprocess with better algorithms
    - Analysis doesn't slow down recording
    - Can manually review/edit if needed
    """
    
    def __init__(self):
        # Check API key
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("GOOGLE_API_KEY not set!")
        
        self.client = genai.Client()
        
        # Components
        self.memory = VisualWorkflowMemory()
        self.analyzer = VisualAnalyzer()
        self.processor = RecordingProcessor()
        self.executor = RobustWorkflowExecutor(analyzer=self.analyzer)
        
        # For workflow matching
        self.context_extractor = EnhancedContextExtractor(
            visual_analyzer=self.analyzer,
            use_embeddings=True
        )
        self.matcher = SemanticWorkflowMatcher(context_extractor=self.context_extractor)
        
        # GUI
        self.overlay: Optional[RecordingOverlay] = None
        
        # Stats
        self.stats = {
            'workflows_recorded': 0,
            'workflows_executed': 0,
            'total_steps_executed': 0
        }
        
        self._show_banner()
    
    def _show_banner(self):
        """Show startup banner"""
        print("\n" + "=" * 70)
        print("🎥 AgentFlow VIDEO - Learn by Observation")
        print("=" * 70)
        print()
        print("✨ Video-Based Recording System:")
        print("   ✓ Full screen recording at 30 FPS")
        print("   ✓ Precise event timestamping")
        print("   ✓ Post-processing with OCR + Vision")
        print("   ✓ Finite automata-style action logs")
        print("   ✓ Robust execution with retry")
        print()
        
        # Show existing workflows
        workflows = self.memory.list_workflows(status='ready')
        if workflows:
            print(f"📚 {len(workflows)} learned workflow(s) available")
        else:
            print("📚 No workflows yet - click START to record your first!")
        
        print("=" * 70)
    
    def start_recording_mode(self):
        """Start recording mode with GUI overlay"""
        print("\n" + "=" * 70)
        print("🎥 RECORDING MODE")
        print("=" * 70)
        print()
        print("A floating window will appear.")
        print("Click START to begin recording your workflow.")
        print("Perform your actions naturally.")
        print("Click STOP when done.")
        print()
        print("The system will then process your recording automatically.")
        print("=" * 70)
        print()
        
        # Create overlay
        self.overlay = RecordingOverlay()
        
        # Set callback for when recording completes
        self.overlay.on_recording_complete = self._on_recording_complete
        
        # Run overlay (blocking)
        try:
            self.overlay.run()
        except KeyboardInterrupt:
            print("\n\n👋 Recording cancelled")
    
    def _on_recording_complete(self, recording_id: str):
        """Called when recording stops - trigger processing"""
        print("\n" + "=" * 70)
        print("🔄 POST-PROCESSING")
        print("=" * 70)
        print()
        print("Processing your recording...")
        print("This may take a minute depending on length.")
        print()
        
        try:
            # Process recording
            workflow_id = self.processor.process_recording(
                recording_id=recording_id,
                show_progress=True
            )
            
            self.stats['workflows_recorded'] += 1
            
            print("\n" + "=" * 70)
            print("✅ WORKFLOW READY!")
            print("=" * 70)
            print()
            print(f"Your workflow is ready to use!")
            print(f"You can now execute it with different parameters.")
            print()
            
            # Show the workflow
            workflow = self.memory.get_workflow(workflow_id)
            print(f"📋 Workflow: {workflow['name']}")
            print(f"   Steps: {workflow['steps_count']}")
            print()
            
            # Reset overlay UI
            if self.overlay:
                self.overlay.reset_ui()
        
        except Exception as e:
            print(f"\n❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            
            if self.overlay:
                self.overlay.reset_ui()
    
    def list_workflows(self):
        """List all learned workflows"""
        workflows = self.memory.list_workflows(status='ready')
        
        if not workflows:
            print("\n📚 No learned workflows yet.")
            print("   Use recording mode to teach me a new workflow!")
            return
        
        print("\n" + "=" * 70)
        print("📚 LEARNED WORKFLOWS")
        print("=" * 70)
        
        for i, wf in enumerate(workflows, 1):
            print(f"\n{i}. {wf['name']}")
            print(f"   {wf.get('description', 'No description')}")
            print(f"   • Steps: {wf['steps_count']}")
            print(f"   • Used: {wf.get('use_count', 0)} times")
            
            if wf.get('tags'):
                print(f"   • Tags: {', '.join(wf['tags'])}")
        
        print("=" * 70)
    
    def execute_workflow_by_name(self, workflow_name: str, parameters: dict = None):
        """Execute a workflow by name"""
        workflows = self.memory.list_workflows(status='ready')
        
        # Find workflow
        matching = [w for w in workflows if w['name'].lower() == workflow_name.lower()]
        
        if not matching:
            print(f"❌ No workflow found: {workflow_name}")
            return False
        
        workflow = self.memory.get_workflow(matching[0]['workflow_id'])
        
        return self._execute_workflow(workflow, parameters or {})
    
    def execute_from_request(self, user_request: str):
        """Execute a workflow by matching user request"""
        print("\n" + "=" * 70)
        print(f"💭 REQUEST: {user_request}")
        print("=" * 70)
        
        # Try to match to learned workflow
        print("\n🔍 Searching for matching workflow...")
        
        workflows = self.memory.list_workflows(status='ready')
        
        if not workflows:
            print("\n❌ No workflows learned yet!")
            print("   Record a workflow first using recording mode.")
            return False
        
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
            
            # Confirm
            try:
                confirm = input("\n   Execute this workflow? [Y/n]: ").strip().lower()
                if confirm == 'n':
                    print("   Cancelled")
                    return False
            except EOFError:
                # Non-interactive mode
                pass
            
            return self._execute_workflow(workflow, params)
        else:
            print(f"\n❌ No matching workflow found")
            print(f"   Best match: {confidence:.0%} (threshold: 60%)")
            return False
    
    def _execute_workflow(self, workflow: dict, parameters: dict) -> bool:
        """Execute a workflow with parameters"""
        print("\n" + "=" * 70)
        print(f"🎬 EXECUTING WORKFLOW")
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
        
        # Execute
        success, results = self.executor.execute_workflow(
            workflow=workflow,
            parameters=parameters,
            verbose=True
        )
        
        # Update stats
        self.stats['workflows_executed'] += 1
        self.stats['total_steps_executed'] += len(results)
        
        # Update usage count
        if success:
            self.memory.increment_usage(workflow['workflow_id'])
        
        return success
    
    def show_stats(self):
        """Show system statistics"""
        print("\n" + "=" * 70)
        print("📊 STATISTICS")
        print("=" * 70)
        
        workflows = self.memory.list_workflows(status='ready')
        
        print(f"\n📚 Workflows:")
        print(f"   • Total learned: {len(workflows)}")
        print(f"   • Total recorded: {self.stats['workflows_recorded']}")
        print(f"   • Total executed: {self.stats['workflows_executed']}")
        
        print(f"\n⚙️  Execution:")
        print(f"   • Total steps executed: {self.stats['total_steps_executed']}")
        
        # Most used workflow
        if workflows:
            most_used = max(workflows, key=lambda w: w.get('use_count', 0))
            if most_used.get('use_count', 0) > 0:
                print(f"\n🏆 Most used workflow:")
                print(f"   • {most_used['name']}")
                print(f"   • Used {most_used['use_count']} times")
        
        print("=" * 70)
    
    def interactive_mode(self):
        """Interactive command-line mode"""
        print("\n" + "=" * 70)
        print("💬 INTERACTIVE MODE")
        print("=" * 70)
        print()
        print("Commands:")
        print("  • 'record' - Start recording mode (GUI)")
        print("  • 'list' - Show learned workflows")
        print("  • 'stats' - Show statistics")
        print("  • 'execute <workflow_name>' - Execute specific workflow")
        print("  • 'quit' or 'exit' - Exit")
        print()
        print("Or describe what you want:")
        print("  • 'Do X for my Y class'")
        print("=" * 70)
        
        while True:
            try:
                user_input = input("\n💬 ").strip()
                
                if not user_input:
                    continue
                
                cmd_lower = user_input.lower()
                
                if cmd_lower in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using AgentFlow VIDEO!")
                    break
                
                elif cmd_lower == 'record':
                    self.start_recording_mode()
                
                elif cmd_lower == 'list':
                    self.list_workflows()
                
                elif cmd_lower == 'stats':
                    self.show_stats()
                
                elif cmd_lower.startswith('execute '):
                    workflow_name = user_input[8:].strip()
                    self.execute_workflow_by_name(workflow_name)
                
                elif cmd_lower in ['help', 'h', '?']:
                    print("\nCommands: record, list, stats, execute <name>, quit")
                
                else:
                    # Try to match and execute
                    self.execute_from_request(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Use 'quit' to exit.")
            
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
        print("Set your Gemini API key:")
        print("  export GOOGLE_API_KEY='your_key_here'")
        print()
        sys.exit(1)
    
    try:
        agent = AgentFlowVideo()
        
        # Check command line args
        if len(sys.argv) > 1:
            if sys.argv[1] == 'record':
                agent.start_recording_mode()
            elif sys.argv[1] == 'list':
                agent.list_workflows()
            else:
                print(f"Unknown command: {sys.argv[1]}")
                print("Usage: python agent_video.py [record|list]")
        else:
            # Interactive mode
            agent.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

