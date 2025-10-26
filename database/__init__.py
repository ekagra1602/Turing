"""
Snowflake Database Utilities

A clean, easy-to-use interface for Snowflake SQL API operations.

Quick Start:
    from database import SnowflakeAPIClient, create_table, insert_record, retrieve_records

    # Initialize client
    client = SnowflakeAPIClient(
        account='your_account',
        warehouse='your_warehouse',
        database='your_database',
        schema='your_schema'
    )

    # Create a table
    create_table(client, 'users', {'id': 'VARCHAR(100)', 'name': 'VARCHAR(200)'}, primary_key='id')

    # Insert data
    insert_record(client, 'users', {'id': 'u1', 'name': 'John Doe'})

    # Query data
    result = retrieve_records(client, 'users')
    print(result['data'])

See examples.py for complete usage examples.
"""

# Export client
from .client import SnowflakeAPIClient

# Export all operations
from .operations import (
    create_table,
    insert_record,
    insert_records_batch,
    retrieve_records,
    update_records,
    delete_records
)

# Export helpers (in case someone needs them)
from .helpers import infer_type, format_value

# Define what gets imported with "from database import *"
__all__ = [
    # Client
    'SnowflakeAPIClient',

    # Operations
    'create_table',
    'insert_record',
    'insert_records_batch',
    'retrieve_records',
    'update_records',
    'delete_records',

    # Helpers
    'infer_type',
    'format_value',
]

# Version info
__version__ = '1.0.0'
__author__ = 'AgentFlow Team'
