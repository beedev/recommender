// Simple Vector Search Queries for Neo4j Desktop Testing
// Copy and paste these queries directly into Neo4j Desktop

// 1. Get an actual product embedding for vector search test
MATCH (p:Product)
WHERE p.embedding IS NOT NULL
WITH p.embedding as sample_vector
LIMIT 1
CALL db.index.vector.queryNodes('product_embeddings', 5, sample_vector)
YIELD node, score
RETURN node.name, node.category, score
ORDER BY score DESC
LIMIT 3;

// 2. Check if vector index exists
SHOW INDEXES
WHERE name = 'product_embeddings';

// 3. Count products with embeddings
MATCH (p:Product)
WHERE p.embedding IS NOT NULL
RETURN count(p) as products_with_embeddings;

// 4. Sample product with embedding info
MATCH (p:Product)
WHERE p.embedding IS NOT NULL
RETURN p.name, p.category, size(p.embedding) as embedding_size
LIMIT 3;

// 5. Find products by category
MATCH (p:Product)
WHERE p.category CONTAINS 'Power'
RETURN p.name, p.category
LIMIT 5;

// 6. Show compatibility relationships
MATCH (p1:Product)-[r:COMPATIBLE_WITH]->(p2:Product)
RETURN p1.name, p2.name, r.confidence
LIMIT 5;

// 7. Golden package formations
MATCH (g:GoldenPackage)-[:CONTAINS]->(p:Product)
RETURN g.name, collect(p.name) as products
LIMIT 3;

// 8. Sales data insights
MATCH (s:Sale)-[:PURCHASED]->(p:Product)
RETURN p.category, count(s) as sales_count
ORDER BY sales_count DESC
LIMIT 5;

// 9. Show compatibility relationships with details
MATCH (p1:Product)-[r:COMPATIBLE_WITH]->(p2:Product)
RETURN p1.name, p1.category, p2.name, p2.category, r.confidence, r.rule_id
LIMIT 5;

// 10. Find high-confidence compatibility relationships
MATCH (p1:Product)-[r:COMPATIBLE_WITH]->(p2:Product)
WHERE r.confidence >= 0.8
RETURN p1.name, p2.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 5;

// 11. Count relationships by type
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC;

// 12. Alternative vector search - find similar products to a specific product
MATCH (target:Product {name: 'Renegade ES 300i incl 3 m mains cable and plug'})
WHERE target.embedding IS NOT NULL
CALL db.index.vector.queryNodes('product_embeddings', 5, target.embedding)
YIELD node, score
RETURN node.name, node.category, score
ORDER BY score DESC;