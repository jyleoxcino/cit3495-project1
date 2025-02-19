from flask import Flask, request, jsonify, send_file
import os
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/media-data')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth:5000')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/create_user_directory', methods=['POST'])
def create_user_directory():
    data = request.json
    username = data.get('username')
    user_upload_path = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_upload_path, exist_ok=True)
    return jsonify({'message': 'User directory created'}), 201

@app.route('/upload', methods=['POST'])
def upload_file():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    
    auth_response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={'Authorization': token})
    if auth_response.status_code != 200:
        return jsonify({'message': 'Unauthorized'}), 401
    
    username = auth_response.json().get('username')
    user_upload_path = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_upload_path, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(user_upload_path, filename)
    file.save(file_path)
    
    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 201

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['GET'])
def get_file(filename):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    
    auth_response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={'Authorization': token})
    if auth_response.status_code != 200:
        return jsonify({'message': 'Unauthorized'}), 401
    
    username = auth_response.json().get('username')
    user_upload_path = os.path.join(UPLOAD_FOLDER, username)
    file_path = os.path.join(user_upload_path, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'message': 'File not found'}), 404
    
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
