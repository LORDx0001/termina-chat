from flask import Flask, request, jsonify
import subprocess, socket, sqlite3, os

app = Flask(__name__)
DB = "ports.db"
SERVER = "server.py"

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    return s.getsockname()[1]

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            port INTEGER PRIMARY KEY,
            launched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def save_port(port):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO rooms (port) VALUES (?)", (port,))
    conn.commit()

@app.route("/launch", methods=["POST"])
def launch():
    port = get_free_port()
    subprocess.Popen(['python3', SERVER, str(port)])
    save_port(port)
    return jsonify({"port": port})

@app.route("/rooms")
def rooms():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT port, launched_at FROM rooms ORDER BY launched_at DESC").fetchall()
    return jsonify([{"port": r[0], "launched_at": r[1]} for r in rows])

@app.route("/status")
def status():
    port = int(request.args.get("port", 0))
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', port))
    return jsonify({"port": port, "open": result == 0})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

