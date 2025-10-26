"""
Snowflake CRUD Operations

Convenience functions for common database operations:
- create_table: Create tables
- insert_record: Insert single records
- insert_records_batch: Insert multiple records at once
- retrieve_records: Query/SELECT data
- update_records: Update existing records
- delete_records: Delete records
"""

from typing import Dict, List, Any, Optional
from .client import SnowflakeAPIClient
from .helpers import infer_type, format_value


def create_table(
    client: SnowflakeAPIClient,
    table_name: str,
    columns: Dict[str, str],
    primary_key: Optional[str] = None,
    if_not_exists: bool = True
) -> Dict[str, Any]:
    """
    Create a table in Snowflake

    Convenience function to create a table without writing raw SQL.
    Pass in column names and types as a dictionary.

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to create (e.g., 'users', 'workflow', 'steps')
        columns: Dict mapping column names to data types
                 Format: {'column_name': 'DATA_TYPE CONSTRAINTS'}
        primary_key: Column name to use as primary key (optional)
        if_not_exists: If True, adds IF NOT EXISTS (won't error if table exists)

    Returns:
        Dict containing execution results (check for 'error' key if failed)

    Example 1 - Simple table:
        result = create_table(
            client,
            'users',
            {
                'id': 'VARCHAR(100)',
                'name': 'VARCHAR(200)',
                'email': 'VARCHAR(200)'
            },
            primary_key='id'
        )

    Example 2 - Table with defaults and constraints:
        result = create_table(
            client,
            'logs',
            {
                'log_id': 'NUMBER AUTOINCREMENT',
                'message': 'TEXT NOT NULL',
                'level': 'VARCHAR(20) DEFAULT \'INFO\'',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP()'
            },
            primary_key='log_id'
        )

    Example 3 - Your workflow table:
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
    """
    # Build column definitions
    column_defs = [f"{col} {dtype}" for col, dtype in columns.items()]

    # Add primary key constraint if specified
    if primary_key:
        column_defs.append(f"PRIMARY KEY ({primary_key})")

    # Construct SQL
    exists_clause = "IF NOT EXISTS " if if_not_exists else ""
    sql = f"""
    CREATE TABLE {exists_clause}{table_name} (
        {', '.join(column_defs)}
    )
    """

    return client.execute_statement(sql)


def insert_record(
    client: SnowflakeAPIClient,
    table_name: str,
    data: Dict[str, Any],
    use_bindings: bool = False
) -> Dict[str, Any]:
    """
    Insert a single record into a table

    Easy way to insert one row of data into a table. Just pass a dict with
    column names as keys and values as values.

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to insert into
        data: Dict mapping column names to values
              Keys = column names, Values = what to insert
        use_bindings: Use parameter bindings (more secure, but slower)

    Returns:
        Dict with execution results (check for 'error' if failed)

    Example 1 - Insert a workflow:
        result = insert_record(
            client,
            'workflow',
            {
                'workflow_id': 'wf_001',
                'workflow_name': 'Open Canvas',
                'workflow_description': 'Opens Canvas and navigates to class',
                'workflow_video': 'https://example.com/video.mp4'
            }
        )
        print(result)  # Check if successful

    Example 2 - Insert a step:
        result = insert_record(
            client,
            'steps',
            {
                'step_id': 'step_001',
                'step_description': 'Click on login button',
                'step_number': 1,
                'workflow_id': 'wf_001'
            }
        )

    Example 3 - Insert with different data types:
        result = insert_record(
            client,
            'users',
            {
                'user_id': 'u123',
                'username': 'john_doe',
                'age': 25,
                'is_active': True,
                'bio': None  # NULL value
            }
        )
    """
    columns = list(data.keys())

    if use_bindings:
        # Use parameter bindings (recommended for security)
        placeholders = [f":{i+1}" for i in range(len(columns))]
        sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """

        # Create bindings dict with proper format
        bindings = {str(i+1): {'type': infer_type(val), 'value': val}
                   for i, val in enumerate(data.values())}

        return client.execute_statement(sql, bindings=bindings)
    else:
        # Direct value insertion (use only for trusted data)
        values = [format_value(val) for val in data.values()]
        sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(values)})
        """

        return client.execute_statement(sql)


