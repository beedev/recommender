# Vector Compatibility Search with Intelligent Fallback

## Overview

The Vector Compatibility Search system provides advanced product compatibility matching using semantic similarity with intelligent fallback to rules-based search when confidence is low.

## Architecture

```
User Query → Vector Similarity Search → Confidence Check → Results
                                              ↓ (if confidence < threshold)
                                      Rules-Based Fallback → Results
```

## Configuration

All settings are configurable via `.env` file:

```env
# Vector similarity confidence threshold (0.0-1.0)
# Results below this threshold trigger fallback to rules-based search
VECTOR_CONFIDENCE_THRESHOLD=0.8

# Number of candidates to retrieve from vector search
VECTOR_SEARCH_LIMIT=20

# Enable fallback to rules-based search when vector confidence is low
ENABLE_COMPATIBILITY_FALLBACK=true
```

## API Usage

### Endpoint: `POST /api/v1/vector-compatibility/compatibility-search`

**Request:**
```json
{
  "query": "Find feeders compatible with Aristo 500 ix for aluminum marine work",
  "target_product_id": "0094378274",  // Optional: specific product for compatibility
  "category_filter": "Feeder",        // Optional: filter by category
  "limit": 10                         // Optional: max results (default: 10)
}
```

**Response:**
```json
{
  "query": "Find feeders compatible with Aristo 500 ix for aluminum marine work",
  "method_used": "vector_high_confidence",
  "confidence_threshold": 0.8,
  "results": [
    {
      "product_id": "0094378275",
      "product_name": "VR 7000 Wire Feeder - Marine Grade",
      "category": "Feeder",
      "subcategory": "Wire Feeder",
      "description": "Marine-grade wire feeder designed for saltwater environments...",
      "compatibility_score": 0.89,
      "sales_frequency": 45
    }
  ],
  "total_found": 8,
  "execution_time_ms": 23.4,
  "target_product_context": "Aristo 500 ix (PowerSource)"
}
```

## Search Methods

### 1. Vector High Confidence (`vector_high_confidence`)
- Vector similarity search returns results above confidence threshold
- Uses 384-dimensional product embeddings
- Semantic understanding of compatibility relationships
- **Best case**: Fast, accurate, semantic matching

### 2. Vector Low Confidence (`vector_low_confidence`) 
- Vector results available but below confidence threshold
- Returns vector results as backup when fallback fails
- **Fallback case**: Some results better than no results

### 3. Rules Fallback (`rules_fallback`)
- Text-based search using extracted keywords
- Pattern matching in product names, descriptions, specifications
- Basic compatibility scoring based on term matches
- **Fallback case**: When vector confidence is insufficient

### 4. No Results (`no_results`)
- No compatible products found with any method
- Suggests query refinement or broader search terms

### 5. Error (`error`)
- System error during search execution
- Check logs for detailed error information

## Example Queries

### Simple Queries
- "Find MIG welders for aluminum"
- "Portable feeders for steel work" 
- "Heavy duty coolers for industrial use"
- "TIG torches for stainless steel"

### Complex Compatibility Queries
- "Find feeders compatible with Aristo 500 ix for aluminum marine work"
- "What coolers work with MIG welding in outdoor windy conditions"
- "Portable accessories for heavy duty steel fabrication in construction"
- "Find all products compatible with Warrior 400i that work with stainless steel in aerospace environment"

### Target Product Queries
```json
{
  "query": "compatible feeders for marine aluminum work",
  "target_product_id": "0094378274",
  "category_filter": "Feeder"
}
```

## Performance Characteristics

### Vector Search Performance
- **Execution Time**: ~15-30ms for vector search
- **Accuracy**: High semantic understanding
- **Coverage**: All 248 products with embeddings

### Fallback Performance  
- **Execution Time**: ~10-50ms for text search
- **Accuracy**: Basic keyword matching
- **Coverage**: All products in database

### Confidence Scoring
- **0.9-1.0**: Excellent semantic match
- **0.8-0.9**: Good compatibility (default threshold)
- **0.7-0.8**: Moderate compatibility
- **0.6-0.7**: Low compatibility 
- **<0.6**: Poor match (triggers fallback)

## Configuration Tuning

### Confidence Threshold (`VECTOR_CONFIDENCE_THRESHOLD`)
- **0.9**: Very strict, only excellent matches (may miss good results)
- **0.8**: Balanced setting (recommended default)
- **0.7**: More permissive, includes moderate matches
- **0.6**: Very permissive, rarely triggers fallback

### Search Limit (`VECTOR_SEARCH_LIMIT`)
- **10**: Fast, minimal candidates
- **20**: Balanced (recommended default)
- **50**: Comprehensive, slower processing

### Enable Fallback (`ENABLE_COMPATIBILITY_FALLBACK`)
- **true**: Smart fallback when vector confidence low (recommended)
- **false**: Vector-only mode, no fallback

## Integration Examples

### Python Client
```python
import aiohttp

async def search_compatible_products(query, target_product_id=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/vector-compatibility/compatibility-search",
            json={
                "query": query,
                "target_product_id": target_product_id,
                "limit": 10
            }
        ) as response:
            return await response.json()

# Example usage
results = await search_compatible_products(
    "Find marine feeders for aluminum welding",
    target_product_id="0094378274"
)

print(f"Found {results['total_found']} results using {results['method_used']}")
```

### JavaScript/React
```javascript
const searchCompatibility = async (query, targetProductId = null) => {
  const response = await fetch('/api/v1/vector-compatibility/compatibility-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      target_product_id: targetProductId,
      limit: 10
    })
  });
  
  return response.json();
};

// Example usage
const results = await searchCompatibility(
  "Find marine feeders for aluminum welding",
  "0094378274"
);

console.log(`Found ${results.total_found} results using ${results.method_used}`);
```

## Monitoring and Observability

### Key Metrics
- **Vector Hit Rate**: Percentage of searches using vector_high_confidence
- **Fallback Rate**: Percentage of searches requiring fallback
- **Average Confidence**: Mean confidence score of vector results
- **Response Time**: P50/P95/P99 response times by method

### Logging
- All searches logged with query, method used, and result count
- Confidence scores logged for performance analysis
- Fallback triggers logged for threshold tuning

### Health Checks
- Vector index health via `/vector-compatibility/config`
- Embedding generator status
- Database connectivity

## Troubleshooting

### Low Vector Confidence
- **Symptom**: Frequent fallback to rules-based search
- **Cause**: Query terms not well represented in embeddings
- **Solution**: Lower `VECTOR_CONFIDENCE_THRESHOLD` or improve query phrasing

### No Results Found
- **Symptom**: `method_used: "no_results"`
- **Cause**: Very specific query with no matching products
- **Solution**: Broaden search terms or remove category filters

### Slow Performance
- **Symptom**: High response times
- **Cause**: Large `VECTOR_SEARCH_LIMIT` or complex fallback queries
- **Solution**: Reduce search limits or optimize database queries

### Vector Index Issues
- **Symptom**: Vector search errors
- **Cause**: Missing or corrupted vector index
- **Solution**: Regenerate embeddings and recreate vector index

## Future Enhancements

1. **Hybrid Scoring**: Combine vector similarity with sales frequency
2. **User Feedback Learning**: Improve embeddings based on user selections
3. **Contextual Boosting**: Enhance queries with user session context
4. **Advanced Fallback**: Use NLP for better keyword extraction
5. **Performance Caching**: Cache common queries for faster response