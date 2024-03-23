# Import necessary modules from Flask, Flask-CORS for handling Cross Origin Resource Sharing (CORS),
# standard Python modules for network communication and logging,
# as well as custom modules for database operations and the application's RESTful interfaces.
from flask import Flask, jsonify, request
from flask_cors import CORS
import socket
import logging
from logging.handlers import RotatingFileHandler
from database import DataBase

# Import blueprints. Blueprints are used in Flask to organize a group of related views and other code.
# Rather than registering views and other code directly with an application,
# they are registered with a blueprint. Then the blueprint is registered with the application
# when it is available in the factory function.
from RESTUser import user_bp
from RESTCommunity import community_bp
from RESTEvents import events_bp
from RESTPosting import posting_bp
from RESTNightWatch import night_watch_bp

# Obtain the host's name and IP address. This is used for running the Flask server
# and can also be returned to clients for direct IP access if necessary.
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

# Initialize the Flask application and enable CORS for all domains.
# CORS is a security feature that allows restricting resources implemented in web browsers.
# It prevents web pages from making requests to a different domain than the one that served the web page.
app = Flask(__name__)
CORS(app)

# Initialize the database connection by creating an instance of the custom DataBase class
# and retrieving the database connection from it.
dbase = DataBase()
db = dbase.db

# Configure logging for the application using a rotating file handler,
# which keeps the log file at a manageable size and archives old log entries.
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Register the application blueprints. Each blueprint represents a different
# module or component of the application, such as users, communities, events, postings, and a night watch service.
app.register_blueprint(user_bp)
app.register_blueprint(community_bp)
app.register_blueprint(events_bp)
app.register_blueprint(posting_bp)
app.register_blueprint(night_watch_bp)


# Before each request, log the request details using the before_request hook.
# This is useful for monitoring and debugging.
@app.before_request
def before_request_logging():
    app.logger.info(f'Handling request: {request.method} {request.path} from {request.remote_addr}')


# After each request, log the response status code using the after_request hook.
@app.after_request
def after_request_logging(response):
    app.logger.info(f'Response: {response.status_code}')
    return response


# Provide a generic error handler that logs the exception and returns a 500 Internal Server Error response.
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'An error occurred: {e}', exc_info=True)
    return jsonify({'error': 'An internal error occurred.'}), 500


# Define a route to return the server's IP address. This can be useful for diagnostic purposes.
@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


# Define a health check route that attempts to perform a simple operation on the database.
# It returns the status of the application and the database.
@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.command('ping')
    except Exception as e:
        app.logger.error(f'Database connection failed: {e}', exc_info=True)
        return jsonify({'status': 'down', 'database': 'down', 'error': str(e)}), 500
    return jsonify({'status': 'up', 'database': 'up'}), 200


# The entry point for running the Flask application, specifying the host and port.
# debug=False is set for production use to not expose detailed errors.
if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)
