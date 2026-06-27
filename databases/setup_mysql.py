import pymysql
import time

time.sleep(5)

conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='root1234',
    database='environmental_db'
)

cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        device_id VARCHAR(50),
        temperature FLOAT,
        humidity FLOAT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("MySQL table created successfully!")
