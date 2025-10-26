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
        schema: str = 'YOUR_SCHEMA',
        role: Optional[str] = None
    ):
        """
        Initialize Snowflake API client with configuration

        Args:
            account: Your Snowflake account identifier (e.g., 'xy12345.us-east-1')
            warehouse: Snowflake warehouse name (e.g., 'COMPUTE_WH')
            database: Database name (e.g., 'PRODUCTION_DB')
            schema: Schema name (e.g., 'PUBLIC')
            role: Optional role name (e.g., 'ACCOUNTADMIN', uses user default if None)

        Example:
            client = SnowflakeAPIClient(
                account='mycompany.us-west-2',
                warehouse='COMPUTE_WH',
                database='ANALYTICS',
                schema='PUBLIC',
                role='ANALYST_ROLE'
            )

        Important Notes:
            - Database, schema, and warehouse names are CASE-SENSITIVE
            - AUTOCOMMIT must be TRUE (set per query or statement level)
            - PUT and GET commands are NOT supported
            - For multi-statement requests, use semicolons between statements
        """
        self.account = account
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role

        # Construct base URL for Snowflake SQL API
        self.base_url = f"https://{self.account}.snowflakecomputing.com/api/v2/statements"

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Snowflake SQL API requests

        Returns HTTP headers needed for API requests. YOU NEED TO ADD YOUR AUTH HERE!

        Snowflake supports two authentication methods:

        1. OAuth Authentication:
            - Header: 'Authorization': 'Bearer <oauth_token>'
            - Optional: 'X-Snowflake-Authorization-Token-Type': 'OAUTH'

        2. Key Pair JWT Authentication:
            - Header: 'Authorization': 'Bearer <jwt_token>'
            - Optional: 'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT'
            - JWT must include: iss, sub, iat, exp fields
            - JWT expires after 1 hour maximum

        Example (OAuth):
            def _get_headers(self):
                return {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.oauth_token}',
                    'X-Snowflake-Authorization-Token-Type': 'OAUTH'
                }

        Example (Key Pair JWT):
            def _get_headers(self):
                return {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.jwt_token}',
                    'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT'
                }

        Reference: https://docs.snowflake.com/en/developer-guide/sql-api/authenticating
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            # TODO: Add your authentication headers here
            # Option 1 - OAuth:
            # 'Authorization': 'Bearer YOUR_OAUTH_TOKEN',
            # 'X-Snowflake-Authorization-Token-Type': 'OAUTH'
            #
            # Option 2 - Key Pair JWT:
            # 'Authorization': 'Bearer YOUR_JWT_TOKEN',
            # 'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT'
        }

    def execute_statement(
        self,
        sql: str,
        timeout: Optional[int] = None,
        bindings: Optional[Dict[str, Any]] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL statement using Snowflake SQL API

        This is the core method that sends SQL to Snowflake and gets results back.
        Use this for any custom SQL you want to run.

        Args:
            sql: SQL statement to execute (e.g., "SELECT * FROM users WHERE id = 1")
                 For multiple statements, separate with semicolons
            timeout: Maximum seconds to wait (None = uses STATEMENT_TIMEOUT_IN_SECONDS)
            bindings: Parameter bindings for prepared statements (use ? placeholders)
            role: Role to use for this statement (overrides client default)

        Returns:
            Dict with query results and metadata. Possible structures:
            - HTTP 200: ResultSet object with 'data', 'statementHandle', etc.
            - HTTP 202: QueryStatus object (query still running)
            - HTTP 422: QueryFailureStatus object (query failed)
            - HTTP 429: Rate limited, retry with backoff

        Example 1 - Simple query:
            result = client.execute_statement("SELECT * FROM users LIMIT 5")
            if 'data' in result:
                print(result['data'])  # Access the results

        Example 2 - With parameter bindings (use ? placeholders):
            result = client.execute_statement(
                "SELECT * FROM users WHERE status = ? AND age > ?",
                bindings={
                    '1': {'type': 'TEXT', 'value': 'active'},
                    '2': {'type': 'FIXED', 'value': 18}
                }
            )

        Example 3 - Multi-statement request:
            result = client.execute_statement(
                "CREATE TABLE test (id INT); INSERT INTO test VALUES (1), (2);"
            )

        Example 4 - With specific role:
            result = client.execute_statement(
                "SELECT * FROM sensitive_data",
                role='ACCOUNTADMIN'
            )

        Response Status Codes:
            - 200: Query completed successfully
            - 202: Query still executing (poll with get_statement_status)
            - 422: Query failed (check error in response)
            - 429: Rate limited (implement retry with backoff)

        Reference: https://docs.snowflake.com/en/developer-guide/sql-api/submitting-requests
        """
        payload = {
            'statement': sql,
            'database': self.database,
            'schema': self.schema,
            'warehouse': self.warehouse
        }

        # Add optional fields only if provided
        if timeout is not None:
            payload['timeout'] = timeout

        if bindings:
            payload['bindings'] = bindings

        if role or self.role:
            payload['role'] = role if role else self.role

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=(timeout + 10) if timeout else None
            )

            # Handle different HTTP status codes
            if response.status_code == 200:
                # Success - query completed
                return response.json()
            elif response.status_code == 202:
                # Query still running
                return response.json()
            elif response.status_code == 422:
                # Query failed
                return {**response.json(), 'error': 'Query execution failed', 'status_code': 422}
            elif response.status_code == 429:
                # Rate limited
                return {'error': 'Rate limited', 'status_code': 429, 'message': 'Retry with backoff'}
            else:
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

    def get_result_partition(self, statement_handle: str, partition: int = 0) -> Dict[str, Any]:
        """
        Retrieve a specific partition of query results

        Large result sets are split into partitions by Snowflake. Use this to retrieve
        additional partitions beyond the first one (which is included in the initial response).

        Args:
            statement_handle: Handle/ID from the statement execution
            partition: Partition number to retrieve (0-indexed, 0 is included in initial response)

        Returns:
            Dict containing the partition data

        Example:
            # Execute a query that returns lots of data
            result = client.execute_statement("SELECT * FROM large_table")
            handle = result['statementHandle']

            # Check if there are multiple partitions
            partition_info = result.get('resultSetMetaData', {}).get('partitionInfo', [])
            print(f"Total partitions: {len(partition_info)}")

            # Get partition 1 (partition 0 is in the initial result)
            if len(partition_info) > 1:
                partition_1 = client.get_result_partition(handle, partition=1)
                print(partition_1['data'])

            # Get partition 2
            if len(partition_info) > 2:
                partition_2 = client.get_result_partition(handle, partition=2)
                print(partition_2['data'])

        Note:
            - Partition 0 is included in the initial execute_statement() response
            - Use this method only for partitions 1, 2, 3, etc.
            - Check 'partitionInfo' in resultSetMetaData to see how many partitions exist

        Reference: https://docs.snowflake.com/en/developer-guide/sql-api/handling-responses
        """
        url = f"{self.base_url}/{statement_handle}?partition={partition}"

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
