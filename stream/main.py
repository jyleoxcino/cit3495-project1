import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('STREAM_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('STREAM_PASSWORD')
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
        return redirect(url_for('browse_files'))

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
        return redirect(url_for('browse_files'))

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
            return redirect(url_for('browse_files'))
        else:
            message = "Invalid username or password."

    return render_template('login.html', message=message)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/browse', methods=['GET'])
@login_required
def browse_files():
    """ List files available for the logged-in user """
    username = current_user.username
    user_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    # Fetch files from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT filename FROM uploads.files WHERE username = %s", (username,))
    files = [row[0] for row in cur.fetchall()]
    cur.close()

    # Check which files actually exist in the Docker volume
    existing_files = [f for f in files if os.path.exists(os.path.join(user_upload_path, f))]
    return render_template('browse.html', files=existing_files, username=username)

@app.route('/media/<filename>', methods=['GET'])
@login_required
def view_media(filename):
    """ Serve files from the Docker volume for viewing in the browser """
    username = current_user.username
    user_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], username)

    file_path = os.path.join(user_upload_path, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    # Check file type to display appropriately
    if filename.lower().endswith(('.mp4', '.webm', '.ogg')):
        return render_template('video_player.html', filename=filename, username=username)
    elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return f'<img src="{url_for("serve_file", filename=filename)}" style="max-width:100%">'
    elif filename.lower().endswith(('.txt', '.log', '.csv')):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f'<pre>{f.read()}</pre>'
    else:
        return "Unsupported file type", 400

@app.route('/serve/<filename>', methods=['GET'])
@login_required
def serve_file(filename):
    """ Serve video files with correct MIME type """
    username = current_user.username
    user_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    file_path = os.path.join(user_upload_path, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    # Determine MIME type based on file extension
    mime_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogg": "video/ogg",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska"
    }

    ext = os.path.splitext(filename)[1].lower()
    mime_type = mime_types.get(ext, "application/octet-stream")  # Default fallback

    return send_file(file_path, mimetype=mime_type)

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('browse_files'))  # Redirect logged-in users to the upload page

if __name__ == '__main__':
    app.run(debug=True, port=8090, host='0.0.0.0')
