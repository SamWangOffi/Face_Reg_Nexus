import psycopg2

# === Connect to PostgreSQL ===
try:
    conn = psycopg2.connect(
        dbname="smart_tour",
        user="postgres",
        password="123456",  # ⚠️ Replace with your actual password
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("✅ Connected to PostgreSQL database successfully.")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# === SQL Statements to Create Tables ===
sql_commands = [
    """
    CREATE TABLE IF NOT EXISTS face_encoding (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        encoding FLOAT8[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS group_status_log (
        id SERIAL PRIMARY KEY,
        current_count INTEGER,
        total_count INTEGER,
        status VARCHAR(50),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS visitor_event_log (
        id SERIAL PRIMARY KEY,
        visitor_name VARCHAR(100),
        matched_from_encoding_id INTEGER REFERENCES face_encoding(id),
        detected_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS visitor_schedule (
        id SERIAL PRIMARY KEY,
        visitor_name VARCHAR(100),
        company VARCHAR(100),
        visit_start TIMESTAMP,
        visit_end TIMESTAMP,
        tour_lead VARCHAR(100)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS warning_log (
        id SERIAL PRIMARY KEY,
        current_count INTEGER,
        status VARCHAR(50),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

# === Execute SQL Commands ===
try:
    for command in sql_commands:
        cursor.execute(command)
    conn.commit()
    print("✅ All tables created successfully.")
except Exception as e:
    print(f"❌ Failed to create tables: {e}")
    conn.rollback()

# === Close Connection ===
cursor.close()
conn.close()
