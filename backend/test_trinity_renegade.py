#!/usr/bin/env python3
"""
Test Trinity queries with 'package with Renegade' scenarios
Verify that the new Order→Trinity architecture works correctly
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append('/Users/bharath/Desktop/AgenticAI/Recommender/backend')

from app.database.repositories.neo4j_repository import Neo4jRepository
from app.database.neo4j import Neo4jConnection
from app.agents.simple_neo4j_agent import SimpleNeo4jAgent
from app.agents.simple_intent_agent import SimpleWeldingIntent
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_trinity_semantic_search():
    """Test Trinity semantic search functionality"""
    try:
        logger.info("🚀 Testing Trinity Semantic Search with Renegade scenarios...")
        
        # Initialize Neo4j connection and repository
        neo4j_connection = Neo4jConnection()
        neo4j_repo = Neo4jRepository(neo4j_connection)
        agent = SimpleNeo4jAgent(neo4j_repo)
        
        # Test queries
        test_queries = [
            "package with Renegade",
            "Renegade ES 300i welding package",
            "Renegade power source with accessories",
            "welding package Renegade ES",
            "complete Renegade setup"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing query: '{query}'")
            
            # Test Trinity semantic search
            trinity_results = await agent.search_trinity_combinations(query, limit=3)
            
            if trinity_results:
                logger.info(f"✅ Found {len(trinity_results)} Trinity combinations:")
                for i, trinity in enumerate(trinity_results):
                    logger.info(f"  {i+1}. {trinity['powersource_name']} + "
                               f"{trinity['feeder_name']} + {trinity['cooler_name']} "
                               f"(score: {trinity['similarity_score']:.3f}, orders: {trinity['order_count']})")
                
                # Test getting components for the best Trinity
                best_trinity = trinity_results[0]
                components = await agent.get_trinity_package_components(best_trinity['trinity_id'])
                
                if components:
                    logger.info(f"✅ Trinity components retrieved:")
                    for category, comp in components.items():
                        logger.info(f"  - {category}: {comp.product_name} ({comp.product_id})")
                else:
                    logger.warning(f"❌ Could not retrieve components for Trinity {best_trinity['trinity_id']}")
            else:
                logger.warning(f"❌ No Trinity results found for '{query}'")
        
        await neo4j_connection.close()
        logger.info("🎯 Trinity semantic search tests completed")
        
    except Exception as e:
        logger.error(f"❌ Error in Trinity semantic search test: {e}")
        import traceback
        traceback.print_exc()

async def test_full_package_formation():
    """Test full package formation with Trinity-first approach"""
    try:
        logger.info("🚀 Testing full package formation with Trinity-first approach...")
        
        # Initialize Neo4j connection and repository
        neo4j_connection = Neo4jConnection()
        neo4j_repo = Neo4jRepository(neo4j_connection)
        agent = SimpleNeo4jAgent(neo4j_repo)
        
        # Create test intent
        intent = SimpleWeldingIntent(
            original_query="package with Renegade ES 300i",
            welding_process=["MIG"],
            material="steel",
            industry="fabrication",
            application="general",
            environment="indoor",
            confidence=0.9
        )
        
        logger.info("🔍 Testing full package formation...")
        package = await agent.form_welding_package(intent)
        
        if package:
            logger.info(f"✅ Package formed successfully:")
            logger.info(f"  Power Source: {package.power_source.product_name if package.power_source else 'None'}")
            logger.info(f"  Feeders: {[f.product_name for f in package.feeders]}")
            logger.info(f"  Coolers: {[c.product_name for c in package.coolers]}")
            logger.info(f"  Accessories: {len(package.accessories)} items")
            logger.info(f"  Total Price: ${package.total_price:.2f}")
            logger.info(f"  Package Score: {package.package_score:.3f}")
            logger.info(f"  Confidence: {package.confidence:.3f}")
        else:
            logger.warning("❌ No package formed")
        
        await neo4j_connection.close()
        logger.info("🎯 Full package formation test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in full package formation test: {e}")
        import traceback
        traceback.print_exc()

async def test_direct_trinity_queries():
    """Test direct Trinity queries using Neo4j"""
    try:
        logger.info("🚀 Testing direct Trinity queries...")
        
        # Initialize Neo4j connection and repository
        neo4j_connection = Neo4jConnection()
        neo4j_repo = Neo4jRepository(neo4j_connection)
        
        # Test 1: Check Trinity nodes exist
        trinity_count_query = "MATCH (tr:Trinity) RETURN count(tr) as total_trinities"
        result = await neo4j_repo.execute_query(trinity_count_query, {})
        trinity_count = result[0]['total_trinities'] if result else 0
        logger.info(f"📊 Total Trinity nodes in database: {trinity_count}")
        
        # Test 2: Check Renegade Trinity existence
        renegade_query = """
        MATCH (tr:Trinity) 
        WHERE tr.powersource_name CONTAINS 'Renegade'
        RETURN tr.trinity_id, tr.powersource_name, tr.feeder_name, tr.cooler_name, tr.order_count
        ORDER BY tr.order_count DESC
        LIMIT 5
        """
        renegade_results = await neo4j_repo.execute_query(renegade_query, {})
        
        if renegade_results:
            logger.info(f"✅ Found {len(renegade_results)} Renegade Trinity combinations:")
            for trinity in renegade_results:
                logger.info(f"  - {trinity['powersource_name']} + {trinity['feeder_name']} + {trinity['cooler_name']} "
                           f"({trinity['order_count']} orders)")
        else:
            logger.warning("❌ No Renegade Trinity combinations found")
        
        # Test 3: Check Order→Trinity relationships
        order_trinity_query = """
        MATCH (o:Order)-[:FORMS_TRINITY]->(tr:Trinity)
        WHERE tr.powersource_name CONTAINS 'Renegade'
        RETURN count(DISTINCT o) as orders_with_renegade_trinity
        """
        order_result = await neo4j_repo.execute_query(order_trinity_query, {})
        order_count = order_result[0]['orders_with_renegade_trinity'] if order_result else 0
        logger.info(f"📊 Orders with Renegade Trinity: {order_count}")
        
        await neo4j_connection.close()
        logger.info("🎯 Direct Trinity queries test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in direct Trinity queries test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    logger.info("🎯 Starting Trinity Renegade Test Suite...")
    
    await test_direct_trinity_queries()
    await test_trinity_semantic_search()
    await test_full_package_formation()
    
    logger.info("🏆 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())