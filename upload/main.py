import os
import requests
import jwt
import logging
import mimetypes
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL  # ✅ Import MySQLdb
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5000')
FILE_SYSTEM_URL = os.getenv('FILE_SYSTEM_URL', 'http://localhost:5001')

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB upload limit

# ✅ Add MySQL configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'db')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = 'uploads'  # Ensure this matches MySQL DB name

mysql = MySQL(app)  # ✅ Initialize MySQL

logging.basicConfig(level=logging.INFO)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv', 'avi'}

def verify_token(token):
    """Decodes and verifies JWT token"""
    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return decoded_token.get('username')
    except jwt.ExpiredSignatureError:
        logging.error("Token expired")
        return None
    except jwt.InvalidTokenError:
        logging.error("Invalid token")
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET'])
def upload():
    """Displays the upload page."""
    token = request.cookies.get('token')
    if not token:
        return redirect(f"{AUTH_SERVICE_URL}/login?message=Please log in first.")

    username = verify_token(token)
    if not username:
        return redirect(f"{AUTH_SERVICE_URL}/login?message=Session expired. Please log in again.")

    return render_template('upload.html', username=username)  # ✅ Show upload page
@app.route('/process_upload', methods=['POST'])
def process_upload():
    """Handles the video upload process."""
    token = request.cookies.get('token') or request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    username = verify_token(token.replace("Bearer ", "")) if "Bearer " in token else verify_token(token)
    if not username:
        return jsonify({'message': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)

    # ✅ Send file to File System Service
    file_response = requests.post(
        f"{FILE_SYSTEM_URL}/upload",
        headers={'Authorization': f'Bearer {token}'},
        files={'file': (filename, file.stream)}
    )

    if file_response.status_code == 201:
        file_path = file_response.json().get('file_path')

        # ✅ Insert into MySQL for Global Access
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO files (username, filename, filepath) VALUES (%s, %s, %s)", 
                        (username, filename, file_path))
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            logging.error(f"Database error: {e}")
            return jsonify({'message': f'Database error: {str(e)}'}), 500

        return redirect("http://localhost:8090/browse")  # ✅ Redirect to browse page
    else:
        return jsonify({'message': 'File upload failed'}), 500

@app.route('/upload/success', methods=['GET'])
def upload_success():
    """✅ Success page for uploads"""
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
