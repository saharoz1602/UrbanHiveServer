from flask import Flask, jsonify, request
from flask_cors import CORS
import socket
import logging
from logging.handlers import RotatingFileHandler
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
# Initialize the database connection
dbase = DataBase()
db = dbase.db

# Configure logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Register the Blueprints with the app
app.register_blueprint(user_bp)
app.register_blueprint(community_bp)
app.register_blueprint(events_bp)
app.register_blueprint(posting_bp)
app.register_blueprint(night_watch_bp)

# Flask Server
@app.before_request
def before_request_logging():
    app.logger.info(f'Handling request: {request.method} {request.path} from {request.remote_addr}')


@app.after_request
def after_request_logging(response):
    app.logger.info(f'Response: {response.status_code}')
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'An error occurred: {e}', exc_info=True)
    return jsonify({'error': 'An internal error occurred.'}), 500


@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Try to perform a simple read operation on the database
        db.command('ping')
    except Exception as e:
        app.logger.error(f'Database connection failed: {e}', exc_info=True)
        return jsonify({'status': 'down', 'database': 'down', 'error': str(e)}), 500

    return jsonify({'status': 'up', 'database': 'up'}), 200


if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)
