import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth:5000')
FILE_SYSTEM_URL = os.getenv('FILE_SYSTEM_URL', 'http://filesystem:5001')

@app.route('/browse', methods=['GET'])
def browse_files():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    # Verify user token
    auth_response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={'Authorization': token})
    if auth_response.status_code != 200:
        return jsonify({'message': 'Unauthorized'}), 401

    username = auth_response.json().get('username')

    # Get list of files from File System Service
    file_response = requests.get(f"{FILE_SYSTEM_URL}/files", headers={'Authorization': token})
    
    if file_response.status_code == 200:
        files = file_response.json().get('files', [])
        return render_template('browse.html', files=files, username=username)
    else:
        return jsonify({'message': 'Could not fetch files'}), 500

@app.route('/media/<filename>', methods=['GET'])
def view_media(filename):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    # Verify user token
    auth_response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={'Authorization': token})
    if auth_response.status_code != 200:
        return jsonify({'message': 'Unauthorized'}), 401

    username = auth_response.json().get('username')

    # Stream file from File System Service
    media_url = f"{FILE_SYSTEM_URL}/files/{filename}"
    return render_template('video_player.html', filename=filename, media_url=media_url, username=username)

if __name__ == '__main__':
    app.run(debug=True, port=8090, host='0.0.0.0')
