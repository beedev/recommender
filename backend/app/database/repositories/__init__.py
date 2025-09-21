"""
Repository pattern implementations for database access.

This package provides repository classes for both Neo4j (graph database)
and PostgreSQL (relational database) with safe, parameterized queries.
"""

from .neo4j_repository import Neo4jRepository, get_neo4j_repository
from .postgres_repository import PostgreSQLRepository, get_postgres_repository

__all__ = [
    # Neo4j Repository
    "Neo4jRepository",
    "get_neo4j_repository",
    
    # PostgreSQL Repository
    "PostgreSQLRepository", 
    "get_postgres_repository"
]