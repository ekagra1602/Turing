"""
Snowflake Database Examples

Complete examples showing how to use the database utilities.
Run this file with: python -m database.examples

Before running:
1. Add your Snowflake configuration below
2. Add authentication to client._get_headers() in client.py
"""

import json
from .client import SnowflakeAPIClient
from .operations import (
    create_table,
    insert_record,
    insert_records_batch,
    retrieve_records,
    update_records,
    delete_records
)


def run_examples():
    """Run all examples demonstrating database operations"""

    # ========================================
    # STEP 1: Initialize the client
    # ========================================
    # Create a client with your Snowflake configuration
    # You only need to do this once at the start of your program
    print("="*50)
    print("Initializing Snowflake client...")
    client = SnowflakeAPIClient(
        account='YOUR_ACCOUNT',           # e.g., 'xy12345.us-east-1'
        warehouse='YOUR_WAREHOUSE',       # e.g., 'COMPUTE_WH'
        database='YOUR_DATABASE',         # e.g., 'PRODUCTION'
        schema='YOUR_SCHEMA'              # e.g., 'PUBLIC'
    )
    print("✓ Client initialized")

    # ========================================
    # STEP 2: Create the workflow table
    # ========================================
    # This creates your first table to store workflow information
    # This table stores workflow metadata
    print("\n" + "="*50)
    print("Creating workflow table...")
    result = create_table(
        client,
        'workflow',
        {
            'workflow_id': 'VARCHAR(100)',
            'workflow_name': 'VARCHAR(200) NOT NULL',
            'workflow_description': 'TEXT',
            'workflow_video': 'VARCHAR(500)'
        },
        primary_key='workflow_id'
    )
    print("✓ Workflow table created")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 3: Create the steps table
    # ========================================
    # This table stores individual steps for each workflow
    # Note: It has a FOREIGN KEY to workflow table and UNIQUE constraint
    print("\n" + "="*50)
    print("Creating steps table...")
    steps_table_sql = """
    CREATE TABLE IF NOT EXISTS steps (
        step_id VARCHAR(100) PRIMARY KEY,
        step_description TEXT,
        step_number INTEGER NOT NULL,
        workflow_id VARCHAR(100) NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflow(workflow_id),
        UNIQUE (step_number, workflow_id)
    )
    """
    result = client.execute_statement(steps_table_sql)
    print("✓ Steps table created with foreign key and unique constraint")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 4: Insert a workflow
    # ========================================
    # Now let's add some data - first insert a workflow
    print("\n" + "="*50)
    print("Inserting a workflow record...")
    result = insert_record(
        client,
        'workflow',
        {
            'workflow_id': 'wf_001',
            'workflow_name': 'Open Canvas Class',
            'workflow_description': 'Workflow to open a specific class in Canvas',
            'workflow_video': 'https://example.com/videos/wf_001.mp4'
        }
    )
    print("✓ Workflow inserted")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 5: Insert steps (batch insert)
    # ========================================
    # Now insert multiple steps for this workflow in one go
    print("\n" + "="*50)
    print("Inserting steps for the workflow (batch insert)...")
    steps_data = [
        {
            'step_id': 'step_001',
            'step_description': 'Open browser',
            'step_number': 1,
            'workflow_id': 'wf_001'
        },
        {
            'step_id': 'step_002',
            'step_description': 'Navigate to Canvas',
            'step_number': 2,
            'workflow_id': 'wf_001'
        },
        {
            'step_id': 'step_003',
            'step_description': 'Click on class',
            'step_number': 3,
            'workflow_id': 'wf_001'
        }
    ]
    result = insert_records_batch(client, 'steps', steps_data)
    print("✓ 3 steps inserted at once")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 6: Query the data back
    # ========================================
    # Let's retrieve what we just inserted
    print("\n" + "="*50)
    print("Retrieving workflow data...")
    result = retrieve_records(
        client,
        'workflow',
        columns=['workflow_id', 'workflow_name', 'workflow_description'],
        where_clause="workflow_id = 'wf_001'"
    )
    print("✓ Workflow retrieved:")
    print(json.dumps(result, indent=2))

    print("\n" + "="*50)
    print("Retrieving steps for this workflow (ordered by step number)...")
    result = retrieve_records(
        client,
        'steps',
        columns=['step_id', 'step_number', 'step_description'],
        where_clause="workflow_id = 'wf_001'",
        order_by='step_number ASC'
    )
    print("✓ Steps retrieved in order:")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 7: Update a record
    # ========================================
    print("\n" + "="*50)
    print("Updating workflow description...")
    result = update_records(
        client,
        'workflow',
        {'workflow_description': 'Updated: Enhanced workflow for Canvas'},
        "workflow_id = 'wf_001'"
    )
    print("✓ Workflow updated")
    print(json.dumps(result, indent=2))

    # ========================================
    # STEP 8: Delete a record (commented out for safety)
    # ========================================
    # Uncomment to test deletion
    # print("\n" + "="*50)
    # print("Deleting a step...")
    # result = delete_records(
    #     client,
    #     'steps',
    #     "step_id = 'step_003'"
    # )
    # print("✓ Step deleted")
    # print(json.dumps(result, indent=2))

    # ========================================
    # DONE!
    # ========================================
    print("\n" + "="*50)
    print("✓ All examples completed successfully!")
    print("You now have 1 workflow with 3 steps in your Snowflake database.")


if __name__ == "__main__":
    run_examples()
