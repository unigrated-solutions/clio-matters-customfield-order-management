from flask import Blueprint, request, jsonify, render_template

auth = Blueprint('auth', __name__)

_access_token = None

def get_access_token():
    return _access_token


@auth.route('/set_access_token', methods=['POST'])
def set_access_token():
    global _access_token
    data = request.get_json()
    token = data.get('access_token')
    print(data)
    if not token:
        return jsonify({'error': 'Access token is missing'}), 400

    # Save the token securely (e.g., in a database or in-memory storage)
    _access_token = token
    return jsonify({'message': 'Access token saved successfully'}), 200

@auth.route('/upload-token')
def upload_token():
    # Render a page where the user can upload the token
    return render_template('upload_token.html')