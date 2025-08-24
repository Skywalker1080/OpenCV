import mysql.connector
from datetime import datetime

# Update these with your MySQL credentials
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sanjay@123",
    "database": "traffic_db"
}

def init_db():
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS violations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ts_utc VARCHAR(32) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        violation_type VARCHAR(64) NOT NULL,
        fine INT NOT NULL
    );
    """)
    con.commit()
    cur.close()
    con.close()

def insert_violation(file_path, violation_type, fine):
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO violations (ts_utc, file_path, violation_type, fine)
        VALUES (%s, %s, %s, %s)
    """, (datetime.utcnow().isoformat(), file_path, violation_type, fine))
    con.commit()
    cur.close()
    con.close()

def get_all_violations():
    """Retrieve all violations from the database"""
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT id, ts_utc, file_path, violation_type, fine
        FROM violations
        ORDER BY ts_utc DESC
    """)
    violations = cur.fetchall()
    cur.close()
    con.close()
    return violations