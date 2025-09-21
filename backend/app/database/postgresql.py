"""
PostgreSQL database connection and management.

Provides async connection management, session handling, and connection pooling
for PostgreSQL database containing user data and application state.
"""

import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from contextlib import asynccontextmanager
import asyncio

import asyncpg
from asyncpg import Pool, Connection, Record
from asyncpg.exceptions import PostgresError

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class PostgreSQLConnection:
    """
    PostgreSQL database connection manager with async support.
    
    Handles connection pooling, transaction management, and provides
    safe query execution with parameterized queries.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self.settings = get_settings()
        self._pool: Optional[Pool] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        Establish connection pool to PostgreSQL database.
        
        Raises:
            PostgreSQLError: If unable to connect to database
        """
        try:
            logger.info(f"Connecting to PostgreSQL at {self.settings.POSTGRES_HOST}:{self.settings.POSTGRES_PORT}")
            
            self._pool = await asyncpg.create_pool(
                host=self.settings.POSTGRES_HOST,
                port=self.settings.POSTGRES_PORT,
                user=self.settings.POSTGRES_USER,
                password=self.settings.POSTGRES_PASSWORD,
                database=self.settings.POSTGRES_DB,
                min_size=self.settings.POSTGRES_MIN_CONNECTIONS,
                max_size=self.settings.POSTGRES_MAX_CONNECTIONS,
                command_timeout=30,
                server_settings={
                    'application_name': 'pconfig_recommender_api',
                }
            )
            
            # Verify connection
            await self._verify_connection()
            self._connected = True
            logger.info("Successfully connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise PostgreSQLError(f"PostgreSQL connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            self._connected = False
            logger.info("Disconnected from PostgreSQL database")
    
    async def _verify_connection(self) -> None:
        """
        Verify database connection by running a simple query.
        
        Raises:
            PostgreSQLError: If connection verification fails
        """
        if not self._pool:
            raise PostgreSQLError("No connection pool available")
        
        try:
            async with self._pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                if result != 1:
                    raise PostgreSQLError("Connection verification failed")
        except Exception as e:
            raise PostgreSQLError(f"Connection verification failed: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to PostgreSQL."""
        return self._connected and self._pool is not None
    
    async def execute_query(
        self,
        query: str,
        *args: Any,
        fetch_all: bool = True
    ) -> Optional[List[Record]]:
        """
        Execute a SELECT query with parameters.
        
        Args:
            query: SQL query to execute
            *args: Query parameters for safety
            fetch_all: Whether to fetch all results or just first row
            
        Returns:
            Query results as list of Records or single Record
            
        Raises:
            PostgreSQLError: For database-related errors
        """
        if not self._pool:
            raise PostgreSQLError("No database connection")
        
        try:
            async with self._pool.acquire() as connection:
                if fetch_all:
                    return await connection.fetch(query, *args)
                else:
                    result = await connection.fetchrow(query, *args)
                    return [result] if result else []
                    
        except PostgresError as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise PostgreSQLError(f"Query execution failed: {e}")
    
    async def execute_query_one(
        self,
        query: str,
        *args: Any
    ) -> Optional[Record]:
        """
        Execute a SELECT query and return only the first row.
        
        Args:
            query: SQL query to execute
            *args: Query parameters for safety
            
        Returns:
            First query result as Record or None
            
        Raises:
            PostgreSQLError: For database-related errors
        """
        if not self._pool:
            raise PostgreSQLError("No database connection")
        
        try:
            async with self._pool.acquire() as connection:
                return await connection.fetchrow(query, *args)
                
        except PostgresError as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise PostgreSQLError(f"Query execution failed: {e}")
    
    async def execute_scalar(
        self,
        query: str,
        *args: Any
    ) -> Any:
        """
        Execute a query and return a single scalar value.
        
        Args:
            query: SQL query to execute
            *args: Query parameters for safety
            
        Returns:
            Single scalar value
            
        Raises:
            PostgreSQLError: For database-related errors
        """
        if not self._pool:
            raise PostgreSQLError("No database connection")
        
        try:
            async with self._pool.acquire() as connection:
                return await connection.fetchval(query, *args)
                
        except PostgresError as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise PostgreSQLError(f"Query execution failed: {e}")
    
    async def execute_command(
        self,
        query: str,
        *args: Any
    ) -> str:
        """
        Execute an INSERT, UPDATE, or DELETE command.
        
        Args:
            query: SQL command to execute
            *args: Command parameters for safety
            
        Returns:
            Command result status
            
        Raises:
            PostgreSQLError: For database-related errors
        """
        if not self._pool:
            raise PostgreSQLError("No database connection")
        
        try:
            async with self._pool.acquire() as connection:
                return await connection.execute(query, *args)
                
        except PostgresError as e:
            logger.error(f"PostgreSQL command error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            raise PostgreSQLError(f"Command execution failed: {e}")
    
    async def execute_transaction(
        self,
        commands: List[tuple]
    ) -> List[Any]:
        """
        Execute multiple commands in a transaction.
        
        Args:
            commands: List of (query, *args) tuples to execute
            
        Returns:
            List of command results
            
        Raises:
            PostgreSQLError: For database-related errors
        """
        if not self._pool:
            raise PostgreSQLError("No database connection")
        
        try:
            async with self._pool.acquire() as connection:
                async with connection.transaction():
                    results = []
                    for query, *args in commands:
                        result = await connection.execute(query, *args)
                        results.append(result)
                    return results
                    
        except PostgresError as e:
            logger.error(f"PostgreSQL transaction error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing transaction: {e}")
            raise PostgreSQLError(f"Transaction execution failed: {e}")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get PostgreSQL database information and statistics.
        
        Returns:
            Dictionary containing database information
        """
        if not self._pool:
            return {"status": "not_connected"}
        
        try:
            async with self._pool.acquire() as connection:
                info = {}
                
                # Database version
                version = await connection.fetchval("SELECT version()")
                info["version"] = version
                
                # Database size
                size_query = """
                SELECT pg_size_pretty(pg_database_size($1)) as size
                """
                size = await connection.fetchval(size_query, self.settings.POSTGRES_DB)
                info["database_size"] = size
                
                # Connection info
                info["database_name"] = self.settings.POSTGRES_DB
                info["host"] = self.settings.POSTGRES_HOST
                info["port"] = self.settings.POSTGRES_PORT
                info["pool_size"] = f"{self._pool.get_size()}/{self._pool.get_max_size()}"
                
                # Table count
                table_count = await connection.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                info["table_count"] = table_count
                
                return info
                
        except Exception as e:
            logger.warning(f"Could not get database info: {e}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on PostgreSQL connection.
        
        Returns:
            Dictionary containing health status
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            if not self._pool:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "No connection pool available",
                    "database": self.settings.POSTGRES_DB
                }
            
            async with self._pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "connected": self.is_connected,
                "response_time_ms": round(response_time, 2),
                "database": self.settings.POSTGRES_DB,
                "pool_size": f"{self._pool.get_size()}/{self._pool.get_max_size()}"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "database": self.settings.POSTGRES_DB
            }
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """
        Context manager for PostgreSQL connections.
        
        Yields:
            PostgreSQL connection instance
        """
        if not self._pool:
            raise PostgreSQLError("No connection pool available")
        
        async with self._pool.acquire() as connection:
            yield connection


# Global PostgreSQL connection instance
postgres_connection = PostgreSQLConnection()


async def get_postgres_connection() -> PostgreSQLConnection:
    """
    Dependency for getting PostgreSQL connection.
    
    Returns:
        PostgreSQL connection instance
        
    Raises:
        PostgreSQLError: If not connected to database
    """
    if not postgres_connection.is_connected:
        await postgres_connection.connect()
    
    return postgres_connection


async def get_connection():
    """
    Get a database connection for agent tracking.
    
    Returns:
        Context manager for database connection
    """
    connection_instance = await get_postgres_connection()
    return connection_instance.get_connection()


async def close_postgres_connection() -> None:
    """Close the global PostgreSQL connection pool."""
    await postgres_connection.disconnect()