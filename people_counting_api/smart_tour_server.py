from flask import Flask, jsonify, request
import psycopg2
import click

app = Flask(__name__)

# === PostgreSQL Connection Info ===
DB_CONFIG = {
    "dbname": "smart_tour",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# === Flask CLI Command to Initialize Tables ===
@app.cli.command("init-db")
def init_db():
    conn = get_db_connection()
    if not conn:
        exit(1)
    cursor = conn.cursor()

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
            matched_from_encoding_id INTEGER REFERENCES face_encoding(id) ON DELETE SET NULL,
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

    try:
        for command in sql_commands:
            cursor.execute(command)
        conn.commit()
        print("All tables created successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Failed to create tables: {e}")
    finally:
        cursor.close()
        conn.close()

# === In-memory shared group state ===
group_data = {
    "current_count": 0,
    "total_count": 0,
    "status": "WAITING"
}

@app.route("/group_status", methods=["GET"])
def get_group_status():
    return jsonify(group_data)

@app.route("/update_group_status", methods=["POST"])
def update_group_status():
    data = request.get_json()
    group_data["current_count"] = data.get("current_count", group_data["current_count"])
    group_data["total_count"] = data.get("total_count", group_data["total_count"])
    group_data["status"] = data.get("status", group_data["status"])

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO group_status_log (current_count, total_count, status)
            VALUES (%s, %s, %s)
            """,
            (
                group_data["current_count"],
                group_data["total_count"],
                group_data["status"]
            )
        )
        conn.commit()
        print(f"Logged to DB: {group_data}")
    except Exception as e:
        conn.rollback()
        print(f"DB write failed: {e}")
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Group status updated successfully."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