def insert_records_batch(
    client: SnowflakeAPIClient,
    table_name: str,
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Insert multiple records in a single batch

    Much faster than calling insert_record() multiple times! Use this when you need
    to insert many rows at once.

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to insert into
        records: List of dicts, where each dict is one row to insert
                 All dicts should have the same keys (column names)

    Returns:
        Dict with execution results

    Example 1 - Insert multiple steps for a workflow:
        result = insert_records_batch(
            client,
            'steps',
            [
                {
                    'step_id': 'step_001',
                    'step_description': 'Open browser',
                    'step_number': 1,
                    'workflow_id': 'wf_001'
                },
                {
                    'step_id': 'step_002',
                    'step_description': 'Navigate to site',
                    'step_number': 2,
                    'workflow_id': 'wf_001'
                },
                {
                    'step_id': 'step_003',
                    'step_description': 'Click login',
                    'step_number': 3,
                    'workflow_id': 'wf_001'
                }
            ]
        )
        print(result)  # All 3 steps inserted at once!

    Example 2 - Insert multiple workflows:
        workflows = [
            {'workflow_id': 'wf_001', 'workflow_name': 'Login Flow', 'workflow_description': 'User login', 'workflow_video': None},
            {'workflow_id': 'wf_002', 'workflow_name': 'Checkout Flow', 'workflow_description': 'Purchase items', 'workflow_video': None}
        ]
        result = insert_records_batch(client, 'workflow', workflows)
    """
    if not records:
        return {'error': 'No records to insert', 'success': False}

    columns = list(records[0].keys())

    # Build multi-row INSERT
    value_rows = []
    for record in records:
        values = [format_value(record.get(col)) for col in columns]
        value_rows.append(f"({', '.join(values)})")

    sql = f"""
    INSERT INTO {table_name} ({', '.join(columns)})
    VALUES {', '.join(value_rows)}
    """

    return client.execute_statement(sql)


def retrieve_records(
    client: SnowflakeAPIClient,
    table_name: str,
    columns: Optional[List[str]] = None,
    where_clause: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retrieve records from a table

    Query/select data from a table with optional filtering, sorting, and limiting.
    This builds a SELECT statement for you.

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to query
        columns: List of specific columns to get (None = get all columns with *)
        where_clause: Filter condition (without 'WHERE' word)
                     Example: "age > 25 AND status = 'active'"
        order_by: Sort order (without 'ORDER BY' words)
                 Example: "created_at DESC" or "step_number ASC"
        limit: Maximum number of rows to return

    Returns:
        Dict with query results in 'data' field

    Example 1 - Get all workflows:
        result = retrieve_records(client, 'workflow')
        for row in result['data']:
            print(row['workflow_name'])

    Example 2 - Get specific workflow by ID:
        result = retrieve_records(
            client,
            'workflow',
            columns=['workflow_name', 'workflow_description'],
            where_clause="workflow_id = 'wf_001'"
        )
        print(result['data'][0])  # First (and only) matching row

    Example 3 - Get steps for a workflow, ordered:
        result = retrieve_records(
            client,
            'steps',
            where_clause="workflow_id = 'wf_001'",
            order_by='step_number ASC'
        )
        for step in result['data']:
            print(f"Step {step['step_number']}: {step['step_description']}")

    Example 4 - Get recent workflows (with limit):
        result = retrieve_records(
            client,
            'workflow',
            columns=['workflow_id', 'workflow_name'],
            order_by='workflow_id DESC',
            limit=10
        )

    Example 5 - Complex where clause:
        result = retrieve_records(
            client,
            'steps',
            where_clause="step_number > 1 AND step_description LIKE '%click%'"
        )
    """
    # Build SELECT clause
    select_cols = ', '.join(columns) if columns else '*'

    # Build SQL
    sql = f"SELECT {select_cols} FROM {table_name}"

    if where_clause:
        sql += f" WHERE {where_clause}"

    if order_by:
        sql += f" ORDER BY {order_by}"

    if limit:
        sql += f" LIMIT {limit}"

    return client.execute_statement(sql)


def update_records(
    client: SnowflakeAPIClient,
    table_name: str,
    updates: Dict[str, Any],
    where_clause: str
) -> Dict[str, Any]:
    """
    Update records in a table

    Modify existing rows in a table. IMPORTANT: Always include a WHERE clause
    or you'll update ALL rows!

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to update
        updates: Dict of column names to new values
                 Keys = columns to update, Values = new values
        where_clause: Condition to match rows (without 'WHERE' word)
                     This determines which rows get updated

    Returns:
        Dict with execution results (includes number of rows updated)

    Example 1 - Update a workflow's description:
        result = update_records(
            client,
            'workflow',
            {
                'workflow_description': 'Updated description',
                'workflow_video': 'https://new-url.com/video.mp4'
            },
            "workflow_id = 'wf_001'"
        )
        print(result)  # Shows how many rows were updated

    Example 2 - Update a step description:
        result = update_records(
            client,
            'steps',
            {'step_description': 'Click the new login button'},
            "step_id = 'step_001'"
        )

    Example 3 - Update multiple steps in a workflow:
        result = update_records(
            client,
            'steps',
            {'workflow_id': 'wf_002'},  # Move steps to different workflow
            "workflow_id = 'wf_001' AND step_number > 5"
        )

    WARNING: Without WHERE clause, ALL rows will be updated!
    """
    # Build SET clause
    set_clauses = [f"{col} = {format_value(val)}" for col, val in updates.items()]

    sql = f"""
    UPDATE {table_name}
    SET {', '.join(set_clauses)}
    WHERE {where_clause}
    """

    return client.execute_statement(sql)


def delete_records(
    client: SnowflakeAPIClient,
    table_name: str,
    where_clause: str
) -> Dict[str, Any]:
    """
    Delete records from a table

    Permanently removes rows from a table. BE CAREFUL - deletions are permanent!
    ALWAYS include a WHERE clause or you'll delete EVERYTHING!

    Args:
        client: SnowflakeAPIClient instance
        table_name: Name of the table to delete from
        where_clause: Condition to match rows to delete (without 'WHERE' word)

    Returns:
        Dict with execution results (includes number of rows deleted)

    Example 1 - Delete a specific workflow:
        result = delete_records(
            client,
            'workflow',
            "workflow_id = 'wf_001'"
        )
        print(result)  # Shows how many rows were deleted

    Example 2 - Delete all steps in a workflow:
        result = delete_records(
            client,
            'steps',
            "workflow_id = 'wf_001'"
        )
        # This removes all steps associated with workflow wf_001

    Example 3 - Delete old or invalid records:
        result = delete_records(
            client,
            'workflow',
            "workflow_video IS NULL AND workflow_id LIKE 'test_%'"
        )

    WARNING: Without WHERE clause, ALL rows will be deleted!
    Double-check your WHERE clause before running!
    """
    sql = f"DELETE FROM {table_name} WHERE {where_clause}"

    return client.execute_statement(sql)
