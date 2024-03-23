from flask import Flask, jsonify
from flask_cors import CORS
import socket
from database import DataBase
# import blueprints for the application
from RESTUser import user_bp
from RESTCommunity import community_bp
from RESTEvents import events_bp
from RESTPosting import posting_bp
from RESTNightWatch import night_watch_bp

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

app = Flask(__name__)
CORS(app)

# Register the Blueprints with the app
app.register_blueprint(user_bp)
app.register_blueprint(community_bp)
app.register_blueprint(events_bp)
app.register_blueprint(posting_bp)
app.register_blueprint(night_watch_bp)


# Flask Server
@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


dbase = DataBase()
db = dbase.db


@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Try to perform a simple read operation on the database
        db.command('ping')
    except Exception as e:
        return jsonify({'status': 'down', 'database': 'down', 'error': str(e)}), 500

    return jsonify({'status': 'up', 'database': 'up'}), 200


if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)
