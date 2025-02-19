import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('UPLOAD_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('UPLOAD_PASSWORD')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM credentials.users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return User(*user) if user else None

@login_manager.unauthorized_handler
def unauthorized():
    return render_template('login.html', message="You must be logged in to access this page.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO credentials.users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()

        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], username), exist_ok=True)

        return redirect(url_for('login', message='Registration successful. Please log in.'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Check if user is already logged in
        return redirect(url_for('upload'))

    message = request.args.get('message', '')  # Get message from URL if exists

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM credentials.users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            login_user(User(*user))
            return redirect(url_for('upload'))
        else:
            message = "Invalid username or password."

    return render_template('login.html', message=message)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            cur = mysql.connection.cursor()
            username = current_user.username
            user_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], username)

            if not os.path.exists(user_upload_path):
                os.makedirs(user_upload_path)

            filename = secure_filename(file.filename)
            file.save(os.path.join(user_upload_path, filename))

            cur.execute("INSERT INTO uploads.files (username, filename, filepath) VALUES (%s, %s, %s)", (username, filename, user_upload_path))
            mysql.connection.commit()
            cur.close()

            return render_template('upload.html', message='File uploaded successfully.')
    return render_template('upload.html')

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('upload'))  # Redirect logged-in users to the upload page

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
