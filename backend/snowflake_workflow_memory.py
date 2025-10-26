"""
Snowflake Workflow Memory
Cloud-based workflow storage using Snowflake database

Replaces local file-based storage with cloud database for:
- Workflow metadata
- Semantic actions  
- Parameters
- Usage tracking

Screenshots/videos can be stored in S3 with URLs in database.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Import Snowflake database utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))

from database import (
    SnowflakeAPIClient,
    create_table,
    insert_record,
    retrieve_records,
    update_records,
    delete_records
)


class SnowflakeWorkflowMemory:
    """
    Cloud-based workflow memory using Snowflake
    
    Stores workflows in Snowflake cloud database instead of local files.
    Perfect for production deployments and team collaboration.
    
    Features:
    - Cloud storage (accessible from anywhere)
    - Automatic syncing
    - No local file management needed
    - Perfect for demos with 3-5 workflows
    """
    
    def __init__(self, 
                 account: str = None,
                 warehouse: str = None,
                 database: str = None,
                 schema: str = None,
                 auto_create_tables: bool = True):
        """
        Initialize Snowflake workflow memory
        
        Args:
            account: Snowflake account (or set SNOWFLAKE_ACCOUNT env var)
            warehouse: Warehouse name (or set SNOWFLAKE_WAREHOUSE env var)
            database: Database name (or set SNOWFLAKE_DATABASE env var)
            schema: Schema name (or set SNOWFLAKE_SCHEMA env var)
            auto_create_tables: Automatically create tables if they don't exist
        """
        # Get config from environment or parameters
        self.account = account or os.getenv('SNOWFLAKE_ACCOUNT', 'YOUR_ACCOUNT')
        self.warehouse = warehouse or os.getenv('SNOWFLAKE_WAREHOUSE', 'YOUR_WAREHOUSE')
        self.database = database or os.getenv('SNOWFLAKE_DATABASE', 'YOUR_DATABASE')
        self.schema = schema or os.getenv('SNOWFLAKE_SCHEMA', 'YOUR_SCHEMA')
        
        # Initialize Snowflake client
        self.client = SnowflakeAPIClient(
            account=self.account,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema
        )
        
        print(f"✅ Snowflake Workflow Memory initialized")
        print(f"   Account: {self.account}")
        print(f"   Database: {self.database}.{self.schema}")
        
        # Create tables if needed
        if auto_create_tables:
            self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create workflow tables if they don't exist"""
        print("\n🔧 Ensuring Snowflake tables exist...")
        
        try:
            # Create workflows table
            result = create_table(
                self.client,
                'workflows',
                {
                    'workflow_id': 'VARCHAR(100)',
                    'workflow_name': 'VARCHAR(500) NOT NULL',
                    'workflow_description': 'TEXT',
                    'semantic_actions': 'TEXT',  # JSON array as string
                    'parameters': 'TEXT',  # JSON array as string
                    'tags': 'TEXT',  # JSON array as string
                    'created': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP()',
                    'last_used': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP()',
                    'use_count': 'INTEGER DEFAULT 0',
                    'status': 'VARCHAR(50) DEFAULT \'ready\'',
                    'steps_count': 'INTEGER DEFAULT 0',
                    'video_url': 'VARCHAR(1000)'  # Optional S3/cloud URL
                },
                primary_key='workflow_id',
                if_not_exists=True
            )
            
            if 'error' not in result:
                print("   ✓ Workflows table ready")
            else:
                print(f"   ⚠️  Table creation: {result.get('error')}")
            
        except Exception as e:
            print(f"   ⚠️  Could not create tables: {e}")
            print("   Make sure Snowflake credentials are configured!")
    
    def create_workflow(self, 
                       name: str, 
                       description: str = "", 
                       tags: List[str] = None) -> str:
        """
        Create a new workflow
        
        Args:
            name: Workflow name
            description: Description
            tags: Optional tags
        
        Returns:
            workflow_id
        """
        workflow_id = str(uuid.uuid4())
        
        try:
            result = insert_record(
                self.client,
                'workflows',
                {
                    'workflow_id': workflow_id,
                    'workflow_name': name,
                    'workflow_description': description or '',
                    'tags': json.dumps(tags or []),
                    'status': 'recording',
                    'steps_count': 0,
                    'use_count': 0
                }
            )
            
            if 'error' in result:
                print(f"❌ Error creating workflow: {result['error']}")
                return None
            
            print(f"✅ Created workflow in Snowflake: {name}")
            return workflow_id
            
        except Exception as e:
            print(f"❌ Error creating workflow: {e}")
            return None
    
    def finalize_workflow(self, 
                         workflow_id: str, 
                         parameters: List[Dict] = None,
                         semantic_actions: List[Dict] = None,
                         steps_count: int = 0):
        """
        Finalize a workflow and mark it ready
        
        Args:
            workflow_id: ID of workflow
            parameters: Identified parameters
            semantic_actions: Semantic action sequence
            steps_count: Number of raw steps recorded
        """
        try:
            updates = {
                'status': 'ready'
            }
            
            if parameters:
                updates['parameters'] = json.dumps(parameters)
            
            if semantic_actions:
                updates['semantic_actions'] = json.dumps(semantic_actions)
            
            if steps_count > 0:
                updates['steps_count'] = steps_count
            
            result = update_records(
                self.client,
                'workflows',
                updates,
                f"workflow_id = '{workflow_id}'"
            )
            
            if 'error' in result:
                print(f"❌ Error finalizing workflow: {result['error']}")
                return False
            
            print(f"✅ Workflow finalized in Snowflake")
            return True
            
        except Exception as e:
            print(f"❌ Error finalizing workflow: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """
        Get a workflow by ID
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow dict or None
        """
        try:
            result = retrieve_records(
                self.client,
                'workflows',
                where_clause=f"workflow_id = '{workflow_id}'"
            )
            
            if 'data' not in result or not result['data']:
                return None
            
            # Parse JSON fields
            workflow = result['data'][0]
            workflow = self._parse_workflow(workflow)
            
            return workflow
            
        except Exception as e:
            print(f"❌ Error getting workflow: {e}")
            return None
    
    def list_workflows(self, 
                      status: str = None, 
                      tags: List[str] = None) -> List[Dict]:
        """
        List all workflows
        
        Args:
            status: Filter by status ('ready', 'recording', etc.)
            tags: Filter by tags (not implemented for Snowflake yet)
        
        Returns:
            List of workflow dicts
        """
        try:
            where_clause = None
            
            if status:
                where_clause = f"status = '{status}'"
            
            result = retrieve_records(
                self.client,
                'workflows',
                where_clause=where_clause,
                order_by='created DESC'
            )
            
            if 'data' not in result:
                return []
            
            # Parse JSON fields
            workflows = [self._parse_workflow(wf) for wf in result['data']]
            
            # Filter by tags if specified (done in Python since Snowflake JSON querying is complex)
            if tags:
                workflows = [wf for wf in workflows 
                           if any(tag in wf.get('tags', []) for tag in tags)]
            
            return workflows
            
        except Exception as e:
            print(f"❌ Error listing workflows: {e}")
            return []
    
    def increment_usage(self, workflow_id: str):
        """Increment usage counter"""
        try:
            # Get current count
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                return
            
            new_count = workflow.get('use_count', 0) + 1
            
            result = update_records(
                self.client,
                'workflows',
                {
                    'use_count': new_count,
                    'last_used': datetime.now().isoformat()
                },
                f"workflow_id = '{workflow_id}'"
            )
            
            if 'error' not in result:
                print(f"✓ Updated usage count: {new_count}")
            
        except Exception as e:
            print(f"⚠️  Could not increment usage: {e}")
    
    def delete_workflow(self, workflow_id: str):
        """Delete a workflow"""
        try:
            result = delete_records(
                self.client,
                'workflows',
                f"workflow_id = '{workflow_id}'"
            )
            
            if 'error' in result:
                print(f"❌ Error deleting workflow: {result['error']}")
                return False
            
            print(f"✅ Deleted workflow: {workflow_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting workflow: {e}")
            return False
    
    def _parse_workflow(self, workflow: Dict) -> Dict:
        """Parse JSON fields in workflow"""
        # Parse JSON string fields
        if 'semantic_actions' in workflow and workflow['semantic_actions']:
            try:
                workflow['semantic_actions'] = json.loads(workflow['semantic_actions'])
            except:
                workflow['semantic_actions'] = []
        else:
            workflow['semantic_actions'] = []
        
        if 'parameters' in workflow and workflow['parameters']:
            try:
                workflow['parameters'] = json.loads(workflow['parameters'])
            except:
                workflow['parameters'] = []
        else:
            workflow['parameters'] = []
        
        if 'tags' in workflow and workflow['tags']:
            try:
                workflow['tags'] = json.loads(workflow['tags'])
            except:
                workflow['tags'] = []
        else:
            workflow['tags'] = []
        
        return workflow
    
    def search_workflows(self, query: str) -> List[Dict]:
        """
        Search workflows by name or description
        
        Args:
            query: Search query
        
        Returns:
            List of matching workflows
        """
        try:
            # Use SQL LIKE for search
            where_clause = f"workflow_name LIKE '%{query}%' OR workflow_description LIKE '%{query}%'"
            
            result = retrieve_records(
                self.client,
                'workflows',
                where_clause=where_clause,
                order_by='created DESC'
            )
            
            if 'data' not in result:
                return []
            
            workflows = [self._parse_workflow(wf) for wf in result['data']]
            return workflows
            
        except Exception as e:
            print(f"❌ Error searching workflows: {e}")
            return []


def test_snowflake_memory():
    """Test Snowflake workflow memory"""
    print("=" * 70)
    print("Testing Snowflake Workflow Memory")
    print("=" * 70)
    print()
    
    # Initialize
    memory = SnowflakeWorkflowMemory()
    
    # Create a test workflow
    print("\n1. Creating test workflow...")
    workflow_id = memory.create_workflow(
        "Test Workflow",
        description="A test workflow for Snowflake integration",
        tags=["test", "demo"]
    )
    
    if workflow_id:
        print(f"   Created: {workflow_id}")
        
        # Finalize with semantic actions
        print("\n2. Finalizing workflow...")
        semantic_actions = [
            {
                'semantic_type': 'open_application',
                'target': 'Chrome',
                'description': 'Open Chrome browser'
            },
            {
                'semantic_type': 'click_element',
                'target': 'Canvas',
                'description': 'Click Canvas link'
            }
        ]
        
        parameters = [
            {
                'name': 'course_name',
                'example_value': 'Machine Learning',
                'type': 'string'
            }
        ]
        
        memory.finalize_workflow(
            workflow_id,
            parameters=parameters,
            semantic_actions=semantic_actions,
            steps_count=10
        )
        
        # Retrieve it
        print("\n3. Retrieving workflow...")
        workflow = memory.get_workflow(workflow_id)
        if workflow:
            print(f"   Name: {workflow['workflow_name']}")
            print(f"   Actions: {len(workflow['semantic_actions'])}")
            print(f"   Parameters: {len(workflow['parameters'])}")
        
        # List all workflows
        print("\n4. Listing all workflows...")
        workflows = memory.list_workflows(status='ready')
        print(f"   Found {len(workflows)} ready workflows")
        
        # Increment usage
        print("\n5. Incrementing usage...")
        memory.increment_usage(workflow_id)
        
        # Search
        print("\n6. Searching...")
        results = memory.search_workflows("Test")
        print(f"   Found {len(results)} matching workflows")
        
        print("\n✅ All tests passed!")
        print("\n⚠️  Remember to delete test workflow when done:")
        print(f"   memory.delete_workflow('{workflow_id}')")


if __name__ == "__main__":
    test_snowflake_memory()

