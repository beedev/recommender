
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', '123Welcome'))

with driver.session(database='recommender') as session:
          # Check what types of nodes have DETERMINES relationships
          query = '''
          MATCH (from)-[:DETERMINES]->(to)
          RETURN labels(from) as from_labels, labels(to) as to_labels, count(*) as count
          '''

          print('DETERMINES relationship types:')
          result = session.run(query)
          for record in result:
              print(f'{record["from_labels"]} -> {record["to_labels"]}: {record["count"]} relationships')

          # Check if DETERMINES creates Trinity-like groups
          query2 = '''
          MATCH (source)-[:DETERMINES]->(p:Product)
          WITH source, collect(p.category) as categories, collect(p.name) as products
          WHERE size(categories) >= 3
          RETURN source.name as source_name, categories, products
          ORDER BY size(categories) DESC
          '''

          print('\\nSources that DETERMINE multiple product categories:')
          result2 = session.run(query2)
          for record in result2:
              print(f'\\n{record["source_name"]}:')
              categories = record['categories']
              products = record['products']
              for i, (cat, prod) in enumerate(zip(categories, products)):
                  print(f'  {cat}: {prod}')

driver.close()
    