from flask import Flask, request, jsonify
from flask_pymongo import PyMongo, ObjectId
from flask_cors import CORS
from database import database
import socket
from flask import jsonify, request, abort
from pymongo.errors import DuplicateKeyError
from Entities.User import User

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
    try:
        # Fetch all user documents from the MongoDB collection
        users_list = list(users.find())

        # Convert ObjectId to string for JSON serialization
        for user in users_list:
            user['_id'] = str(user['_id'])

        return jsonify({"message": "Users fetched successfully", "users": users_list}), 200
    except Exception as e:
        # Handle exceptions
        return jsonify({"error": str(e)}), 500


@app.route('/user/', methods=['POST'])
def add_user():
    """
    EXAMPLE OF USER OBJECT IN THE MONGO DB
    {
      "name": "dadsor",
      "email": "dandss@gmail.com",
      "password": "danors93",
      "id": "255321353"
    }
    """
    # Get JSON data from the request
    user_data = request.get_json()

    # Check if the 'id' field is present in the user data
    if 'id' not in user_data:
        abort(400, description="id field is required")

    # Check if a user with the same ID already exists
    if users.find_one({"id": user_data["id"]}) is not None:
        return jsonify({"message": "User with this ID already exists"}), 409

    try:
        # Insert the user data into the MongoDB collection
        inserted = users.insert_one(user_data)
    except DuplicateKeyError:
        # Handle the case where the insertion fails due to a duplicate key (e.g., email)
        return jsonify({"message": "User with this data already exists"}), 409

    # Convert ObjectId to string
    user_data["_id"] = str(inserted.inserted_id)

    return jsonify({"message": "User added successfully", "user": user_data}), 201


from flask import jsonify, abort

@app.route('/user/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    # Fetch the user from the MongoDB collection using the provided id
    user = users.find_one({"id": user_id})

    # Check if the user exists
    if user is None:
        # If no user is found, return a 404 Not Found response
        abort(404, description="User not found")

    # Convert ObjectId to string for the response
    user["_id"] = str(user["_id"])

    # Return the user data
    # Exclude sensitive data like password from the response
    user.pop('password', None)

    return jsonify(user), 200



@app.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    # Get the JSON data from the request
    update_data = request.get_json()

    # Find the user in the MongoDB collection
    user = users.find_one({"id": user_id})

    # If the user doesn't exist, return a 404 Not Found response
    if user is None:
        abort(404, description="User not found")

    # Update the user's data in the database
    # Note: This will update the fields provided in the request and leave others unchanged
    users.update_one({"id": user_id}, {"$set": update_data})

    # Fetch the updated user data
    updated_user = users.find_one({"id": user_id})

    # Convert ObjectId to string for the response
    updated_user["_id"] = str(updated_user["_id"])

    # Exclude sensitive data like password from the response
    updated_user.pop('password', None)

    # Return the updated user data
    return jsonify(updated_user), 200


@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Check if the user exists
    if users.find_one({"id": user_id}) is None:
        # If no user is found, return a 404 Not Found response
        abort(404, description="User not found")

    # Delete the user from the MongoDB collection
    users.delete_one({"id": user_id})

    # Return a success message
    return jsonify({"message": "User deleted successfully"}), 200




# Flask Server
@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    return jsonify({"server_ip": host_ip}), 200


if __name__ == "__main__":
    app.run(host=host_ip, port=5000, debug=False)
