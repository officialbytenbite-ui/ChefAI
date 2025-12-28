from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'chefai'

mysql = MySQL(app)

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



@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    full_name = data['full_name']
    email = data['email']
    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()

    # Check if user already exists
    cur.execute(
        "SELECT * FROM user_info WHERE username=%s OR email=%s",
        (username, email)
    )
    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        return jsonify({"message": "User already exists"}), 409

    # Insert new user
    cur.execute(
        "INSERT INTO user_info (full_name, email, username, password) VALUES (%s,%s,%s,%s)",
        (full_name, email, username, password)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Signup successful"}), 201

if __name__ == "__main__":
    app.run(debug=True)