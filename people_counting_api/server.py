from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

# === Initialize PostgreSQL connection ===
try:
    conn = psycopg2.connect(
        dbname="smart_tour",       # Your database name
        user="postgres",           # Your database username
        password="123456",         # ⚠️ Replace with your actual password
        host="localhost",          # Use IP if remote
        port="5432"
    )
    cursor = conn.cursor()
    print("✅ Successfully connected to PostgreSQL database.")
except Exception as e:
    print(f"❌ Failed to connect to PostgreSQL: {e}")
    exit(1)

# === In-memory shared group state (accessible via GET) ===
group_data = {
    "current_count": 0,
    "total_count": 0,
    "status": "WAITING"
}

# === GET endpoint: used by frontend or other systems to fetch status ===
@app.route("/group_status", methods=["GET"])
def get_group_status():
    return jsonify(group_data)

# === POST endpoint: called by tracking module to update group status ===
@app.route("/update_group_status", methods=["POST"])
def update_group_status():
    data = request.get_json()

    # Update memory state
    group_data["current_count"] = data.get("current_count", group_data["current_count"])
    group_data["total_count"] = data.get("total_count", group_data["total_count"])
    group_data["status"] = data.get("status", group_data["status"])

    # Log to PostgreSQL
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
        print(f"📝 Status logged to database: {group_data}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to write to database: {e}")

    return jsonify({"message": "Group status updated successfully."}), 200

# === Run Flask app ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
