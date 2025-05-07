from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime

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
        print(f" Failed to connect to PostgreSQL: {e}")
        return None

# === POST & GET handler for warning ===
@app.route("/warning", methods=["GET", "POST"])
def handle_warning():
    if request.method == "GET":
        return jsonify({"message": "⚙️ Warning API is running."}), 200

    data = request.get_json()
    print(" Warning received!")
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Current Count: {data.get('current_count')}")
    print(f"Status: {data.get('status')}")
    print(f"Company: {data.get('company', 'Unknown')}")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO warning_log (current_count, status, timestamp, company)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    data.get("current_count"),
                    data.get("status"),
                    data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    data.get("company", "Unknown")
                )
            )
            conn.commit()
            print(" Warning logged to database.")
        except Exception as e:
            conn.rollback()
            print(f" Failed to insert warning: {e}")
        finally:
            cursor.close()
            conn.close()

    return jsonify({"message": "Warning received successfully."}), 200

# === Optional: retrieve recent warning logs ===
@app.route("/warnings", methods=["GET"])
def get_recent_warnings():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, current_count, status, timestamp, company
            FROM warning_log
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        result = [
            {
                "id": r[0],
                "current_count": r[1],
                "status": r[2],
                "timestamp": r[3].strftime("%Y-%m-%d %H:%M:%S"),
                "company": r[4]
            } for r in rows
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Query failed: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)
