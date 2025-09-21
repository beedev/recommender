"""
Database connection management for the Pconfig Recommender API.

This package provides connection management and factories for both Neo4j
(graph database) and PostgreSQL (relational database) connections.
"""

import logging
from typing import Dict, Any

from .neo4j import (
    Neo4jConnection,
    neo4j_connection,
    get_neo4j_connection,
    close_neo4j_connection
)
from .postgresql import (
    PostgreSQLConnection,
    postgres_connection,
    get_postgres_connection,
    close_postgres_connection
)

logger = logging.getLogger(__name__)

__all__ = [
    # Neo4j
    "Neo4jConnection",
    "neo4j_connection",
    "get_neo4j_connection",
    "close_neo4j_connection",
    
    # PostgreSQL
    "PostgreSQLConnection", 
    "postgres_connection",
    "get_postgres_connection",
    "close_postgres_connection",
    
    # Utilities
    "get_database_connections",
    "init_databases",
    "close_all_connections",
    "health_check_all_databases"
]


async def get_database_connections() -> Dict[str, Any]:
    """
    Get all database connection instances.
    
    Returns:
        Dictionary containing all database connections
    """
    return {
        "neo4j": await get_neo4j_connection(),
        "postgres": await get_postgres_connection()
    }


async def init_databases() -> Dict[str, Any]:
    """
    Initialize all database connections.
    
    Returns:
        Dictionary containing connection status for each database
    """
    results = {}
    
    # Initialize Neo4j connection
    try:
        await neo4j_connection.connect()
        results["neo4j"] = {
            "status": "connected",
            "database": neo4j_connection.settings.NEO4J_DATABASE
        }
        logger.info("Neo4j database connection initialized successfully")
    except Exception as e:
        results["neo4j"] = {
            "status": "failed",
            "error": str(e)
        }
        logger.error(f"Failed to initialize Neo4j connection: {e}")
    
    # Initialize PostgreSQL connection
    try:
        await postgres_connection.connect()
        results["postgres"] = {
            "status": "connected", 
            "database": postgres_connection.settings.POSTGRES_DB
        }
        logger.info("PostgreSQL database connection initialized successfully")
    except Exception as e:
        results["postgres"] = {
            "status": "failed",
            "error": str(e)
        }
        logger.error(f"Failed to initialize PostgreSQL connection: {e}")
    
    return results


async def close_all_connections() -> None:
    """
    Close all database connections gracefully.
    """
    logger.info("Closing all database connections...")
    
    # Close Neo4j connection
    try:
        await close_neo4j_connection()
        logger.info("Neo4j connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing Neo4j connection: {e}")
    
    # Close PostgreSQL connection
    try:
        await close_postgres_connection()
        logger.info("PostgreSQL connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")
    
    logger.info("All database connections closed")


async def health_check_all_databases() -> Dict[str, Dict[str, Any]]:
    """
    Perform health checks on all database connections.
    
    Returns:
        Dictionary containing health status for each database
    """
    health_status = {}
    
    # Neo4j health check
    try:
        if neo4j_connection.is_connected:
            health_status["neo4j"] = await neo4j_connection.health_check()
        else:
            health_status["neo4j"] = {
                "status": "not_connected",
                "connected": False,
                "database": neo4j_connection.settings.NEO4J_DATABASE
            }
    except Exception as e:
        health_status["neo4j"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    # PostgreSQL health check
    try:
        if postgres_connection.is_connected:
            health_status["postgres"] = await postgres_connection.health_check()
        else:
            health_status["postgres"] = {
                "status": "not_connected",
                "connected": False,
                "database": postgres_connection.settings.POSTGRES_DB
            }
    except Exception as e:
        health_status["postgres"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    return health_status