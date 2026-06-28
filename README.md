# Environmental Monitoring — MQTT, Python & Multi-Database Integration

IoT Environmental Monitoring system using MQTT, Python, MySQL, MongoDB and Neo4j.

## What it does

Simulated IoT sensors publish data to a Mosquitto MQTT broker. A Python application subscribes to the broker, receives each message in real time, and routes it to the database that best matches its structure:

```
Sensors → Mosquitto Broker → Python Router → MySQL / MongoDB / Neo4j
```

| MQTT Topic | Data | Database | Why |
|---|---|---|---|
| `sensors/temperature` | Temperature & humidity | MySQL | Fixed fields → relational table |
| `sensors/readings` | Full reading + air quality + battery | MongoDB | Optional fields → flexible document |
| `sensors/network` | Device → gateway connection | Neo4j | Relationship data → graph |

## Project Structure

```
environmental-monitoring/
├── docker-compose.yml          # Launches all 4 services
├── mosquitto/
│   ├── config/mosquitto.conf   # Broker configuration
│   ├── data/                   # Persistence files (auto-generated)
│   └── log/                    # Broker logs (auto-generated)
├── databases/
│   ├── setup_mysql.py          # Creates the sensor_readings table
│   └── setup_neo4j.py          # Seeds initial graph nodes
├── publisher/
│   └── publisher.py            # Sensor simulator (publishes messages)
└── subscriber/
    └── router.py               # Subscribes and routes to databases
```

## Technologies

| Technology | Role | Version |
|---|---|---|
| Docker / Compose | Orchestrates all services | Engine 29.x |
| Eclipse Mosquitto | MQTT broker | 2.x |
| Python + Paho MQTT | Simulator and router | 3.14 / paho 2.1 |
| MySQL | Relational storage for temperature readings | 8.0 |
| MongoDB | Document storage for full sensor readings | 7 |
| Neo4j | Graph storage for device network | 5 |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Python 3.10+
- Python dependencies:

```bash
pip install paho-mqtt pymysql pymongo neo4j
```

## How to Run

### 1. Start all services
```bash
docker compose up -d
```
This starts Mosquitto, MySQL, MongoDB and Neo4j in the background.

### 2. Set up the databases (run once)
```bash
python3 databases/setup_mysql.py
python3 databases/setup_neo4j.py
```

### 3. Start the router (subscriber)
```bash
python3 subscriber/router.py
```
Leave this running — it waits for incoming messages and routes them to the correct database.

### 4. Start the sensor simulator (publisher)
In a new terminal:
```bash
python3 publisher/publisher.py
```
This continuously publishes simulated sensor data every 3 seconds. Press `Ctrl+C` to stop.

## How it works

The routing logic in `router.py` is driven entirely by the MQTT topic:

```python
def on_message(client, userdata, message):
    topic   = message.topic
    payload = json.loads(message.payload.decode())

    if topic == "sensors/temperature":
        save_to_mysql(payload)      # uniform reading  → relational
    elif topic == "sensors/readings":
        save_to_mongodb(payload)    # full document    → document store
    elif topic == "sensors/network":
        save_to_neo4j(payload)      # device link      → graph
```

## Ports

| Service | Host Port | Notes |
|---|---|---|
| Mosquitto | 1883 | Standard MQTT port |
| MySQL | 3307 | Mapped to 3307 to avoid conflict with local MySQL on 3306 |
| MongoDB | 27017 | Standard MongoDB port |
| Neo4j Browser | 7474 | Web UI: http://localhost:7474 |
| Neo4j Bolt | 7687 | Python driver connection |

## Notes

- **Anonymous MQTT access** is enabled (`allow_anonymous true`) — suitable for local development only. In production, disable this and configure TLS + authentication.
- **Hardcoded credentials** are used for simplicity. In production, use environment variables or a secrets manager.
- **py2neo was not used** — it is no longer maintained and incompatible with Neo4j 5. The official `neo4j` Python driver is used instead.

## Source code

GitHub: [github.com/omermeftuhibrahim/environmental-monitoring](https://github.com/omermeftuhibrahim/environmental-monitoring)

## Author

Omer Meftuh Ibrahim — Università degli Studi di Messina  
Databases — Module B (NoSQL) — Project DB-B1  
Course Instructor: Prof. Ruggeri
