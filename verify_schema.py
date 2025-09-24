#!/usr/bin/env python3
"""
Database Schema Verification Script
Checks what node types and relationships actually exist in the Neo4j database
"""

import asyncio
from neo4j import GraphDatabase

class SchemaVerifier:
    def __init__(self, uri="bolt://127.0.0.1:7687", user="neo4j", password="123Welcome", database="recommender"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
    
    def close(self):
        self.driver.close()
    
    def verify_schema(self):
        """Check actual database schema"""
        
        with self.driver.session(database=self.database) as session:
            print("🔍 DATABASE SCHEMA VERIFICATION")
            print("=" * 50)
            
            # 1. Check all node types and their counts
            print("\n📊 NODE TYPES:")
            node_query = """
            CALL db.labels() YIELD label
            CALL apoc.cypher.run("MATCH (n:" + label + ") RETURN count(n) as count", {}) YIELD value
            RETURN label, value.count as count
            ORDER BY value.count DESC
            """
            
            try:
                result = session.run(node_query)
                for record in result:
                    print(f"   {record['label']}: {record['count']} nodes")
            except Exception as e:
                # Fallback if APOC is not available
                print("   Using simple node count queries...")
                basic_labels = ["Product", "Transaction", "Order", "Customer", "GoldenPackage"]
                for label in basic_labels:
                    try:
                        simple_query = f"MATCH (n:{label}) RETURN count(n) as count"
                        result = session.run(simple_query)
                        count = result.single()["count"]
                        if count > 0:
                            print(f"   {label}: {count} nodes")
                    except:
                        pass
            
            # 2. Check all relationship types and their counts
            print("\n🔗 RELATIONSHIP TYPES:")
            rel_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            CALL apoc.cypher.run("MATCH ()-[r:" + relationshipType + "]-() RETURN count(r) as count", {}) YIELD value
            RETURN relationshipType, value.count as count
            ORDER BY value.count DESC
            """
            
            try:
                result = session.run(rel_query)
                for record in result:
                    print(f"   {record['relationshipType']}: {record['count']} relationships")
            except Exception as e:
                # Fallback if APOC is not available
                print("   Using simple relationship count queries...")
                basic_rels = ["CONTAINS", "PURCHASED", "MADE", "COMPATIBLE_WITH", "CO_OCCURS"]
                for rel in basic_rels:
                    try:
                        simple_query = f"MATCH ()-[r:{rel}]-() RETURN count(r) as count"
                        result = session.run(simple_query)
                        count = result.single()["count"]
                        if count > 0:
                            print(f"   {rel}: {count} relationships")
                    except:
                        pass
            
            # 3. Check specific sales-related patterns
            print("\n💰 SALES DATA PATTERNS:")
            
            # Check Transaction nodes specifically
            trans_query = "MATCH (t:Transaction) RETURN count(t) as count"
            result = session.run(trans_query)
            trans_count = result.single()["count"]
            print(f"   Transaction nodes: {trans_count}")
            
            # Check Order nodes specifically  
            order_query = "MATCH (o:Order) RETURN count(o) as count"
            result = session.run(order_query)
            order_count = result.single()["count"]
            print(f"   Order nodes: {order_count}")
            
            # Check Transaction->Product relationships
            if trans_count > 0:
                trans_contains_query = "MATCH (t:Transaction)-[:CONTAINS]->(p:Product) RETURN count(*) as count"
                result = session.run(trans_contains_query)
                trans_contains = result.single()["count"]
                print(f"   Transaction-[:CONTAINS]->Product: {trans_contains}")
                
                # Sample a few transactions
                sample_query = "MATCH (t:Transaction)-[:CONTAINS]->(p:Product) RETURN t.order_id, p.name LIMIT 3"
                result = session.run(sample_query)
                print(f"   Sample transactions:")
                for record in result:
                    print(f"     Order {record['t.order_id']}: {record['p.name']}")
            
            # Check Order->Product relationships (if any exist)
            if order_count > 0:
                order_purchased_query = "MATCH (o:Order)-[:PURCHASED]->(p:Product) RETURN count(*) as count"
                result = session.run(order_purchased_query)
                order_purchased = result.single()["count"]
                print(f"   Order-[:PURCHASED]->Product: {order_purchased}")
            
            # 4. Check what relationships Products actually have for sales
            print("\n🛍️ PRODUCT SALES RELATIONSHIPS:")
            product_sales_query = """
            MATCH (p:Product)
            OPTIONAL MATCH (p)<-[:CONTAINS]-(t:Transaction)
            OPTIONAL MATCH (p)<-[:PURCHASED]-(o:Order)
            WITH p, count(DISTINCT t) as transaction_count, count(DISTINCT o) as order_count
            WHERE transaction_count > 0 OR order_count > 0
            RETURN p.name, transaction_count, order_count
            ORDER BY transaction_count DESC, order_count DESC
            LIMIT 5
            """
            
            result = session.run(product_sales_query)
            for record in result:
                print(f"   {record['p.name']}: {record['transaction_count']} transactions, {record['order_count']} orders")

if __name__ == "__main__":
    verifier = SchemaVerifier()
    try:
        verifier.verify_schema()
    finally:
        verifier.close()