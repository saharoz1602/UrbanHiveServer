from flask import Flask, request, jsonify
from flask_pymongo import PyMongo, ObjectId
from flask_cors import CORS
from database import database
import socket

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

dbase = database()
db = dbase.db

# Access a collection named 'users'
users = db['users']

# Insert a document into the 'users' collection
# users.insert_one({"name": "John", "email": "john@example.com"})

app = Flask(__name__)
CORS(app)

@app.route('/users', methods=['GET'])
def get_users():
    return

from flask import request, jsonify

@app.route('/user/', methods=['POST'])
def add_user():
    # Get JSON data from the request
    user_data = request.get_json()

    # Insert the user data into the MongoDB collection
    inserted = users.insert_one(user_data)

    # Convert ObjectId to string
    user_data["_id"] = str(inserted.inserted_id)

    return jsonify({"message": "User added successfully", "user": user_data}), 201


@app.route('/user/<id>', methods=['GET'])
def get_user_by_id(id):
    return

@app.route('/user/<id>', methods=['PUT'])
def update_user(id):
    return

@app.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
    return jsonify({"message": "User deleted successfully"})

# Flask Server
@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)

