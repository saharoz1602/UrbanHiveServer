from flask import Flask, jsonify
from flask_cors import CORS
import socket
from RESTUser import user_bp  # Import the Blueprint from user.py
from RESTCommunity import community_bp

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

app = Flask(__name__)
CORS(app)

# Register the Blueprint with the app
app.register_blueprint(user_bp)
app.register_blueprint(community_bp)

# Flask Server
@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)
