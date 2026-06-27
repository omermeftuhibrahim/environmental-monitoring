import paho.mqtt.client as mqtt
import pymysql
import pymongo
from neo4j import GraphDatabase
import json
from datetime import datetime

mysql_conn = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="root1234",
    database="environmental_db"
)
mysql_cursor = mysql_conn.cursor()

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["environmental_db"]
mongo_collection = mongo_db["sensor_readings"]

neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j1234")
)

def save_to_mysql(data):
    mysql_cursor.execute(
        "INSERT INTO sensor_readings (device_id, temperature, humidity) VALUES (%s, %s, %s)",
        (data["device_id"], data["temperature"], data["humidity"])
    )
    mysql_conn.commit()
    print(f"  -> MySQL: saved temperature {data['temperature']}C humidity {data['humidity']}%")

def save_to_mongodb(data):
    data["timestamp"] = datetime.now().isoformat()
    mongo_collection.insert_one(data)
    print(f"  -> MongoDB: saved full reading from {data['device_id']}")

def save_to_neo4j(data):
    with neo4j_driver.session() as session:
        session.run(
            "MERGE (d:Device {device_id: $device_id}) "
            "MERGE (g:Gateway {gateway_id: $gateway_id}) "
            "MERGE (d)-[:CONNECTS_TO {timestamp: $timestamp}]->(g)",
            device_id=data["device_id"],
            gateway_id=data["gateway_id"],
            timestamp=str(datetime.now())
        )
    print(f"  -> Neo4j: saved connection {data['device_id']} -> {data['gateway_id']}")

def on_message(client, userdata, message):
    topic = message.topic
    payload = json.loads(message.payload.decode())
    print(f"\nMessage received on topic: {topic}")
    if topic == "sensors/temperature":
        save_to_mysql(payload)
    elif topic == "sensors/readings":
        save_to_mongodb(payload)
    elif topic == "sensors/network":
        save_to_neo4j(payload)

def on_connect(client, userdata, flags, rc, properties=None):
    print("Router connected to Mosquitto!")
    client.subscribe("sensors/temperature")
    client.subscribe("sensors/readings")
    client.subscribe("sensors/network")
    print("Subscribed to all topics. Waiting for messages...")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)
client.loop_forever()
