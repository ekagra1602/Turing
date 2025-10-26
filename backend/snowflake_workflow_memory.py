"""
Working Snowflake integration with PASSWORD authentication
"""
import os
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

load_dotenv()


class SnowflakeWorkflowMemory:
    """Snowflake workflow storage - PASSWORD AUTH"""
    
    def __init__(self):
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError("pip install snowflake-connector-python")
        
        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.user = os.getenv('SNOWFLAKE_USER')
        self.password = os.getenv('SNOWFLAKE_PASSWORD')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
        self.database = os.getenv('SNOWFLAKE_DATABASE', 'AGENTFLOW_DB')
        self.schema = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
        self.role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
        
        if not self.password or self.password == 'PUT_YOUR_PASSWORD_HERE':
            raise ValueError("Set SNOWFLAKE_PASSWORD in .env file")
        
        self.conn = None
        self._connect()
        self._setup_database()
    
    def _connect(self):
        """Connect with password"""
        self.conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            role=self.role
        )
        print(f"✅ Connected to Snowflake: {self.database}")
    
    def _setup_database(self):
        """Setup database and tables"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE DATABASE {self.database}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            cursor.execute(f"USE SCHEMA {self.schema}")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id VARCHAR(100) PRIMARY KEY,
                    workflow_name VARCHAR(500) NOT NULL,
                    workflow_description TEXT,
                    semantic_actions TEXT,
                    parameters TEXT,
                    tags TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                    use_count INTEGER DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'ready',
                    steps_count INTEGER DEFAULT 0
                )
            """)
            print(f"✅ Database ready: {self.database}.{self.schema}")
        finally:
            cursor.close()
    
    def create_workflow(self, name: str, description: str = "", tags: List[str] = None) -> str:
        """Create new workflow"""
        workflow_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO workflows 
                (workflow_id, workflow_name, workflow_description, tags, status, steps_count, use_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (workflow_id, name, description, json.dumps(tags or []), 'recording', 0, 0))
            return workflow_id
        finally:
            cursor.close()
    
    def save_workflow(self, workflow_id: str, semantic_actions: List[Dict], 
                     parameters: List[str], steps_count: int = 0):
        """Save workflow data"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE workflows 
                SET semantic_actions = %s, parameters = %s, steps_count = %s, status = 'ready'
                WHERE workflow_id = %s
            """, (json.dumps(semantic_actions), json.dumps(parameters), steps_count, workflow_id))
        finally:
            cursor.close()
    
    def finalize_workflow(self, workflow_id: str, parameters: List[Dict] = None, 
                         semantic_actions: List[Dict] = None, steps_count: int = 0):
        """Finalize workflow - alias for save_workflow for compatibility"""
        if semantic_actions and parameters:
            # Convert parameters from dict format to list of names
            param_names = [p.get('name', '') for p in parameters] if isinstance(parameters[0], dict) else parameters
            self.save_workflow(workflow_id, semantic_actions, param_names, steps_count)
    
    def list_workflows(self, status: str = 'ready', tags: List[str] = None) -> List[Dict]:
        """List all workflows"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT workflow_id, workflow_name, workflow_description, 
                       parameters, steps_count, use_count, created
                FROM workflows 
                WHERE status = %s
                ORDER BY created DESC
            """, (status,))
            
            workflows = []
            for row in cursor:
                workflows.append({
                    'workflow_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'parameters': json.loads(row[3]) if row[3] else [],
                    'steps_count': row[4],
                    'use_count': row[5],
                    'created': str(row[6])
                })
            return workflows
        finally:
            cursor.close()
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT workflow_id, workflow_name, workflow_description,
                       semantic_actions, parameters, steps_count
                FROM workflows WHERE workflow_id = %s
            """, (workflow_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'workflow_id': row[0],
                'name': row[1],
                'description': row[2],
                'semantic_actions': json.loads(row[3]) if row[3] else [],
                'parameters': json.loads(row[4]) if row[4] else [],
                'steps_count': row[5]
            }
        finally:
            cursor.close()
    
    def increment_usage(self, workflow_id: str):
        """Increment usage count"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE workflows SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP()
                WHERE workflow_id = %s
            """, (workflow_id,))
        finally:
            cursor.close()
    
    def close(self):
        if self.conn:
            self.conn.close()


# Test
if __name__ == '__main__':
    print("Testing Snowflake connection...")
    memory = SnowflakeWorkflowMemory()
    workflows = memory.list_workflows()
    print(f"✅ Found {len(workflows)} workflows")
    memory.close()

