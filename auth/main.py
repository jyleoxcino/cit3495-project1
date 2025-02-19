from flask import Flask, request, jsonify, render_template, redirect, url_for
import jwt
import datetime
import os
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'db')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = 'credentials'

mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])  # Allow both GET and POST
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, user_dir) VALUES (%s, %s, %s)", 
                    (username, password, f"/media-data/{username}"))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login', message="Registration successful. Please log in."))

    message = request.args.get('message', '')
    return render_template('register.html', message=message)  # If GET request, show the registration page
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = request.args.get('message', '')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            token = jwt.encode({'username': username, 'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
                               app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'token': token})
        else:
            return render_template('login.html', message="Invalid credentials. Please try again.", show_alert=True)

    return render_template('login.html', message="", show_alert=False)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
