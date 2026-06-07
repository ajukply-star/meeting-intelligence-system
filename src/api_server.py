from flask import Flask, request, jsonify
import json
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DB_PATH = "data/meetings.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            date TEXT,
            participants TEXT,
            summary TEXT,
            action_items TEXT,
            decisions TEXT,
            risks TEXT,
            follow_up_needed INTEGER,
            follow_up_reason TEXT,
            parking_lot TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id TEXT PRIMARY KEY,
            meeting_id TEXT,
            task TEXT,
            assignee TEXT,
            deadline TEXT,
            priority TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized.")


def save_meeting_to_db(meeting_data: dict):
    import uuid
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    meeting_id = meeting_data.get("meeting_id", str(uuid.uuid4()))

    cursor.execute("""
        INSERT OR REPLACE INTO meetings
        (id, date, participants, summary, action_items, decisions,
         risks, follow_up_needed, follow_up_reason, parking_lot, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting_id,
        meeting_data.get("date", datetime.now().isoformat()),
        json.dumps(meeting_data.get("participants", [])),
        meeting_data.get("summary", ""),
        json.dumps(meeting_data.get("action_items", [])),
        json.dumps(meeting_data.get("decisions", [])),
        json.dumps(meeting_data.get("risks", [])),
        1 if meeting_data.get("follow_up_needed") else 0,
        meeting_data.get("follow_up_reason"),
        json.dumps(meeting_data.get("parking_lot", [])),
        datetime.now().isoformat()
    ))

    for i, item in enumerate(meeting_data.get("action_items", [])):
        import uuid as _uuid
        cursor.execute("""
            INSERT OR REPLACE INTO action_items
            (id, meeting_id, task, assignee, deadline, priority, completed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            str(_uuid.uuid4()),
            meeting_id,
            item.get("task", ""),
            item.get("assignee", "Unassigned"),
            item.get("deadline", ""),
            item.get("priority", "medium")
        ))

    conn.commit()
    conn.close()
    return meeting_id


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Meeting Intelligence API is running"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Main endpoint. Receives transcript text, returns full intelligence JSON.
    N8N calls this endpoint.
    """
    try:
        data = request.json

        if not data or "transcript" not in data:
            return jsonify({"error": "Missing 'transcript' field in request body"}), 400

        transcript_text = data["transcript"]
        participants = data.get("participants", [])

        from extract_intelligence import extract_intelligence, add_metadata
        from transcribe import format_transcript_for_llm

        if isinstance(transcript_text, list):
            dummy = {"utterances": transcript_text}
            transcript_text = format_transcript_for_llm(dummy)

        result = extract_intelligence(transcript_text)
        result["participants"] = participants

        from datetime import datetime
        import uuid
        result["meeting_id"] = str(uuid.uuid4())
        result["date"] = datetime.now().isoformat()

        meeting_id = save_meeting_to_db(result)
        result["meeting_id"] = meeting_id

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/meetings", methods=["GET"])
def get_meetings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, summary, follow_up_needed FROM meetings ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    meetings = [
        {"id": r[0], "date": r[1], "summary": r[2], "follow_up_needed": bool(r[3])}
        for r in rows
    ]
    return jsonify(meetings)


@app.route("/action_items", methods=["GET"])
def get_action_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, meeting_id, task, assignee, deadline, priority, completed
        FROM action_items
        ORDER BY deadline ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    items = [
        {
            "id": r[0], "meeting_id": r[1], "task": r[2],
            "assignee": r[3], "deadline": r[4],
            "priority": r[5], "completed": bool(r[6])
        }
        for r in rows
    ]
    return jsonify(items)


@app.route("/action_items/<item_id>/complete", methods=["POST"])
def mark_complete(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE action_items SET completed = 1, completed_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), item_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


if __name__ == "__main__":
    init_db()
    print("Starting Flask API on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)