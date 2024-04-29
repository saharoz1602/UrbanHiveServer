import os

from flask import Flask, jsonify, request
from flask_cors import CORS
import socket
import logging
from logging.handlers import RotatingFileHandler
from database import DataBase
from RESTUser import user_bp
from RESTCommunity import community_bp
from RESTEvents import events_bp
from RESTPosting import posting_bp
from RESTNightWatch import night_watch_bp
from Infrastructure.Files import config

from flask import Flask, jsonify, request
from bson import ObjectId
import json


class MongoJsonEncoder(json.JSONEncoder):
    """
        Custom JSON encoder subclass used to serialize MongoDB ObjectId objects into JSON.
        MongoDB uses ObjectId objects for unique identifiers, which are not serializable by default JSON encoder.
    """
    def default(self, obj):
        """
                Override the default() method to convert ObjectId to string.

                Parameters:
                    obj (object): The object to serialize.

                Returns:
                    str: The string representation of the ObjectId.
                    Otherwise, use the standard JSON encoding for the object.
        """
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


def create_app():
    """
        Create and configure an instance of the Flask application.

        Returns:
            app (Flask): The configured Flask application instance.
    """
    app = Flask(__name__)
    app.json_encoder = MongoJsonEncoder
    CORS(app)

    log_directory = os.path.join(config.application_file_path, "logs", "app")
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, "app.log")
    handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Database setup
    dbase = DataBase()
    db = dbase.db

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(posting_bp)
    app.register_blueprint(night_watch_bp)

    # Before and after request hooks
    @app.before_request
    def before_request_logging():
        """
            Log details about the incoming request before processing it.
        """
        app.logger.info(f'Handling request: {request.method} {request.path} from {request.remote_addr}')

    @app.after_request
    def after_request_logging(response):
        """
                Log details about the response after processing a request.

                Parameters:
                    response (Response): The Flask response object.

                Returns:
                    Response: The response object, possibly modified.
        """
        app.logger.info(f'Response: {response.status_code}')
        return response

    # Error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        """
        Handle uncaught exceptions by logging them and returning an error response.

        Parameters:
            e (Exception): The exception that was raised.

        Returns:
            Tuple: A tuple containing an error message and a status code.
        """
        app.logger.error(f'An error occurred: {e}', exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

    # Routes
    @app.route('/get_server_ip', methods=['GET'])
    def get_server_ip():
        """
        Endpoint to retrieve the server IP address.

        Returns:
            jsonify: JSON object containing the server IP address.
        """
        host_ip = socket.gethostbyname(socket.gethostname())
        return jsonify({"server_ip": host_ip}), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint to verify database connectivity and service health.

        Returns:
            jsonify: JSON object indicating the health status of the application and database.
        """
        try:
            db.command('ping')
        except Exception as e:
            app.logger.error(f'Database connection failed: {e}', exc_info=True)
            return jsonify({'status': 'down', 'database': 'down', 'error': str(e)}), 500
        return jsonify({'status': 'up', 'database': 'up'}), 200

    return app


def run_server(host='0.0.0.0', port=5000):
    """
    Start the Flask application on the specified host and port.

    Parameters:
        host (str): The host address to bind the server to.
        port (int): The port number on which the server will listen.
    """
    app = create_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    run_server(host=host_ip, port=5000)
