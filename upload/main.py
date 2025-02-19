import os
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth:5000')
FILE_SYSTEM_URL = os.getenv('FILE_SYSTEM_URL', 'http://filesystem:5001')

@app.route('/upload', methods=['POST'])
def upload_file():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    # Verify user token
    auth_response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={'Authorization': token})
    if auth_response.status_code != 200:
        return jsonify({'message': 'Unauthorized'}), 401

    username = auth_response.json().get('username')

    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)

    # Send file to File System Service
    files = {'file': (filename, file.stream)}
    file_response = requests.post(f"{FILE_SYSTEM_URL}/upload", headers={'Authorization': token}, files=files)

    if file_response.status_code == 201:
        return jsonify({'message': 'File uploaded successfully', 'file_path': file_response.json().get('file_path')}), 201
    else:
        return jsonify({'message': 'File upload failed'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
