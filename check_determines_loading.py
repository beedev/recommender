#!/usr/bin/env python3
"""
Check DETERMINES relationships loading
Investigation script to verify which PowerSources have DETERMINES relationships
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_determines_relationships():
    """Check what DETERMINES relationships exist for PowerSources"""
    
    # Database connection
    uri = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '123Welcome')
    database = os.getenv('NEO4J_DATABASE', 'recommender')
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            print("=== PowerSource DETERMINES Relationship Analysis ===\n")
            
            # Get all PowerSources
            powersources_query = """
            MATCH (p:Product {category: 'PowerSource'})
            RETURN p.gin as gin, p.name as name
            ORDER BY p.name
            """
            
            powersources = session.run(powersources_query)
            all_powersources = list(powersources)
            
            print(f"Total PowerSources in database: {len(all_powersources)}")
            print()
            
            # Check DETERMINES relationships for each PowerSource
            for ps in all_powersources:
                gin = ps['gin']
                name = ps['name']
                
                # Count DETERMINES relationships
                determines_query = """
                MATCH (p:Product {gin: $gin})-[d:DETERMINES]->(target:Product)
                RETURN count(d) as determines_count,
                       collect(DISTINCT target.category) as target_categories
                """
                
                result = session.run(determines_query, gin=gin)
                data = result.single()
                
                determines_count = data['determines_count']
                target_categories = data['target_categories']
                
                if determines_count > 0:
                    print(f"✅ {name} ({gin}): {determines_count} DETERMINES relationships -> {target_categories}")
                else:
                    print(f"❌ {name} ({gin}): 0 DETERMINES relationships")
            
            print("\n=== Summary ===")
            
            # Get total counts
            summary_query = """
            MATCH (p:Product {category: 'PowerSource'})
            OPTIONAL MATCH (p)-[d:DETERMINES]->()
            WITH p, count(d) as determines_count
            RETURN 
                count(p) as total_powersources,
                sum(CASE WHEN determines_count > 0 THEN 1 ELSE 0 END) as powersources_with_determines,
                sum(determines_count) as total_determines_relationships
            """
            
            summary = session.run(summary_query).single()
            
            print(f"PowerSources with DETERMINES relationships: {summary['powersources_with_determines']}/{summary['total_powersources']}")
            print(f"Total DETERMINES relationships: {summary['total_determines_relationships']}")
            
            # Check what's in the compatibility rules file
            print("\n=== Analysis of the Issue ===")
            
            # The PowerSources without DETERMINES rules:
            missing_determines = [
                ("0446200880", "Aristo 500ix CE"),
                ("0445250880", "Renegade ES 300i Kit w/welding cables"),
                ("0445100880", "Renegade ES 300i incl 3 m mains cable and plug")
            ]
            
            for gin, name in missing_determines:
                # Check if this PowerSource exists in the database
                exists_query = "MATCH (p:Product {gin: $gin}) RETURN count(p) as count"
                exists = session.run(exists_query, gin=gin).single()['count']
                
                if exists > 0:
                    print(f"⚠️  {name} ({gin}) exists in database but has no DETERMINES rules in compatibility_rules.json")
                else:
                    print(f"ℹ️  {name} ({gin}) does not exist in database")
            
            print("\n=== PowerSources with DETERMINES rules in compatibility_rules.json ===")
            # These are the only ones with DETERMINES rules:
            warrior_series = [
                ("0445555880", "Warrior 750i CC/CV"),
                ("0465350883", "Warrior 500i CC/CV"), 
                ("0465350884", "Warrior 400i CC/CV")
            ]
            
            for gin, name in warrior_series:
                print(f"✅ {name} ({gin}) has DETERMINES rules in compatibility_rules.json")
    
    finally:
        driver.close()

if __name__ == "__main__":
    check_determines_relationships()