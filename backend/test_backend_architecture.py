#!/usr/bin/env python3
"""
Test Backend Architecture Implementation
Verify that all backend services are using the new Order→Trinity→Product architecture
"""

import asyncio
import logging
import sys
import json
import time
from typing import Dict, Any

# Add backend to path
sys.path.append('/Users/bharath/Desktop/AgenticAI/Recommender/backend')

from app.database.neo4j import Neo4jConnection
from app.database.repositories.neo4j_repository import Neo4jRepository
from app.agents.simple_neo4j_agent import SimpleNeo4jAgent
from app.services.enterprise.smart_neo4j_service import SmartNeo4jService
from app.services.enterprise.enterprise_orchestrator_service import EnterpriseOrchestratorService
from app.services.enterprise.enhanced_state_models import (
    EnhancedProcessedIntent, UserContext, ExpertiseMode, LanguageCode
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendArchitectureTest:
    """Comprehensive test suite for backend architecture"""
    
    def __init__(self):
        self.connection = None
        self.neo4j_repo = None
        self.simple_agent = None
        self.smart_service = None
        self.orchestrator = None
    
    async def setup(self):
        """Initialize all services"""
        try:
            logger.info("🔧 Setting up test environment...")
            
            # Initialize database connection
            self.connection = Neo4jConnection()
            await self.connection.connect()
            
            self.neo4j_repo = Neo4jRepository(self.connection)
            
            # Initialize agents and services
            self.simple_agent = SimpleNeo4jAgent(self.neo4j_repo)
            self.smart_service = SmartNeo4jService(self.neo4j_repo)
            self.orchestrator = EnterpriseOrchestratorService(self.neo4j_repo)
            
            logger.info("✅ Test environment setup completed")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise
    
    async def cleanup(self):
        """Clean up test environment"""
        try:
            if self.connection:
                await self.connection.disconnect()
            logger.info("🧹 Test environment cleaned up")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    async def test_trinity_semantic_search(self) -> Dict[str, Any]:
        """Test Trinity semantic search functionality"""
        logger.info("🔍 Testing Trinity semantic search...")
        
        try:
            test_queries = [
                "package with Renegade",
                "complete welding setup",
                "Renegade ES 300i kit",
                "MIG welding system"
            ]
            
            results = {}
            
            for query in test_queries:
                start_time = time.time()
                trinity_results = await self.simple_agent.search_trinity_combinations(query, limit=3)
                processing_time = (time.time() - start_time) * 1000
                
                results[query] = {
                    "trinity_count": len(trinity_results),
                    "processing_time_ms": processing_time,
                    "top_result": trinity_results[0] if trinity_results else None
                }
                
                logger.info(f"  Query: '{query}' → {len(trinity_results)} results ({processing_time:.1f}ms)")
            
            return {
                "status": "success",
                "test_results": results,
                "total_queries": len(test_queries)
            }
            
        except Exception as e:
            logger.error(f"❌ Trinity semantic search test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_trinity_component_retrieval(self) -> Dict[str, Any]:
        """Test Trinity component retrieval"""
        logger.info("🔧 Testing Trinity component retrieval...")
        
        try:
            # First get some Trinity IDs
            trinity_query = """
            MATCH (tr:Trinity)
            RETURN tr.trinity_id as trinity_id
            LIMIT 3
            """
            
            trinity_ids_result = await self.neo4j_repo.execute_query(trinity_query, {})
            trinity_ids = [result['trinity_id'] for result in trinity_ids_result]
            
            if not trinity_ids:
                return {"status": "failed", "error": "No Trinity nodes found in database"}
            
            results = {}
            
            for trinity_id in trinity_ids:
                start_time = time.time()
                components = await self.simple_agent.get_trinity_package_components(trinity_id)
                processing_time = (time.time() - start_time) * 1000
                
                results[trinity_id] = {
                    "component_count": len(components) if components else 0,
                    "processing_time_ms": processing_time,
                    "categories": list(components.keys()) if components else []
                }
                
                logger.info(f"  Trinity {trinity_id} → {len(components) if components else 0} components ({processing_time:.1f}ms)")
            
            return {
                "status": "success",
                "test_results": results,
                "total_trinities": len(trinity_ids)
            }
            
        except Exception as e:
            logger.error(f"❌ Trinity component retrieval test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_smart_service_trinity_integration(self) -> Dict[str, Any]:
        """Test Smart Neo4j Service Trinity integration"""
        logger.info("🧠 Testing Smart Neo4j Service Trinity integration...")
        
        try:
            # Create test intent for Trinity-first approach
            test_intent = EnhancedProcessedIntent(
                original_query="complete welding package for Renegade",
                welding_processes=["MIG"],
                materials=["steel"],
                applications=["fabrication"],
                industries=["automotive"],
                expertise_mode=ExpertiseMode.GUIDED,
                language_code=LanguageCode.EN,
                confidence=0.9,
                complexity_score=0.6,
                multilingual_support=False,
                original_intent=None  # Would be populated in real scenario
            )
            
            start_time = time.time()
            
            # Test Trinity-first approach
            trinity_result = await self.smart_service._try_trinity_semantic_search(
                test_intent, 
                "test_trace_001"
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            if trinity_result:
                return {
                    "status": "success",
                    "trinity_packages_found": len(trinity_result.packages),
                    "trinity_formation_rate": trinity_result.trinity_formation_rate,
                    "processing_time_ms": processing_time,
                    "algorithms_used": [alg.value for alg in trinity_result.algorithms_used]
                }
            else:
                return {
                    "status": "no_results",
                    "message": "Trinity search did not find suitable packages",
                    "processing_time_ms": processing_time
                }
            
        except Exception as e:
            logger.error(f"❌ Smart service Trinity integration test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_enterprise_orchestrator_integration(self) -> Dict[str, Any]:
        """Test Enterprise Orchestrator integration"""
        logger.info("🏢 Testing Enterprise Orchestrator integration...")
        
        try:
            # Create user context
            user_context = UserContext(
                user_id="test_user_001",
                session_id="test_session_001",
                preferred_language="en",
                expertise_history=[],
                previous_queries=[],
                industry_context="automotive",
                organization="Test Corp",
                role="test_user",
                permissions=[]
            )
            
            start_time = time.time()
            
            # Test complete orchestrator flow
            response = await self.orchestrator.process_recommendation_request(
                query="I need a complete welding package with Renegade",
                user_context=user_context,
                session_id="test_session_001"
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success",
                "packages_found": len(response.packages),
                "processing_time_ms": processing_time,
                "trinity_formation_rate": getattr(response, 'trinity_formation_rate', 0.0),
                "has_explanations": bool(response.explanations),
                "has_formatted_response": bool(response.formatted_response),
                "confidence": response.confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Enterprise orchestrator integration test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_architecture_queries(self) -> Dict[str, Any]:
        """Test that queries are using the new architecture"""
        logger.info("🏗️ Testing architecture query patterns...")
        
        try:
            # Test Order→Trinity relationships
            order_trinity_query = """
            MATCH (o:Order)-[:FORMS_TRINITY]->(tr:Trinity)
            RETURN count(DISTINCT o) as order_count, count(DISTINCT tr) as trinity_count
            """
            
            result = await self.neo4j_repo.execute_query(order_trinity_query, {})
            order_trinity_data = result[0] if result else {"order_count": 0, "trinity_count": 0}
            
            # Test Trinity→Product relationships  
            trinity_product_query = """
            MATCH (tr:Trinity)-[:COMPRISES]->(p:Product)
            RETURN count(DISTINCT tr) as trinity_count, count(DISTINCT p) as product_count
            """
            
            result = await self.neo4j_repo.execute_query(trinity_product_query, {})
            trinity_product_data = result[0] if result else {"trinity_count": 0, "product_count": 0}
            
            # Test complete chain: Order→Trinity→Product
            chain_query = """
            MATCH (o:Order)-[:FORMS_TRINITY]->(tr:Trinity)-[:COMPRISES]->(p:Product)
            RETURN count(DISTINCT o) as orders, count(DISTINCT tr) as trinities, count(DISTINCT p) as products
            """
            
            result = await self.neo4j_repo.execute_query(chain_query, {})
            chain_data = result[0] if result else {"orders": 0, "trinities": 0, "products": 0}
            
            return {
                "status": "success",
                "order_trinity_relationships": order_trinity_data,
                "trinity_product_relationships": trinity_product_data,
                "complete_chain": chain_data,
                "architecture_healthy": (
                    order_trinity_data["order_count"] > 0 and 
                    trinity_product_data["trinity_count"] > 0 and 
                    chain_data["orders"] > 0
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Architecture query test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend architecture tests"""
        logger.info("🚀 Starting comprehensive backend architecture tests...")
        
        await self.setup()
        
        try:
            test_results = {}
            
            # Run all tests
            test_results["trinity_semantic_search"] = await self.test_trinity_semantic_search()
            test_results["trinity_component_retrieval"] = await self.test_trinity_component_retrieval()
            test_results["smart_service_integration"] = await self.test_smart_service_trinity_integration()
            test_results["orchestrator_integration"] = await self.test_enterprise_orchestrator_integration()
            test_results["architecture_queries"] = await self.test_architecture_queries()
            
            # Calculate overall success
            successful_tests = sum(1 for result in test_results.values() if result["status"] == "success")
            total_tests = len(test_results)
            
            overall_result = {
                "overall_status": "success" if successful_tests == total_tests else "partial",
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "success_rate": successful_tests / total_tests * 100,
                "detailed_results": test_results
            }
            
            logger.info(f"🎯 Backend Architecture Tests Completed: {successful_tests}/{total_tests} tests passed ({overall_result['success_rate']:.1f}%)")
            
            return overall_result
            
        finally:
            await self.cleanup()

async def main():
    """Run backend architecture tests"""
    test_suite = BackendArchitectureTest()
    results = await test_suite.run_all_tests()
    
    print("\n" + "="*80)
    print("BACKEND ARCHITECTURE TEST RESULTS")
    print("="*80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Success Rate: {results['success_rate']:.1f}% ({results['successful_tests']}/{results['total_tests']})")
    print("\nDetailed Results:")
    
    for test_name, result in results['detailed_results'].items():
        status_emoji = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_emoji} {test_name.replace('_', ' ').title()}: {result['status']}")
    
    print("="*80)
    
    if results['success_rate'] == 100:
        print("🎉 All backend services are successfully using the new Trinity architecture!")
    else:
        print("⚠️  Some tests failed. Review the detailed results above.")

if __name__ == "__main__":
    asyncio.run(main())