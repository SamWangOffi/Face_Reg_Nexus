from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/warning', methods=['POST'])
def warning():
    data = request.get_json()
    print("🚨 收到报警！")
    print(f"时间戳: {data.get('timestamp')}")
    print(f"当前人数: {data.get('current_count')}")
    print(f"状态: {data.get('status')}")
    return jsonify({"message": "Warning received successfully."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)
