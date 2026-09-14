from flask import Flask, render_template, request, jsonify
import ast
import datetime as dt
import math
import operator
import webbrowser

app = Flask(__name__)

ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod
}
ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def safe_calculate(expression):
    expression = (expression.lower()
                  .replace("times", "*").replace("multiplied by", "*")
                  .replace("divided by", "/").replace("plus", "+")
                  .replace("minus", "-").replace("^", "**").replace("π", str(math.pi)))
    names = {"pi": math.pi, "e": math.e, "sqrt": math.sqrt,
             "sin": math.sin, "cos": math.cos, "tan": math.tan,
             "log": math.log10, "ln": math.log, "abs": abs}

    def visit(node):
        if isinstance(node, ast.Expression): return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
            return ALLOWED_BINOPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
            return ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Name) and node.id in names: return names[node.id]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names:
            return names[node.func.id](*(visit(a) for a in node.args))
        raise ValueError("Unsupported expression")
    value = visit(ast.parse(expression, mode="eval"))
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Invalid result")
    return value

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/command")
def command():
    text = (request.json or {}).get("text", "").strip().lower()
    if not text:
        return jsonify({"reply": "I didn't hear a command."})

    if "time" in text and "timer" not in text:
        return jsonify({"reply": f"The current time is {dt.datetime.now().strftime('%I:%M %p')}."})
    if "date" in text or "today" in text:
        return jsonify({"reply": f"Today is {dt.datetime.now().strftime('%A, %d %B %Y')}."})

    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "maps": "https://maps.google.com",
        "linkedin": "https://www.linkedin.com",
    }
    for key, url in sites.items():
        if text in {key, f"open {key}"}:
            return jsonify({"reply": f"Opening {key.capitalize()}.", "open_url": url})

    if text.startswith("search "):
        q = text[7:].strip()
        return jsonify({"reply": f"Searching for {q}.",
                        "open_url": "https://www.google.com/search?q=" + q.replace(" ", "+")})

    if text.startswith("weather"):
        place = text.replace("weather", "", 1).replace("in", "", 1).strip() or "my location"
        return jsonify({"reply": f"Opening weather information for {place}.",
                        "open_url": "https://www.google.com/search?q=" + ("weather " + place).replace(" ", "+")})

    for prefix in ("calculate ", "solve ", "what is "):
        if text.startswith(prefix):
            candidate = text[len(prefix):]
            if any(ch.isdigit() for ch in candidate):
                try:
                    result = safe_calculate(candidate)
                    return jsonify({"reply": f"The answer is {result:g}."})
                except Exception:
                    pass

    if text in {"help", "commands", "what can you do"}:
        return jsonify({"reply":
            "I can tell the time and date, calculate expressions, search the web, open Google, YouTube, GitHub, Gmail, Maps and LinkedIn, and search weather. "
            "I can also create notes, manage tasks and set reminders from the browser."})

    return jsonify({"reply":
        "I don't know that command yet. Try saying help to hear the available commands."})

if __name__ == "__main__":
    import threading
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5002")
    threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5002, debug=False)
