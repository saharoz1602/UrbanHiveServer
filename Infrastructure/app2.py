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


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Setup logging
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
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
        app.logger.info(f'Handling request: {request.method} {request.path} from {request.remote_addr}')

    @app.after_request
    def after_request_logging(response):
        app.logger.info(f'Response: {response.status_code}')
        return response

    # Error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'An error occurred: {e}', exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

    # Routes
    @app.route('/get_server_ip', methods=['GET'])
    def get_server_ip():
        host_ip = socket.gethostbyname(socket.gethostname())
        return jsonify({"server_ip": host_ip}), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            db.command('ping')
        except Exception as e:
            app.logger.error(f'Database connection failed: {e}', exc_info=True)
            return jsonify({'status': 'down', 'database': 'down', 'error': str(e)}), 500
        return jsonify({'status': 'up', 'database': 'up'}), 200

    return app


def run_server(host='0.0.0.0', port=5000):
    app = create_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    run_server(host=host_ip, port=5000)
