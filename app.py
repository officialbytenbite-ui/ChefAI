import os
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL
import google.generativeai as genai

# ---------------- Flask Setup ----------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------- MySQL Config ----------------
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'chefai'

app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
app.config['MYSQL_PORT'] = int(os.getenv("MYSQL_PORT", 3306))

mysql = MySQL(app)

# ---------------- Gemini AI Config ----------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

last_request_time = 0

# ---------------- Routes ----------------

# Serve chatbot page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/home")
def home():
     return render_template("home.html")

@app.route("/aboutus")
def aboutus():
     return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
     return render_template("contactus.html")

@app.route("/recipie")
def recipie():
     return render_template("recipie.html")

@app.route("/diet")
def diet():
     return render_template("diet.html")

@app.route("/review")
def review():
     return render_template("review.html")

# Recipe generation
@app.route('/generate-recipe', methods=['POST'])
def generate_recipe():
    global last_request_time
    now = time.time()
    if now - last_request_time < 2:
        return jsonify({'error': 'Too many requests. Slow down.'}), 429
    last_request_time = now

    data = request.get_json()
    ingredients = data.get('ingredients')
    health = data.get('health')  # optional, can be used in prompt
    cuisine = data.get('cuisine')  # optional, can be used in prompt

    prompt = f"Give me a recipe with only {ingredients}"
    try:
        response = model.generate_content(
            prompt,
            generation_config={'max_output_tokens': 5000}
        )
        return jsonify({"recipe": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    #signup
    
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not email or not username or not password:
            return jsonify({"message": "Missing fields"}), 400

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT id FROM user_info WHERE username=%s OR email=%s",
            (username, email)
        )

        if cur.fetchone():
            cur.close()
            return jsonify({"message": "User already exists"}), 409

        cur.execute(
            "INSERT INTO user_info (email, username, password) VALUES (%s,%s,%s)",
            (email, username, password)
        )

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Signup successful"}), 201

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"message": "Server error", "error": str(e)}), 500
    

@app.route("/contact",methods=["POST"])
def contact():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        subject = data.get("subject")
        message = data.get("message")

        print("CONTACT MESSAGE:", name, email, subject, message)

        return jsonify({
            "success": True,
            "message": "Message received"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM user_info WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()

    if user:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    # ---------------- DIET PLANNER -----------------------
# =====================================================

@app.route("/diet-plan", methods=["POST"])
def diet_plan():
    data = request.json

    prompt = f"""
    Create a {data.get("planType")} Indian diet plan.
    Diet type: {data.get("dietType")}
    Calories: {data.get("calories")}
    Budget: ₹{data.get("budget")}
    Cooking time: {data.get("time")} minutes
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 7000}
        )
        return jsonify({"plan": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- REVIEWS ----------------------------
# =====================================================

@app.route("/submit-review", methods=["POST"])
def submit_review():
    try:
        data = request.json
        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO recipe_reviews (recipe_name, rating, comment) VALUES (%s,%s,%s)",
            (data["recipe"], data["rating"], data["comment"])
        )

        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Review saved"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-reviews/<recipe>")
def get_reviews(recipe):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT rating, comment FROM recipe_reviews WHERE recipe_name=%s",
        (recipe,)
    )

    rows = cur.fetchall()
    cur.close()

    ratings = [r[0] for r in rows]
    comments = [r[1] for r in rows]
    avg = round(sum(ratings) / len(ratings), 1) if ratings else 0

    return jsonify({
        "average": avg,
        "ratings": ratings,
        "comments": comments
    })




# ---------------- Run App ----------------
# if __name__ == "__main__":
#     app.run(port=5000, debug=True)