#!/usr/bin/env python3
"""
Test Vector Compatibility Search Implementation
Quick test to verify vector compatibility search with fallback is working
"""

import asyncio
import sys
import os
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.repositories.neo4j_repository import Neo4jRepository
from app.database.neo4j import Neo4jConnection
from app.agents.simple_neo4j_agent import SimpleNeo4jAgent
from app.core.config import settings

async def test_vector_compatibility():
    """Test vector compatibility search functionality"""
    
    print("🔍 Testing Vector Compatibility Search with Fallback")
    print(f"📊 Configuration:")
    print(f"   - Vector Confidence Threshold: {settings.VECTOR_CONFIDENCE_THRESHOLD}")
    print(f"   - Vector Search Limit: {settings.VECTOR_SEARCH_LIMIT}")
    print(f"   - Enable Fallback: {settings.ENABLE_COMPATIBILITY_FALLBACK}")
    print()
    
    # Initialize Neo4j connection and agent
    neo4j_connection = Neo4jConnection()
    await neo4j_connection.connect()
    neo4j_repo = Neo4jRepository(neo4j_connection)
    agent = SimpleNeo4jAgent(neo4j_repo)
    
    # Test queries with different complexity levels
    test_queries = [
        {
            "query": "Find MIG welders for aluminum work",
            "category_filter": "PowerSource",
            "description": "Simple vector search"
        },
        {
            "query": "Find feeders compatible with Aristo 500 ix for marine aluminum welding",
            "target_product_id": "0094378274",  # Example product ID
            "category_filter": "Feeder",
            "description": "Complex compatibility with target product"
        },
        {
            "query": "Portable heavy duty equipment for outdoor steel fabrication",
            "description": "General compatibility query"
        },
        {
            "query": "xyz123 nonexistent product compatibility test",
            "description": "Low confidence test to trigger fallback"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"🧪 Test {i}: {test_case['description']}")
        print(f"   Query: '{test_case['query']}'")
        
        try:
            # Run compatibility search
            results, method_used = await agent.find_compatible_products_with_fallback(
                compatibility_query=test_case["query"],
                target_product_id=test_case.get("target_product_id"),
                category_filter=test_case.get("category_filter"),
                limit=5
            )
            
            print(f"   ✅ Method Used: {method_used}")
            print(f"   📋 Results: {len(results)} products found")
            
            # Display top results
            for j, result in enumerate(results[:3]):
                confidence_emoji = "🎯" if result.compatibility_score >= settings.VECTOR_CONFIDENCE_THRESHOLD else "⚠️"
                print(f"      {j+1}. {confidence_emoji} {result.product_name} ({result.category})")
                print(f"         Score: {result.compatibility_score:.3f}")
            
            if len(results) > 3:
                print(f"         ... and {len(results) - 3} more results")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test configuration retrieval
    print("⚙️ Testing configuration retrieval...")
    try:
        # This would be available via API endpoint
        config_info = {
            "vector_confidence_threshold": settings.VECTOR_CONFIDENCE_THRESHOLD,
            "vector_search_limit": settings.VECTOR_SEARCH_LIMIT,
            "enable_compatibility_fallback": settings.ENABLE_COMPATIBILITY_FALLBACK
        }
        print(f"   ✅ Configuration: {json.dumps(config_info, indent=2)}")
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
    
    # Clean up connection
    try:
        await neo4j_connection.close()
    except AttributeError:
        # Connection cleanup not needed for this test
        pass
    
    print()
    print("🎉 Vector compatibility search testing complete!")
    print(f"📝 Summary:")
    print(f"   - Vector search uses embeddings for semantic matching")
    print(f"   - Fallback to rules-based search when confidence < {settings.VECTOR_CONFIDENCE_THRESHOLD}")
    print(f"   - Configurable via .env file settings")
    print(f"   - API available at /api/v1/vector-compatibility/compatibility-search")

if __name__ == "__main__":
    asyncio.run(test_vector_compatibility())