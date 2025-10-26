# Database Module

Clean, modular utilities for interacting with Snowflake using the SQL API.

## 📁 File Structure

```
database/
├── __init__.py          # Main entry point - exports everything
├── client.py            # SnowflakeAPIClient class
├── operations.py        # CRUD functions (create, insert, retrieve, update, delete)
├── helpers.py           # Helper functions (type inference, value formatting)
├── examples.py          # Complete usage examples
└── README.md            # This file
```

## 🚀 Quick Start

### Installation

```bash
pip install requests
```

### Basic Usage

```python
from database import SnowflakeAPIClient, create_table, insert_record, retrieve_records

# 1. Initialize client
client = SnowflakeAPIClient(
    account='your_account',
    warehouse='your_warehouse',
    database='your_database',
    schema='your_schema'
)

# 2. Create a table
create_table(
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

# 3. Insert data
insert_record(
    client,
    'workflow',
    {
        'workflow_id': 'wf_001',
        'workflow_name': 'My Workflow',
        'workflow_description': 'A sample workflow',
        'workflow_video': 'https://example.com/video.mp4'
    }
)

# 4. Query data
result = retrieve_records(
    client,
    'workflow',
    where_clause="workflow_id = 'wf_001'"
)
print(result['data'])
```

## 📚 Module Reference

### `client.py` - SnowflakeAPIClient

Core client for connecting to Snowflake.

**Methods:**
- `__init__(account, warehouse, database, schema)` - Initialize client
- `execute_statement(sql, timeout, bindings)` - Execute any SQL
- `get_statement_status(handle)` - Check query status
- `cancel_statement(handle)` - Cancel running query

### `operations.py` - CRUD Functions

Convenience functions for common operations.

**Functions:**
- `create_table(client, table_name, columns, primary_key, if_not_exists)` - Create tables
- `insert_record(client, table_name, data, use_bindings)` - Insert single record
- `insert_records_batch(client, table_name, records)` - Insert multiple records
- `retrieve_records(client, table_name, columns, where_clause, order_by, limit)` - Query data
- `update_records(client, table_name, updates, where_clause)` - Update records
- `delete_records(client, table_name, where_clause)` - Delete records

### `helpers.py` - Helper Functions

Internal utilities (usually don't need to call directly).

**Functions:**
- `infer_type(value)` - Infer Snowflake type from Python value
- `format_value(value)` - Format Python value as SQL string

### `examples.py` - Usage Examples

Complete working examples. Run with:

```bash
python -m database.examples
```

## 🔧 Configuration

### 1. Set Snowflake Config

When creating the client, provide your Snowflake details:

```python
client = SnowflakeAPIClient(
    account='xy12345.us-east-1',
    warehouse='COMPUTE_WH',
    database='PRODUCTION',
    schema='PUBLIC'
)
```

### 2. Add Authentication

Edit `client.py` and update the `_get_headers()` method with your auth:

```python
def _get_headers(self) -> Dict[str, str]:
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {your_token}'  # Add your token here
    }
```

## 📋 Your Tables

This module is designed for your workflow/steps schema:

### `workflow` table
- `workflow_id` (VARCHAR, PRIMARY KEY)
- `workflow_name` (VARCHAR, NOT NULL)
- `workflow_description` (TEXT)
- `workflow_video` (VARCHAR)

### `steps` table
- `step_id` (VARCHAR, PRIMARY KEY)
- `step_description` (TEXT)
- `step_number` (INTEGER, NOT NULL)
- `workflow_id` (VARCHAR, FOREIGN KEY)
- UNIQUE constraint on `(step_number, workflow_id)`

## 💡 Tips

1. **Import what you need:**
   ```python
   from database import SnowflakeAPIClient, insert_record, retrieve_records
   ```

2. **Or import everything:**
   ```python
   from database import *
   ```

3. **Run examples to test:**
   ```bash
   python -m database.examples
   ```

4. **Check function docstrings:**
   Every function has detailed docstrings with multiple examples!

## 📖 Reference

- [Snowflake SQL API Docs](https://docs.snowflake.com/en/developer-guide/sql-api/intro)
- See individual file docstrings for detailed documentation
- Run `python -m database.examples` for working examples
