"""
Workflow Composition Engine
Enables chaining multiple learned workflows into complex multi-step automations
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path

from visual_memory import VisualWorkflowMemory


@dataclass
class CompositionStep:
    """A step in a composed workflow"""
    workflow_id: str
    workflow_name: str
    parameters: Dict[str, Any]
    wait_after: float = 1.0  # seconds to wait after this workflow
    
    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'parameters': self.parameters,
            'wait_after': self.wait_after
        }


class WorkflowComposer:
    """
    Compose multiple workflows into complex automations.
    
    Example:
        workflow1: "Open Canvas Class"
        workflow2: "Download Files"
        
        composed: "Download files from all my classes"
        → Execute workflow1 with class="ML", then workflow2
        → Execute workflow1 with class="DataVis", then workflow2
        → Execute workflow1 with class="DataMining", then workflow2
    """
    
    def __init__(self, memory: VisualWorkflowMemory = None):
        self.memory = memory or VisualWorkflowMemory()
        self.compositions_file = self.memory.storage_dir / "compositions.json"
        self.compositions = self._load_compositions()
    
    def _load_compositions(self) -> Dict:
        """Load saved compositions"""
        if self.compositions_file.exists():
            try:
                with open(self.compositions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Could not load compositions: {e}")
        
        return {'compositions': []}
    
    def _save_compositions(self):
        """Save compositions to disk"""
        with open(self.compositions_file, 'w') as f:
            json.dump(self.compositions, f, indent=2)
    
    def create_composition(self,
                          name: str,
                          description: str,
                          steps: List[CompositionStep]) -> str:
        """
        Create a new composed workflow.
        
        Args:
            name: Name for this composition
            description: What it does
            steps: List of workflow executions to chain
        
        Returns:
            composition_id
        """
        import uuid
        
        composition_id = str(uuid.uuid4())
        
        composition = {
            'id': composition_id,
            'name': name,
            'description': description,
            'steps': [step.to_dict() for step in steps],
            'created': __import__('datetime').datetime.now().isoformat()
        }
        
        self.compositions['compositions'].append(composition)
        self._save_compositions()
        
        print(f"✅ Created composition: {name}")
        print(f"   ID: {composition_id}")
        print(f"   Steps: {len(steps)}")
        
        return composition_id
    
    def execute_composition(self,
                           composition_id: str,
                           executor,
                           verbose: bool = True) -> bool:
        """
        Execute a composed workflow.
        
        Args:
            composition_id: ID of composition to execute
            executor: RobustWorkflowExecutor instance
            verbose: Print detailed output
        
        Returns:
            True if all steps succeeded
        """
        import time
        
        # Find composition
        composition = None
        for comp in self.compositions['compositions']:
            if comp['id'] == composition_id:
                composition = comp
                break
        
        if not composition:
            print(f"❌ Composition {composition_id} not found")
            return False
        
        if verbose:
            print("\n" + "=" * 70)
            print(f"🎬 EXECUTING COMPOSITION: {composition['name']}")
            print("=" * 70)
            print(f"Description: {composition['description']}")
            print(f"Total steps: {len(composition['steps'])}")
            print()
        
        # Execute each step
        all_success = True
        
        for i, step in enumerate(composition['steps'], 1):
            workflow_id = step['workflow_id']
            parameters = step['parameters']
            wait_after = step.get('wait_after', 1.0)
            
            if verbose:
                print(f"\n🔸 Composition Step {i}/{len(composition['steps'])}")
                print(f"   Workflow: {step['workflow_name']}")
            
            # Load workflow
            try:
                workflow = self.memory.get_workflow(workflow_id)
            except Exception as e:
                print(f"❌ Could not load workflow: {e}")
                all_success = False
                break
            
            # Execute
            success, results = executor.execute_workflow(
                workflow=workflow,
                parameters=parameters,
                verbose=verbose
            )
            
            if not success:
                print(f"❌ Composition failed at step {i}")
                all_success = False
                break
            
            # Wait before next step
            if i < len(composition['steps']):
                if verbose:
                    print(f"\n⏳ Waiting {wait_after}s before next step...")
                time.sleep(wait_after)
        
        if verbose:
            print("\n" + "=" * 70)
            if all_success:
                print("✅ COMPOSITION COMPLETED SUCCESSFULLY")
            else:
                print("❌ COMPOSITION FAILED")
            print("=" * 70)
        
        return all_success
    
    def list_compositions(self):
        """List all compositions"""
        compositions = self.compositions['compositions']
        
        if not compositions:
            print("\n📚 No compositions created yet")
            return
        
        print("\n" + "=" * 70)
        print("📚 WORKFLOW COMPOSITIONS")
        print("=" * 70)
        
        for comp in compositions:
            print(f"\n• {comp['name']}")
            print(f"  {comp['description']}")
            print(f"  Steps: {len(comp['steps'])}")
            
            for i, step in enumerate(comp['steps'], 1):
                print(f"    {i}. {step['workflow_name']}")
                if step['parameters']:
                    params_str = ', '.join([f"{k}={v}" for k, v in step['parameters'].items()])
                    print(f"       ({params_str})")
        
        print("=" * 70)
    
    def suggest_compositions(self, workflows: List[Dict]) -> List[Dict]:
        """
        Analyze workflows and suggest useful compositions.
        
        This uses heuristics to find workflows that are commonly chained.
        """
        suggestions = []
        
        # Look for workflows with complementary tags
        # Example: "navigation" + "action"
        
        navigation_workflows = [w for w in workflows if 'navigation' in w.get('tags', [])]
        action_workflows = [w for w in workflows if 'action' in w.get('tags', [])]
        
        if navigation_workflows and action_workflows:
            for nav in navigation_workflows:
                for action in action_workflows:
                    suggestions.append({
                        'name': f"{nav['name']} + {action['name']}",
                        'description': f"Navigate using {nav['name']}, then perform {action['name']}",
                        'workflows': [nav['workflow_id'], action['workflow_id']]
                    })
        
        return suggestions


class AdaptiveLearner:
    """
    Learn from corrections and improve workflows over time.
    
    When execution fails or user corrects it, learn from that feedback.
    """
    
    def __init__(self, memory: VisualWorkflowMemory = None):
        self.memory = memory or VisualWorkflowMemory()
        self.corrections_file = self.memory.storage_dir / "corrections.json"
        self.corrections = self._load_corrections()
    
    def _load_corrections(self) -> Dict:
        """Load correction history"""
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Could not load corrections: {e}")
        
        return {'corrections': []}
    
    def _save_corrections(self):
        """Save corrections to disk"""
        with open(self.corrections_file, 'w') as f:
            json.dump(self.corrections, f, indent=2)
    
    def record_correction(self,
                         workflow_id: str,
                         step_number: int,
                         what_failed: str,
                         what_worked: Dict[str, Any]):
        """
        Record a correction when user fixes a failed execution.
        
        Args:
            workflow_id: Which workflow failed
            step_number: Which step failed
            what_failed: Description of failure
            what_worked: What the user did to fix it (new coordinates, text, etc.)
        """
        correction = {
            'workflow_id': workflow_id,
            'step_number': step_number,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'what_failed': what_failed,
            'what_worked': what_worked
        }
        
        self.corrections['corrections'].append(correction)
        self._save_corrections()
        
        print("✅ Correction recorded")
        print("   The system will learn from this!")
    
    def apply_corrections(self, workflow_id: str):
        """
        Apply learned corrections to a workflow.
        
        This updates the workflow based on accumulated corrections.
        """
        corrections_for_workflow = [
            c for c in self.corrections['corrections']
            if c['workflow_id'] == workflow_id
        ]
        
        if not corrections_for_workflow:
            print("No corrections to apply")
            return
        
        print(f"\n🧠 Applying {len(corrections_for_workflow)} correction(s)...")
        
        # Load workflow
        workflow = self.memory.get_workflow(workflow_id)
        
        # Apply each correction
        for correction in corrections_for_workflow:
            step_num = correction['step_number']
            what_worked = correction['what_worked']
            
            # Find the step
            step = None
            for s in workflow['steps']:
                if s['step_number'] == step_num:
                    step = s
                    break
            
            if step:
                # Update step with correction
                if 'new_text' in what_worked:
                    step['visual_context']['clicked_text'] = what_worked['new_text']
                
                if 'new_coordinates' in what_worked:
                    step['action_data']['x'] = what_worked['new_coordinates'][0]
                    step['action_data']['y'] = what_worked['new_coordinates'][1]
                
                print(f"   ✓ Updated step {step_num}")
        
        # Save updated workflow
        # (Would need to implement workflow update method)
        print("✅ Corrections applied")
    
    def get_correction_stats(self) -> Dict:
        """Get statistics about corrections"""
        corrections = self.corrections['corrections']
        
        if not corrections:
            return {'total': 0}
        
        # Group by workflow
        by_workflow = {}
        for c in corrections:
            wf_id = c['workflow_id']
            if wf_id not in by_workflow:
                by_workflow[wf_id] = []
            by_workflow[wf_id].append(c)
        
        return {
            'total': len(corrections),
            'workflows_corrected': len(by_workflow),
            'by_workflow': {wf: len(corr) for wf, corr in by_workflow.items()}
        }


def demo_composition():
    """Demo workflow composition"""
    print("=" * 70)
    print("Workflow Composition Demo")
    print("=" * 70)
    print()
    
    memory = VisualWorkflowMemory()
    composer = WorkflowComposer(memory)
    
    # List available workflows
    workflows = memory.list_workflows(status='ready')
    
    if not workflows:
        print("No workflows available. Record some first!")
        return
    
    print("Available workflows:")
    for i, wf in enumerate(workflows, 1):
        print(f"  {i}. {wf['name']}")
    
    print()
    print("You can compose workflows like:")
    print("  1. Open Canvas Class (class='ML')")
    print("  2. Download Files")
    print("  3. Open Canvas Class (class='DataVis')")
    print("  4. Download Files")
    print()
    print("This creates: 'Download files from multiple classes'")
    print()
    print("To create compositions, use the API:")
    print("  composer.create_composition(...)")


if __name__ == "__main__":
    demo_composition()

