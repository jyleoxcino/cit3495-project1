from flask import Flask, request, jsonify
import jwt
import datetime
import os
import uuid
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'db')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = 'credentials'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = generate_password_hash(data.get('password'))
    user_dir = f"/media-data/{username}"
    
    os.makedirs(user_dir, exist_ok=True)
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password, user_dir) VALUES (%s, %s, %s)", (username, password, user_dir))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    
    if user and check_password_hash(user[2], password):
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user_dir': user[3]})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/verify', methods=['GET'])
def verify():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'username': data['username']}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
