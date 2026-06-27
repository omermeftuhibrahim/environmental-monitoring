from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j1234")
)

with driver.session() as session:
    session.run("""
        MERGE (d:Device {device_id: 'sensor_001', type: 'climate', location: 'Room A'})
        MERGE (d2:Device {device_id: 'sensor_002', type: 'climate', location: 'Room B'})
        MERGE (g:Gateway {gateway_id: 'gateway_001', location: 'Building A'})
        MERGE (d)-[:CONNECTS_TO]->(g)
        MERGE (d2)-[:CONNECTS_TO]->(g)
    """)
    print("Neo4j graph created successfully!")

driver.close()
