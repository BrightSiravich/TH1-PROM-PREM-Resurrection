import sqlite3
import pandas as pd
import os

# Database file path
DB_FILE = "patients.db"

def init_db():
    """Initializes the database with the patient_visits table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create table matching the CSV schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hn TEXT,
            visit_date TEXT,
            -- visit_time TEXT, -- Removed
            gender TEXT,
            age INTEGER,
            operation_date TEXT,
            surgeon TEXT,
            assistant TEXT,
            operation_type TEXT,
            procedure_type TEXT,
            follow_up_period TEXT,
            pain_score INTEGER,
            odi_q1 INTEGER,
            odi_q2 INTEGER,
            odi_q3 INTEGER,
            odi_q4 INTEGER,
            odi_q5 INTEGER,
            odi_q6 INTEGER,
            odi_q7 INTEGER,
            odi_q8 INTEGER,
            odi_q9 INTEGER,
            odi_q10 INTEGER,
            odi_score_percent REAL,
            eq5d_1 INTEGER,
            eq5d_2 INTEGER,
            eq5d_3 INTEGER,
            eq5d_4 INTEGER,
            eq5d_5 INTEGER,
            eq5d_score REAL,
            health_status INTEGER,
            satisfaction_score INTEGER,
            note TEXT
        )
    ''')
    
    # Migration: Add procedure_type column if it doesn't exist
    try:
        c.execute("ALTER TABLE patient_visits ADD COLUMN procedure_type TEXT")
    except sqlite3.OperationalError:
        # Column likely already exists
        pass
        
    conn.commit()
    conn.close()

def add_visit(data):
    """Adds a new patient visit record to the database.
    
    Args:
        data (dict): A dictionary containing all the field values.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Prepare the SQL query dynamically based on keys
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    sql = f'INSERT INTO patient_visits ({columns}) VALUES ({placeholders})'
    
    c.execute(sql, list(data.values()))
    conn.commit()
    conn.close()

def get_all_visits():
    """Retrieves all records from the database as a pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    # Read sql query into pandas dataframe
    df = pd.read_sql_query("SELECT * FROM patient_visits", conn)
    conn.close()
    return df

def delete_visit(visit_id):
    """Deletes a visit record by ID."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM patient_visits WHERE id=?", (visit_id,))
    conn.commit()
    conn.close()

def update_visit(visit_id, data):
    """Updates an existing visit record.
    
    Args:
        visit_id (int): The ID of the visit to update.
        data (dict): A dictionary containing the fields to update.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Remove 'id' from data if present to avoid updating primary key
    if 'id' in data:
        del data['id']
        
    # Prepare the SQL query dynamically
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    sql = f'UPDATE patient_visits SET {set_clause} WHERE id = ?'
    
    values = list(data.values())
    values.append(visit_id)
    
    c.execute(sql, values)
    conn.commit()
    conn.close()

def get_patient_history(hn):
    """Retrieves all visits for a specific HN to help with auto-filling."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM patient_visits WHERE hn=? ORDER BY id DESC LIMIT 1", (hn,))
    row = c.fetchone()
    conn.close()
    
    if row:
        # Map the row back to a dictionary (simplified, assumes we know the order or use row_factory)
        # For simplicity in this helper, we'll just return the raw row if found, 
        # but a better approach for auto-fill is to return a dict.
        # Let's use pandas for easier dict conversion
        df = get_all_visits()
        patient_df = df[df['hn'] == hn].sort_values(by='id', ascending=False)
        if not patient_df.empty:
            return patient_df.iloc[0].to_dict()
            
    return None

# Initialize DB on module load (safe to run multiple times)
init_db()
