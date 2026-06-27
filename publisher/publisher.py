import paho.mqtt.client as mqtt
import json
import time
import random

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)

print("Sensor simulator started! Sending readings every 3 seconds...")
print("Press Ctrl+C to stop\n")

counter = 1
while True:
    temp_data = {
        "device_id": f"sensor_00{(counter % 5) + 1}",
        "temperature": round(random.uniform(18.0, 35.0), 2),
        "humidity": round(random.uniform(30.0, 80.0), 2)
    }
    client.publish("sensors/temperature", json.dumps(temp_data))
    print(f"Sent temperature: {temp_data}")

    reading_data = {
        "device_id": f"sensor_00{(counter % 5) + 1}",
        "temperature": temp_data["temperature"],
        "humidity": temp_data["humidity"],
        "air_quality": round(random.uniform(0.0, 100.0), 2),
        "battery": round(random.uniform(50.0, 100.0), 2)
    }
    client.publish("sensors/readings", json.dumps(reading_data))
    print(f"Sent full reading: {reading_data}")

    network_data = {
        "device_id": f"sensor_00{(counter % 5) + 1}",
        "gateway_id": "gateway_001"
    }
    client.publish("sensors/network", json.dumps(network_data))
    print(f"Sent network event: {network_data}\n")

    counter += 1
    time.sleep(3)
