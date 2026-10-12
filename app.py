import os
import sqlite3
import requests

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "student_platform.db")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            marks REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# ---------------- GET MARKS ----------------

@app.route("/api/marks", methods=["GET"])
def get_marks():
    conn = get_db()

    try:
        rows = conn.execute(
            "SELECT * FROM marks ORDER BY id DESC"
        ).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        conn.close()


# ---------------- ADD MARKS ----------------

@app.route("/api/marks", methods=["POST"])
def add_marks():
    data = request.get_json(silent=True) or {}

    student_name = str(data.get("student_name", "")).strip()
    subject = str(data.get("subject", "")).strip()
    marks = data.get("marks")

    if not student_name or not subject or marks is None:
        return jsonify({
            "error": "student_name, subject and marks are required"
        }), 400

    try:
        marks = float(marks)

        if not 0 <= marks <= 100:
            return jsonify({
                "error": "Marks must be between 0 and 100"
            }), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Marks must be a number"}), 400

    conn = get_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO marks (student_name, subject, marks)
            VALUES (?, ?, ?)
            """,
            (student_name, subject, marks)
        )

        conn.commit()

        return jsonify({
            "message": "Marks added successfully",
            "id": cursor.lastrowid
        }), 201

    finally:
        conn.close()


# ---------------- UPDATE MARKS ----------------

@app.route("/api/marks/<int:mark_id>", methods=["PUT"])
def update_marks(mark_id):
    data = request.get_json(silent=True) or {}

    student_name = str(data.get("student_name", "")).strip()
    subject = str(data.get("subject", "")).strip()
    marks = data.get("marks")

    if not student_name or not subject or marks is None:
        return jsonify({"error": "All fields are required"}), 400

    try:
        marks = float(marks)

        if not 0 <= marks <= 100:
            return jsonify({"error": "Marks must be between 0 and 100"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Marks must be a number"}), 400

    conn = get_db()

    try:
        cursor = conn.execute(
            """
            UPDATE marks
            SET student_name = ?, subject = ?, marks = ?
            WHERE id = ?
            """,
            (student_name, subject, marks, mark_id)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404

        return jsonify({"message": "Marks updated successfully"})

    finally:
        conn.close()


# ---------------- DELETE MARKS ----------------

@app.route("/api/marks/<int:mark_id>", methods=["DELETE"])
def delete_marks(mark_id):
    conn = get_db()

    try:
        cursor = conn.execute(
            "DELETE FROM marks WHERE id = ?",
            (mark_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404

        return jsonify({"message": "Marks deleted successfully"})

    finally:
        conn.close()


# ---------------- OLLAMA AI ----------------

@app.route("/api/ai-study-coach", methods=["POST"])
def ai_study_coach():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Please enter a question"}), 400

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": (
                    "You are EduSuccess AI, a helpful student study coach. "
                    "Give clear and practical study advice.\n\n"
                    + question
                ),
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        answer = response.json().get("response", "")

        return jsonify({"answer": answer})

    except requests.RequestException as error:
        app.logger.error("Ollama error: %s", error)

        return jsonify({
            "error": "Ollama is unavailable. Check that Ollama is running."
        }), 503


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

