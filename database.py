import sqlite3
import os

def get_db_connection():
    db_path = os.environ.get('DB_PATH', 'civic_issues.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    schema_path = 'schema.sql'
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
        conn.commit()
    else:
        print("Schema file not found!")
    
    conn.close()

if __name__ == "__main__":
    init_db()