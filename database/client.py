"""
Snowflake SQL API Client

Core client for connecting to and executing statements on Snowflake.

Reference: https://docs.snowflake.com/en/developer-guide/sql-api/intro
"""

import requests
from typing import Dict, Any, Optional


class SnowflakeAPIClient:
    """
    Client for interacting with Snowflake SQL API

    This class handles all communication with Snowflake's REST API for executing SQL statements.
    You initialize it once with your connection details, then use it for all database operations.

    Example Usage:
        # Create a client
        client = SnowflakeAPIClient(
            account='mycompany',
            warehouse='COMPUTE_WH',
            database='MYDB',
            schema='PUBLIC'
        )

        # Execute a custom SQL statement
        result = client.execute_statement("SELECT * FROM my_table LIMIT 10")
        print(result)

        # Check status of a long-running query
        status = client.get_statement_status('query-handle-12345')

        # Cancel a running query
        client.cancel_statement('query-handle-12345')
    """

    def __init__(
        self,
        account: str = 'YOUR_ACCOUNT',
        warehouse: str = 'YOUR_WAREHOUSE',
        database: str = 'YOUR_DATABASE',
        schema: str = 'YOUR_SCHEMA'
    ):
        """
        Initialize Snowflake API client with configuration

        Args:
            account: Your Snowflake account identifier (e.g., 'xy12345.us-east-1')
            warehouse: Snowflake warehouse name (e.g., 'COMPUTE_WH')
            database: Database name (e.g., 'PRODUCTION_DB')
            schema: Schema name (e.g., 'PUBLIC')

        Example:
            client = SnowflakeAPIClient(
                account='mycompany.us-west-2',
                warehouse='COMPUTE_WH',
                database='ANALYTICS',
                schema='PUBLIC'
            )
        """
        self.account = account
        self.warehouse = warehouse
        self.database = database
        self.schema = schema

        # Construct base URL for Snowflake SQL API
        self.base_url = f"https://{self.account}.snowflakecomputing.com/api/v2/statements"

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Snowflake SQL API requests

        Returns HTTP headers needed for API requests. YOU NEED TO ADD YOUR AUTH HERE!

        Common auth methods:
            - Bearer token: 'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
            - OAuth: 'Authorization': 'Bearer YOUR_OAUTH_TOKEN'
            - Key Pair JWT: 'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT'

        Example:
            def _get_headers(self):
                return {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.access_token}'  # Add your token here
                }
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            # TODO: Add your authentication header here
            # 'Authorization': 'Bearer YOUR_TOKEN' or 'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT'
        }

    def execute_statement(
        self,
        sql: str,
        timeout: int = 60,
        bindings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL statement using Snowflake SQL API

        This is the core method that sends SQL to Snowflake and gets results back.
        Use this for any custom SQL you want to run.

        Args:
            sql: SQL statement to execute (e.g., "SELECT * FROM users WHERE id = 1")
            timeout: Maximum seconds to wait for query completion (default: 60)
            bindings: Parameter bindings for prepared statements (optional, for security)

        Returns:
            Dict with query results and metadata, or error info if failed

        Example 1 - Simple query:
            result = client.execute_statement("SELECT * FROM users LIMIT 5")
            print(result['data'])  # Access the results

        Example 2 - With parameter bindings:
            result = client.execute_statement(
                "SELECT * FROM users WHERE status = :1 AND age > :2",
                bindings={
                    '1': {'type': 'TEXT', 'value': 'active'},
                    '2': {'type': 'FIXED', 'value': 18}
                }
            )

        Example 3 - CREATE or INSERT:
            result = client.execute_statement(
                "INSERT INTO logs (message, level) VALUES ('System started', 'INFO')"
            )
            print(result)  # Check success status

        Reference: https://docs.snowflake.com/en/developer-guide/sql-api/submitting-requests
        """
        payload = {
            'statement': sql,
            'timeout': timeout,
            'database': self.database,
            'schema': self.schema,
            'warehouse': self.warehouse
        }

        if bindings:
            payload['bindings'] = bindings

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=timeout + 10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def get_statement_status(self, statement_handle: str) -> Dict[str, Any]:
        """
        Check the status of an asynchronously executed statement

        Use this to poll a long-running query to see if it's done yet.
        The statement_handle is returned in the response from execute_statement().

        Args:
            statement_handle: Unique handle/ID returned from execute_statement()

        Returns:
            Dict with status ('running', 'success', 'failed') and results if complete

        Example:
            # Start a long query
            result = client.execute_statement("SELECT * FROM huge_table")
            handle = result['statementHandle']

            # Check status later
            import time
            while True:
                status = client.get_statement_status(handle)
                if status['statementStatusUrl'] == 'success':
                    print("Query done!", status['data'])
                    break
                elif status['statementStatusUrl'] == 'failed':
                    print("Query failed:", status['message'])
                    break
                time.sleep(2)  # Wait 2 seconds before checking again
        """
        url = f"{self.base_url}/{statement_handle}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def cancel_statement(self, statement_handle: str) -> Dict[str, Any]:
        """
        Cancel a running statement

        Stops a query that's currently executing. Useful if a query is taking too long
        or you started it by mistake.

        Args:
            statement_handle: Handle/ID of the statement to cancel

        Returns:
            Dict with cancellation status (success or error)

        Example:
            # Start a query
            result = client.execute_statement("SELECT * FROM massive_table")
            handle = result['statementHandle']

            # Oops, cancel it!
            cancel_result = client.cancel_statement(handle)
            print(cancel_result)  # {'message': 'Statement cancelled successfully'}
        """
        url = f"{self.base_url}/{statement_handle}/cancel"

        try:
            response = requests.post(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }
