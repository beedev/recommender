#!/usr/bin/env python3
"""
Demo Vector Search Queries
Test vector search to verify Aristo 500 ix exists in database
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

async def test_aristo_search():
    """Test if Aristo 500 ix exists in the database"""
    
    # Load environment variables
    load_dotenv()
    
    print("🎯 TESTING WARRIOR 400 I IN DATABASE")
    print("=" * 50)
    
    try:
        # Import services
        from app.services.vector_migration import get_vector_migration_service
        
        # Get migration service
        migration_service = await get_vector_migration_service()
        
        # Test queries for Warrior 400 i
        test_queries = [
            "Warrior 400 i",
            "Warrior 400i",
            "Warrior 400",
            "Warrior",
            "400 i",
            "welding machine 400 amp",
            "MIG welder 400 amp"
        ]
        
        print("Testing different search terms for Warrior 400 i:")
        print("-" * 50)
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            try:
                # Perform vector search
                results = await migration_service.test_vector_search(query, limit=5)
                
                if results:
                    print(f"   ✅ Found {len(results)} products:")
                    for i, result in enumerate(results, 1):
                        score = result['score']
                        name = result['name']
                        gin = result['gin']
                        category = result.get('category', 'N/A')
                        
                        # Highlight if it contains "Warrior"
                        highlight = "🎯" if "warrior" in name.lower() else "  "
                        
                        print(f"      {i}. {highlight} {name}")
                        print(f"         GIN: {gin} | Category: {category} | Score: {score:.3f}")
                else:
                    print("   ❌ No results found")
                    
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_aristo_search())
    print(f"\n{'🎉 Test completed!' if success else '💥 Test failed!'}")
    sys.exit(0 if success else 1)