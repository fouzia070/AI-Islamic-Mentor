# ================================================
# Main Flask Application
# ================================================

from flask import Flask, request, jsonify, render_template, session
from config import DEBUG, SECRET_KEY
from ai.chains import generate_response
from utils.helpers import validate_question, format_response
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = SECRET_KEY

# History file path
HISTORY_FILE = "history.json"

# -----------------------------------------------
# Load History from JSON file
# -----------------------------------------------
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return {}
    except Exception:
        return {}


# -----------------------------------------------
# Save History to JSON file
# -----------------------------------------------
def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"History save error: {e}")


# -----------------------------------------------
# Homepage Route
# -----------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------------------------
# Login Page Route
# -----------------------------------------------
@app.route("/login")
def login():
    return render_template("login.html")


# -----------------------------------------------
# Register Page Route
# -----------------------------------------------
@app.route("/register")
def register():
    return render_template("register.html")


# -----------------------------------------------
# History Page Route
# -----------------------------------------------
@app.route("/history")
def history():
    return render_template("history.html")


# -----------------------------------------------
# Save User Session After Login
# -----------------------------------------------
@app.route("/save-session", methods=["POST"])
def save_session():
    data = request.json
    session["user_email"] = data.get("email", "")
    session["user_name"]  = data.get("name", "Guest")
    session.permanent     = True
    print(f"Session saved for: {session['user_email']}")
    return jsonify({"success": True})


# -----------------------------------------------
# Logout Route
# -----------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


# -----------------------------------------------
# Get User History
# -----------------------------------------------
@app.route("/get-history", methods=["POST"])
def get_history():
    data  = request.json
    email = data.get("email", "")
    if not email:
        return jsonify({"history": []})

    hist         = load_history()
    user_history = hist.get(email, [])
    return jsonify({"history": user_history[-20:]})


# -----------------------------------------------
# Save Updated History (for delete functionality)
# -----------------------------------------------
@app.route("/save-history", methods=["POST"])
def save_history_route():
    data    = request.json
    email   = data.get("email", "")
    history = data.get("history", [])
    if not email:
        return jsonify({"success": False})
    try:
        hist = load_history()
        hist[email] = list(reversed(history))
        save_history(hist)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# -----------------------------------------------
# Main API Route — Ask Islamic Question
# -----------------------------------------------
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data          = request.json
        user_question = data.get("question", "").strip()

        # Validate question
        is_valid, message = validate_question(user_question)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Generate AI response
        result           = generate_response(user_question)
        formatted_answer = format_response(result["answer"])

        # Save to history if user is logged in
        try:
            email = data.get("email", "") or session.get("user_email", "")
            if email:
                hist = load_history()
                if email not in hist:
                    hist[email] = []
                hist[email].append({
                    "question" : str(user_question)[:200],
                    "answer"   : str(formatted_answer)[:3000],  
                    "type"     : str(result["query_type"]),
                    "time"     : datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_history(hist)
        except Exception:
            pass

        return jsonify({
            "answer"    : formatted_answer,
            "query_type": result["query_type"],
            "success"   : result["success"]
        })

    except Exception as e:
        return jsonify({
            "error"  : f"Something went wrong: {str(e)}",
            "success": False
        }), 500


if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("🕌 AI Islamic Mentor is starting...")
    print("🌐 Running on Hugging Face Space")
    app.run(debug=False, host="0.0.0.0", port=7860, use_reloader=False)
