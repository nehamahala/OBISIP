from flask import Flask, render_template
import secrets
import string

app = Flask(__name__)

SETS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/generate")
def generate():
    from flask import request, jsonify
    data = request.get_json(silent=True) or {}
    try:
        length = int(data.get("length", 12))
    except (TypeError, ValueError):
        return jsonify({"error": "Please enter a valid whole number."}), 400

    if length < 8 or length > 128:
        return jsonify({"error": "Password length must be between 8 and 128."}), 400

    chosen = []
    for key in ("uppercase", "lowercase", "numbers", "symbols"):
        if data.get(key, True):
            chosen.append(SETS[key])

    if not chosen:
        return jsonify({"error": "Select at least one character type."}), 400

    # Keep the selection balanced by guaranteeing one character from
    # each selected group, then securely fill and shuffle the remainder.
    chars = [secrets.choice(group) for group in chosen]
    pool = "".join(chosen)
    chars.extend(secrets.choice(pool) for _ in range(length - len(chars)))
    secrets.SystemRandom().shuffle(chars)

    return jsonify({"password": "".join(chars)})

if __name__ == "__main__":
    import threading, webbrowser
    threading.Timer(1.0, lambda: webbrowser.open_new("http://127.0.0.1:5001")).start()
    app.run(host="127.0.0.1", port=5001, debug=False)
