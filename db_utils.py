import os
import streamlit as st
import pandas as pd
import sqlite3

# Try importing psycopg2, but don't fail if it's not installed (for local dev without it)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

# Configuration
LOCAL_DB_FILE = "database.db"

def get_connection():
    """
    Returns a database connection object.
    Checks st.secrets for 'DB_URL' to decide between Supabase (Postgres) and Local SQLite.
    """
    db_url = st.secrets.get("DB_URL")
    
    if db_url:
        # Cloud: Supabase / PostgreSQL
        if not psycopg2:
            st.error("psycopg2 is not installed. Please add it to requirements.txt")
            st.stop()
        try:
            conn = psycopg2.connect(db_url)
            return conn, "postgres"
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")
            st.stop()
    else:
        # Local: SQLite
        conn = sqlite3.connect(LOCAL_DB_FILE)
        # Enable row factory for dictionary-like access
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def run_query(query, params=None, fetch=False):
    """
    Executes a query against the configured database.
    Handles placeholder conversion (? -> %s) for Postgres.
    
    Args:
        query (str): SQL query with '?' placeholders.
        params (tuple/list): Parameters for the query.
        fetch (bool): If True, returns the result as a DataFrame (for SELECT).
                      If False, returns None (for INSERT/UPDATE/DELETE).
    """
    conn, db_type = get_connection()
    
    # Adjust placeholders for Postgres
    if db_type == "postgres":
        query = query.replace("?", "%s")
        
    try:
        if db_type == "postgres":
            cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cur = conn.cursor()
            
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
            
        if fetch:
            # Fetch data
            if db_type == "postgres":
                # RealDictCursor returns list of dicts
                data = cur.fetchall()
                df = pd.DataFrame(data)
            else:
                # sqlite3.Row needs conversion
                data = cur.fetchall()
                if data:
                    df = pd.DataFrame([dict(row) for row in data])
                else:
                    df = pd.DataFrame()
            conn.close()
            return df
        else:
            # Commit changes
            conn.commit()
            conn.close()
            return None
            
    except Exception as e:
        conn.close()
        raise e

def init_db():
    """Initializes the database table."""
    conn, db_type = get_connection()
    cur = conn.cursor()
    
    # Schema definition
    # Note: We use specific syntax for Auto-increment based on DB type
    if db_type == "postgres":
        id_col = "id SERIAL PRIMARY KEY"
    else:
        id_col = "id INTEGER PRIMARY KEY AUTOINCREMENT"

    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS patient_pro_records (
            {id_col},
            patient_id TEXT,
            visit_date TEXT,
            gender TEXT,
            age INTEGER,
            operation_date TEXT,
            surgeon TEXT,
            assistant TEXT,
            operation_type TEXT,
            procedure_type TEXT,
            follow_up_period TEXT,
            vas_score INTEGER,
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
            odi_score REAL,
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
    """
    
    try:
        cur.execute(create_table_sql)
        conn.commit()
    except Exception as e:
        st.error(f"Error initializing database: {e}")
    finally:
        conn.close()

def add_patient(data):
    """Adds a new patient record."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    sql = f'INSERT INTO patient_pro_records ({columns}) VALUES ({placeholders})'
    run_query(sql, list(data.values()))

def get_all_patients():
    """Retrieves all patient records."""
    return run_query("SELECT * FROM patient_pro_records", fetch=True)

def update_patient(record_id, data):
    """Updates an existing patient record."""
    # Remove 'id' if present
    if 'id' in data:
        del data['id']
        
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    sql = f'UPDATE patient_pro_records SET {set_clause} WHERE id = ?'
    
    params = list(data.values())
    params.append(record_id)
    
    run_query(sql, params)

def delete_patient(record_id):
    """Deletes a patient record."""
    run_query("DELETE FROM patient_pro_records WHERE id = ?", (record_id,))

def get_patient_history(patient_id):
    """Retrieves the most recent visit for a patient."""
    df = run_query("SELECT * FROM patient_pro_records WHERE patient_id = ? ORDER BY id DESC LIMIT 1", (patient_id,), fetch=True)
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def check_duplicate_visit(patient_id, follow_up_period, visit_date):
    """
    Checks if a visit already exists for the given patient_id, follow_up_period, and visit_date.
    Returns True if a duplicate exists, False otherwise.
    """
    query = "SELECT id FROM patient_pro_records WHERE patient_id = ? AND follow_up_period = ? AND visit_date = ?"
    df = run_query(query, (patient_id, follow_up_period, visit_date), fetch=True)
    return not df.empty

# Initialize on import
init_db()
