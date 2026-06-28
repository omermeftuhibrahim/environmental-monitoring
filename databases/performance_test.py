import pymysql
import pymongo
from neo4j import GraphDatabase
import time
import statistics
import random
from datetime import datetime

# ─────────────────────────────────────────────
# Database connections
# ─────────────────────────────────────────────

mysql_conn = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="root1234",
    database="environmental_db"
)
mysql_cursor = mysql_conn.cursor()

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_collection = mongo_client["environmental_db"]["sensor_readings"]

neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j1234")
)

# ─────────────────────────────────────────────
# Helper: generate fake sensor data
# ─────────────────────────────────────────────

def make_data(i):
    device_id = f"sensor_00{(i % 5) + 1}"
    temperature = round(random.uniform(18.0, 35.0), 2)
    humidity = round(random.uniform(30.0, 80.0), 2)
    return {
        "device_id": device_id,
        "temperature": temperature,
        "humidity": humidity,
        "air_quality": round(random.uniform(0.0, 100.0), 2),
        "battery": round(random.uniform(50.0, 100.0), 2),
        "gateway_id": "gateway_001"
    }

# ─────────────────────────────────────────────
# Write functions (same logic as router.py)
# ─────────────────────────────────────────────

def write_mysql(data):
    mysql_cursor.execute(
        "INSERT INTO sensor_readings (device_id, temperature, humidity) VALUES (%s, %s, %s)",
        (data["device_id"], data["temperature"], data["humidity"])
    )
    mysql_conn.commit()

def write_mongodb(data):
    doc = dict(data)
    doc["timestamp"] = datetime.now().isoformat()
    mongo_collection.insert_one(doc)

def write_neo4j(data):
    with neo4j_driver.session() as session:
        session.run(
            "MERGE (d:Device {device_id: $device_id}) "
            "MERGE (g:Gateway {gateway_id: $gateway_id}) "
            "MERGE (d)-[:CONNECTS_TO {timestamp: $timestamp}]->(g)",
            device_id=data["device_id"],
            gateway_id=data["gateway_id"],
            timestamp=str(datetime.now())
        )

# ─────────────────────────────────────────────
# Test 1: Per-write latency (100 writes each)
# ─────────────────────────────────────────────

def test_latency(n=100):
    print(f"\n{'='*55}")
    print(f"  TEST 1: Per-write latency ({n} writes per database)")
    print(f"{'='*55}")

    results = {"MySQL": [], "MongoDB": [], "Neo4j": []}

    for i in range(n):
        data = make_data(i)

        # MySQL
        t0 = time.perf_counter()
        write_mysql(data)
        results["MySQL"].append((time.perf_counter() - t0) * 1000)

        # MongoDB
        t0 = time.perf_counter()
        write_mongodb(data)
        results["MongoDB"].append((time.perf_counter() - t0) * 1000)

        # Neo4j
        t0 = time.perf_counter()
        write_neo4j(data)
        results["Neo4j"].append((time.perf_counter() - t0) * 1000)

    print(f"\n  {'Database':<12} {'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10} {'StdDev':>10}")
    print(f"  {'-'*52}")
    for db, times in results.items():
        print(f"  {db:<12} {statistics.mean(times):>10.2f} {min(times):>10.2f} {max(times):>10.2f} {statistics.stdev(times):>10.2f}")

    return results

# ─────────────────────────────────────────────
# Test 2: Throughput at increasing message rates
# ─────────────────────────────────────────────

def test_throughput(rates=[1, 5, 10, 20, 50]):
    print(f"\n{'='*55}")
    print(f"  TEST 2: Throughput (messages per second)")
    print(f"{'='*55}")
    print(f"\n  {'Target msg/s':>14} {'Actual msg/s':>14} {'Avg latency ms':>16} {'Dropped':>10}")
    print(f"  {'-'*56}")

    for rate in rates:
        interval = 1.0 / rate   # seconds between messages
        n = rate * 5            # run for 5 seconds worth of messages
        latencies = []
        dropped = 0

        start_total = time.perf_counter()
        for i in range(n):
            t0 = time.perf_counter()
            data = make_data(i)
            try:
                write_mysql(data)
                write_mongodb(data)
                write_neo4j(data)
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception:
                dropped += 1

            # sleep only if we finished faster than the interval
            elapsed = time.perf_counter() - t0
            if elapsed < interval:
                time.sleep(interval - elapsed)

        total_time = time.perf_counter() - start_total
        actual_rate = n / total_time
        avg_lat = statistics.mean(latencies) if latencies else 0

        print(f"  {rate:>14} {actual_rate:>14.1f} {avg_lat:>16.2f} {dropped:>10}")

# ─────────────────────────────────────────────
# Test 3: Reliability — 200 consecutive writes
# ─────────────────────────────────────────────

def test_reliability(n=200):
    print(f"\n{'='*55}")
    print(f"  TEST 3: Reliability ({n} consecutive writes)")
    print(f"{'='*55}")

    success = 0
    failed = 0

    for i in range(n):
        data = make_data(i)
        try:
            write_mysql(data)
            write_mongodb(data)
            write_neo4j(data)
            success += 1
        except Exception as e:
            failed += 1
            print(f"  [ERROR] Write {i} failed: {e}")

    print(f"\n  Total writes : {n}")
    print(f"  Successful   : {success}")
    print(f"  Failed       : {failed}")
    print(f"  Success rate : {(success/n)*100:.1f}%")

# ─────────────────────────────────────────────
# Run all tests
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  ENVIRONMENTAL MONITORING — PERFORMANCE TESTS")
    print("="*55)
    print("  Make sure docker compose is running before starting.")

    test_latency(n=100)
    test_throughput(rates=[1, 5, 10, 20, 50])
    test_reliability(n=200)

    print(f"\n{'='*55}")
    print("  All tests complete.")
    print(f"{'='*55}\n")

    mysql_conn.close()
    mongo_client.close()
    neo4j_driver.close()
