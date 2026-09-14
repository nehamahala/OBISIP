from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def calculate_bmi(weight, height_m):
    if weight <= 0 or height_m <= 0:
        raise ValueError("Values must be greater than zero.")
    bmi = weight / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obesity"
    return round(bmi, 2), category

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/calculate")
def calculate():
    try:
        data = request.get_json()
        weight = float(data.get("weight", 0))
        height_cm = float(data.get("height", 0))
        bmi, category = calculate_bmi(weight, height_cm / 100)
        return jsonify(success=True, bmi=bmi, category=category)
    except (TypeError, ValueError):
        return jsonify(success=False, message="Enter valid positive values."), 400

if __name__ == "__main__":
    app.run(debug=True, port=5003)
