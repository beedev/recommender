"""
Neo4j database connection and management.

Provides secure connection management, session handling, and transaction support
for the Neo4j graph database containing product and recommendation data.
"""

import logging
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor

from neo4j import GraphDatabase, Driver, Session, Transaction, Result
from neo4j.exceptions import ServiceUnavailable, TransientError, Neo4jError

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Neo4j database connection manager with async support.
    
    Handles connection pooling, session management, and provides
    both synchronous and asynchronous query execution.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self.settings = get_settings()
        self._driver: Optional[Driver] = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._connected = False
    
    async def connect(self) -> None:
        """
        Establish connection to Neo4j database.
        
        Raises:
            ServiceUnavailable: If unable to connect to database
        """
        try:
            logger.info(f"Connecting to Neo4j at {self.settings.NEO4J_URI}")
            
            # For Aura DB, don't specify encryption settings - they're handled by the URI scheme
            driver_args = {
                "uri": self.settings.NEO4J_URI,
                "auth": (self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD),
                "max_connection_pool_size": self.settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
                "connection_acquisition_timeout": self.settings.NEO4J_CONNECTION_ACQUISITION_TIMEOUT,
                "connection_timeout": self.settings.NEO4J_CONNECTION_TIMEOUT,
                "max_transaction_retry_time": self.settings.NEO4J_MAX_TRANSACTION_RETRY_TIME,
            }
            
            # Only add encryption settings for local Neo4j instances (bolt:// or neo4j://)
            if self.settings.NEO4J_URI.startswith(("bolt://", "neo4j://")):
                driver_args["encrypted"] = False
            
            self._driver = GraphDatabase.driver(**driver_args)
            
            # Verify connection
            await self._verify_connection()
            self._connected = True
            logger.info("Successfully connected to Neo4j database")
            
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise ServiceUnavailable(f"Neo4j connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._driver.close
            )
            self._connected = False
            logger.info("Disconnected from Neo4j database")
    
    async def _verify_connection(self) -> None:
        """
        Verify database connection by running a simple query.
        
        Raises:
            ServiceUnavailable: If connection verification fails
        """
        if not self._driver:
            raise ServiceUnavailable("No driver available")
        
        try:
            result = await self.execute_query("RETURN 1 as test")
            if not result or not result[0].get("test"):
                raise ServiceUnavailable("Connection verification failed")
        except Exception as e:
            raise ServiceUnavailable(f"Connection verification failed: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self._connected and self._driver is not None
    
    def _sync_execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous query execution (internal use).
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters
            database: Database name (defaults to configured database)
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            Neo4jError: For database-related errors
        """
        if not self._driver:
            raise ServiceUnavailable("No database connection")
        
        db_name = database or self.settings.NEO4J_DATABASE
        parameters = parameters or {}
        
        try:
            with self._driver.session(database=db_name) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
                
        except Neo4jError as e:
            logger.error(f"Neo4j query error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise Neo4jError(f"Query execution failed: {e}")
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query asynchronously.
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters for safety
            database: Database name (defaults to configured database)
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            Neo4jError: For database-related errors
        """
        return await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._sync_execute_query,
            query,
            parameters,
            database
        )
    
    def _sync_execute_write_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous write query execution (internal use).
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters
            database: Database name
            
        Returns:
            List of result records as dictionaries
        """
        if not self._driver:
            raise ServiceUnavailable("No database connection")
        
        db_name = database or self.settings.NEO4J_DATABASE
        parameters = parameters or {}
        
        try:
            with self._driver.session(database=db_name) as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, parameters)
                )
                return [record.data() for record in result]
                
        except Neo4jError as e:
            logger.error(f"Neo4j write query error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing write query: {e}")
            raise Neo4jError(f"Write query execution failed: {e}")
    
    async def execute_write_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a write Cypher query asynchronously.
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters for safety
            database: Database name (defaults to configured database)
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            Neo4jError: For database-related errors
        """
        return await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._sync_execute_write_query,
            query,
            parameters,
            database
        )
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get Neo4j database information and statistics.
        
        Returns:
            Dictionary containing database information
        """
        queries = {
            "node_count": "MATCH (n) RETURN count(n) as count",
            "relationship_count": "MATCH ()-[r]->() RETURN count(r) as count",
            "node_labels": "CALL db.labels() YIELD label RETURN collect(label) as labels",
            "relationship_types": "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types",
            "database_info": "CALL dbms.components() YIELD name, versions RETURN name, versions"
        }
        
        info = {}
        for key, query in queries.items():
            try:
                result = await self.execute_query(query)
                if key in ["node_count", "relationship_count"]:
                    info[key] = result[0]["count"] if result else 0
                elif key in ["node_labels", "relationship_types"]:
                    info[key] = result[0].get("labels" if key == "node_labels" else "types", []) if result else []
                else:
                    info[key] = result
            except Exception as e:
                logger.warning(f"Could not get {key}: {e}")
                info[key] = None
        
        return info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection.
        
        Returns:
            Dictionary containing health status
        """
        try:
            start_time = asyncio.get_event_loop().time()
            result = await self.execute_query("RETURN 1 as health_check")
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "connected": self.is_connected,
                "response_time_ms": round(response_time, 2),
                "database": self.settings.NEO4J_DATABASE
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "database": self.settings.NEO4J_DATABASE
            }
    
    @asynccontextmanager
    async def get_session(self, database: Optional[str] = None) -> AsyncGenerator[Session, None]:
        """
        Context manager for Neo4j sessions.
        
        Args:
            database: Database name (defaults to configured database)
            
        Yields:
            Neo4j session instance
        """
        if not self._driver:
            raise ServiceUnavailable("No database connection")
        
        db_name = database or self.settings.NEO4J_DATABASE
        session = self._driver.session(database=db_name)
        
        try:
            yield session
        finally:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, session.close
            )
    
    async def verify_connectivity(self) -> bool:
        """
        Verify database connectivity with a simple test query.
        
        Returns:
            True if connection is working
            
        Raises:
            ServiceUnavailable: If connection fails
        """
        try:
            result = await self.execute_query("RETURN 1 as test")
            return len(result) > 0 and result[0].get("test") == 1
        except Exception as e:
            raise ServiceUnavailable(f"Neo4j connectivity test failed: {e}")
    
    async def get_node_count(self) -> int:
        """Get total count of nodes in database."""
        try:
            result = await self.execute_query("MATCH (n) RETURN count(n) as count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0
    
    async def get_relationship_count(self) -> int:
        """Get total count of relationships in database."""
        try:
            result = await self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0
    
    async def get_product_count(self) -> int:
        """Get count of product nodes."""
        try:
            result = await self.execute_query("MATCH (p:Product) RETURN count(p) as count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0
    
    async def get_package_count(self) -> int:
        """Get count of package nodes."""
        try:
            result = await self.execute_query("MATCH (p:Package) RETURN count(p) as count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0


# Global Neo4j connection instance
neo4j_connection = Neo4jConnection()


async def get_neo4j_connection() -> Neo4jConnection:
    """
    Dependency for getting Neo4j connection.
    
    Returns:
        Neo4j connection instance
        
    Raises:
        ServiceUnavailable: If not connected to database
    """
    if not neo4j_connection.is_connected:
        await neo4j_connection.connect()
    
    return neo4j_connection


async def close_neo4j_connection() -> None:
    """Close the global Neo4j connection."""
    await neo4j_connection.disconnect()