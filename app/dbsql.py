import mysql.connector
from datetime import datetime
import csv
import io

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
        fine INT NOT NULL,
        number_plate VARCHAR(20) DEFAULT NULL
    );
    """)
    
    # Add number_plate column if it doesn't exist (for existing databases)
    try:
        cur.execute("""
        ALTER TABLE violations 
        ADD COLUMN number_plate VARCHAR(20) DEFAULT NULL
        """)
        con.commit()
    except mysql.connector.Error:
        # Column already exists, ignore the error
        pass
    
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
        SELECT id, ts_utc, file_path, violation_type, fine, number_plate
        FROM violations
        ORDER BY ts_utc DESC
    """)
    violations = cur.fetchall()
    cur.close()
    con.close()
    return violations

def update_number_plate(violation_id, number_plate):
    """Update the number plate for a specific violation"""
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("""
        UPDATE violations 
        SET number_plate = %s 
        WHERE id = %s
    """, (number_plate, violation_id))
    con.commit()
    cur.close()
    con.close()

def delete_violation(violation_id):
    """Delete a specific violation from the database"""
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("""
        DELETE FROM violations 
        WHERE id = %s
    """, (violation_id,))
    con.commit()
    rows_affected = cur.rowcount
    cur.close()
    con.close()
    return rows_affected > 0

def delete_all_violations():
    """Delete all violations from the database"""
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("DELETE FROM violations")
    con.commit()
    rows_affected = cur.rowcount
    cur.close()
    con.close()
    return rows_affected

def export_violations_to_csv():
    """Export all violations to CSV format"""
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT id, ts_utc, violation_type, fine, number_plate
        FROM violations
        ORDER BY ts_utc DESC
    """)
    violations = cur.fetchall()
    cur.close()
    con.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Date & Time (UTC)', 'Violation Type', 'Fine Amount (₹)', 'Number Plate'])
    
    # Write data rows
    for violation in violations:
        writer.writerow([
            violation['id'],
            violation['ts_utc'],
            #violation['file_path'],
            violation['violation_type'],
            violation['fine'],
            violation['number_plate'] or ''
        ])
    
    output.seek(0)
    return output.getvalue()