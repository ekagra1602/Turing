"""
Helper functions for Snowflake SQL operations

Internal utilities for type inference and value formatting.
You typically don't need to call these directly.
"""

from typing import Any


def infer_type(value: Any) -> str:
    """
    Infer Snowflake data type from a Python value

    Internal helper that maps Python types to Snowflake types for parameter bindings.
    You don't need to call this directly - insert_record() uses it automatically.

    Args:
        value: Any Python value

    Returns:
        Snowflake type string ('BOOLEAN', 'FIXED', 'REAL', 'TEXT')

    Examples:
        infer_type(True) -> 'BOOLEAN'
        infer_type(42) -> 'FIXED'
        infer_type(3.14) -> 'REAL'
        infer_type('hello') -> 'TEXT'
        infer_type(None) -> 'TEXT'
    """
    if isinstance(value, bool):
        return 'BOOLEAN'
    elif isinstance(value, int):
        return 'FIXED'
    elif isinstance(value, float):
        return 'REAL'
    elif isinstance(value, str):
        return 'TEXT'
    elif value is None:
        return 'TEXT'
    else:
        return 'TEXT'


def format_value(value: Any) -> str:
    """
    Format a Python value as SQL-safe string

    Internal helper that converts Python values to SQL format with proper escaping.
    Handles NULL values, booleans, numbers, and strings with quote escaping.
    You don't need to call this directly - insert functions use it automatically.

    Args:
        value: Any Python value

    Returns:
        SQL-formatted string ready to insert into a query

    Examples:
        format_value(None) -> 'NULL'
        format_value(True) -> 'TRUE'
        format_value(42) -> '42'
        format_value(3.14) -> '3.14'
        format_value('hello') -> "'hello'"
        format_value("it's") -> "'it''s'"  # Escaped single quote
    """
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape single quotes by doubling them
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    else:
        # Convert to string and escape
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"
