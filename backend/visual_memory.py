"""
Visual Memory System for AgentFlow
Stores workflows with visual context, screenshots, and action sequences
"""

import json
import time
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from PIL import Image
import io


class VisualWorkflowMemory:
    """
    Enhanced memory system that stores workflows with complete visual context.
    Each workflow includes:
    - Action sequence
    - Screenshots before/after each action
    - Visual signatures of clicked elements
    - OCR text extraction
    - Parameters and generalization metadata
    """
    
    def __init__(self, storage_dir: Path = None):
        if storage_dir is None:
            storage_dir = Path(__file__).parent / "workflows"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Index file for quick lookup
        self.index_file = self.storage_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load workflow index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load index: {e}")
        
        return {
            'workflows': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_index(self):
        """Save workflow index to disk."""
        self.index['last_updated'] = datetime.now().isoformat()
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def create_workflow(self, name: str, description: str, tags: List[str] = None) -> str:
        """
        Create a new workflow recording.
        
        Returns:
            workflow_id: Unique identifier for this workflow
        """
        workflow_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create workflow directory
        workflow_dir = self.storage_dir / workflow_id
        workflow_dir.mkdir(exist_ok=True)
        (workflow_dir / "steps").mkdir(exist_ok=True)
        
        # Create metadata
        metadata = {
            'workflow_id': workflow_id,
            'name': name,
            'description': description,
            'tags': tags or [],
            'created': timestamp,
            'last_used': timestamp,
            'use_count': 0,
            'status': 'recording',
            'steps_count': 0
        }
        
        # Save metadata
        with open(workflow_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Add to index
        self.index['workflows'][workflow_id] = {
            'name': name,
            'description': description,
            'tags': tags or [],
            'created': timestamp,
            'path': str(workflow_dir)
        }
        self._save_index()
        
        print(f"✅ Created workflow: {name} (ID: {workflow_id})")
        return workflow_id
    
    def add_step(self, 
                 workflow_id: str,
                 action_type: str,
                 action_data: Dict[str, Any],
                 screenshot_before: Image.Image = None,
                 screenshot_after: Image.Image = None,
                 visual_context: Dict[str, Any] = None):
        """
        Add a step to a workflow recording.
        
        Args:
            workflow_id: ID of workflow to add to
            action_type: Type of action (click, type, scroll, etc.)
            action_data: Action-specific data (coordinates, text, etc.)
            screenshot_before: Screenshot before action
            screenshot_after: Screenshot after action
            visual_context: Additional visual data (OCR, element crops, etc.)
        """
        workflow_dir = self.storage_dir / workflow_id
        if not workflow_dir.exists():
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Load metadata
        with open(workflow_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Step number
        step_num = metadata['steps_count'] + 1
        step_id = f"step_{step_num:03d}"
        
        # Create step data
        step_data = {
            'step_id': step_id,
            'step_number': step_num,
            'timestamp': time.time(),
            'action_type': action_type,
            'action_data': action_data,
            'visual_context': visual_context or {}
        }
        
        # Save screenshots
        if screenshot_before:
            before_path = workflow_dir / "steps" / f"{step_id}_before.png"
            screenshot_before.save(before_path)
            step_data['screenshot_before'] = str(before_path.name)
        
        if screenshot_after:
            after_path = workflow_dir / "steps" / f"{step_id}_after.png"
            screenshot_after.save(after_path)
            step_data['screenshot_after'] = str(after_path.name)
        
        # Save step data
        step_file = workflow_dir / "steps" / f"{step_id}.json"
        with open(step_file, 'w') as f:
            json.dump(step_data, f, indent=2)
        
        # Update metadata
        metadata['steps_count'] = step_num
        with open(workflow_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  ✓ Added step {step_num}: {action_type}")
    
    def finalize_workflow(self, workflow_id: str, parameters: List[Dict] = None):
        """
        Finalize a workflow recording and mark it ready for use.
        
        Args:
            workflow_id: ID of workflow to finalize
            parameters: List of identified parameters (name, type, location, etc.)
        """
        workflow_dir = self.storage_dir / workflow_id
        
        # Load metadata
        with open(workflow_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Update status
        metadata['status'] = 'ready'
        metadata['finalized'] = datetime.now().isoformat()
        
        # Add parameters if provided
        if parameters:
            metadata['parameters'] = parameters
        
        # Save updated metadata
        with open(workflow_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Workflow finalized: {metadata['name']}")
        return metadata
    
    def get_workflow(self, workflow_id: str) -> Dict:
        """Load complete workflow data."""
        workflow_dir = self.storage_dir / workflow_id
        
        if not workflow_dir.exists():
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Load metadata
        with open(workflow_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Load all steps
        steps = []
        for i in range(1, metadata['steps_count'] + 1):
            step_file = workflow_dir / "steps" / f"step_{i:03d}.json"
            if step_file.exists():
                with open(step_file, 'r') as f:
                    steps.append(json.load(f))
        
        metadata['steps'] = steps
        return metadata
    
    def list_workflows(self, tags: List[str] = None, status: str = None) -> List[Dict]:
        """
        List all workflows, optionally filtered.
        
        Args:
            tags: Filter by tags
            status: Filter by status (recording, ready, etc.)
        
        Returns:
            List of workflow metadata
        """
        workflows = []
        
        for workflow_id, info in self.index['workflows'].items():
            # Filter by tags
            if tags and not any(tag in info.get('tags', []) for tag in tags):
                continue
            
            # Load full metadata for status check
            workflow_dir = self.storage_dir / workflow_id
            metadata_file = workflow_dir / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Filter by status
                if status and metadata.get('status') != status:
                    continue
                
                workflows.append(metadata)
        
        # Sort by created date
        workflows.sort(key=lambda x: x['created'], reverse=True)
        return workflows
    
    def search_workflows(self, query: str) -> List[Dict]:
        """
        Search workflows by name, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            List of matching workflows
        """
        query_lower = query.lower()
        matches = []
        
        for workflow in self.list_workflows():
            # Search in name
            if query_lower in workflow['name'].lower():
                matches.append((workflow, 1.0))
                continue
            
            # Search in description
            if query_lower in workflow.get('description', '').lower():
                matches.append((workflow, 0.8))
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in workflow.get('tags', [])):
                matches.append((workflow, 0.6))
        
        # Sort by relevance
        matches.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in matches]
    
    def increment_usage(self, workflow_id: str):
        """Increment usage counter for a workflow."""
        workflow_dir = self.storage_dir / workflow_id
        metadata_file = workflow_dir / "metadata.json"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metadata['use_count'] = metadata.get('use_count', 0) + 1
        metadata['last_used'] = datetime.now().isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def delete_workflow(self, workflow_id: str):
        """Delete a workflow and all its data."""
        import shutil
        
        workflow_dir = self.storage_dir / workflow_id
        if workflow_dir.exists():
            shutil.rmtree(workflow_dir)
        
        if workflow_id in self.index['workflows']:
            del self.index['workflows'][workflow_id]
            self._save_index()
        
        print(f"✅ Deleted workflow: {workflow_id}")
    
    def export_workflow(self, workflow_id: str, output_path: Path):
        """Export workflow as a portable package."""
        import zipfile
        
        workflow_dir = self.storage_dir / workflow_id
        
        with zipfile.ZipFile(output_path, 'w') as zipf:
            for file in workflow_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(workflow_dir)
                    zipf.write(file, arcname)
        
        print(f"✅ Exported workflow to: {output_path}")
    
    def import_workflow(self, zip_path: Path) -> str:
        """Import a workflow from an exported package."""
        import zipfile
        
        # Generate new workflow ID
        workflow_id = str(uuid.uuid4())
        workflow_dir = self.storage_dir / workflow_id
        workflow_dir.mkdir(exist_ok=True)
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(workflow_dir)
        
        # Load metadata and add to index
        with open(workflow_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        metadata['workflow_id'] = workflow_id  # Update ID
        
        with open(workflow_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.index['workflows'][workflow_id] = {
            'name': metadata['name'],
            'description': metadata['description'],
            'tags': metadata.get('tags', []),
            'created': metadata['created'],
            'path': str(workflow_dir)
        }
        self._save_index()
        
        print(f"✅ Imported workflow: {metadata['name']} (ID: {workflow_id})")
        return workflow_id


def test_visual_memory():
    """Test the visual memory system."""
    print("=" * 70)
    print("Testing Visual Workflow Memory")
    print("=" * 70)
    
    memory = VisualWorkflowMemory()
    
    # Create a test workflow
    workflow_id = memory.create_workflow(
        name="Open Canvas Class",
        description="Navigate to Canvas and open a specific class",
        tags=["canvas", "education", "navigation"]
    )
    
    # Simulate recording steps
    print("\nRecording steps...")
    
    # Step 1: Navigate
    memory.add_step(
        workflow_id=workflow_id,
        action_type="navigate",
        action_data={
            "url": "https://canvas.asu.edu",
            "method": "browser"
        },
        visual_context={
            "description": "Navigate to Canvas homepage"
        }
    )
    
    # Step 2: Click class
    memory.add_step(
        workflow_id=workflow_id,
        action_type="click",
        action_data={
            "x": 500,
            "y": 300,
            "normalized_x": 340,
            "normalized_y": 314
        },
        visual_context={
            "clicked_text": "Machine Learning",
            "element_type": "link",
            "ocr_confidence": 0.95
        }
    )
    
    # Finalize
    memory.finalize_workflow(
        workflow_id=workflow_id,
        parameters=[
            {
                "name": "class_name",
                "type": "string",
                "example": "Machine Learning",
                "location": "step_2",
                "description": "Name of the class to open"
            }
        ]
    )
    
    # List workflows
    print("\nAll workflows:")
    workflows = memory.list_workflows()
    for wf in workflows:
        print(f"  - {wf['name']} ({wf['steps_count']} steps)")
    
    # Load workflow
    print("\nLoading workflow...")
    loaded = memory.get_workflow(workflow_id)
    print(f"  Name: {loaded['name']}")
    print(f"  Steps: {len(loaded['steps'])}")
    for step in loaded['steps']:
        print(f"    {step['step_number']}. {step['action_type']}")
    
    print("\n✅ Visual memory system working!")


if __name__ == "__main__":
    test_visual_memory()

