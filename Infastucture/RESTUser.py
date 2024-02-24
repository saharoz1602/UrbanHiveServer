from flask import Blueprint, jsonify, request, abort
from database import database  # Ensure this is accessible from this module
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

# Initialize database connection
dbase = database()
db = dbase.db
users = db['users']

# Create a Flask Blueprint for the user routes
user_bp = Blueprint('user', __name__)


@user_bp.route('/users', methods=['GET'])
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


@user_bp.route('/user/', methods=['POST'])
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


@user_bp.route('/user/<user_id>', methods=['GET'])
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


@user_bp.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    # Get the JSON data from the request
    update_data = request.get_json()

    # Ensure the update data does not contain '_id' or 'id'
    update_data.pop('_id', None)
    update_data.pop('id', None)

    # Find the user in the MongoDB collection
    user = users.find_one({"id": user_id})

    # If the user doesn't exist, return a 404 Not Found response
    if user is None:
        abort(404, description="User not found")

    try:
        # Update the user's data in the database
        # Note: This will update the fields provided in the request and leave others unchanged
        updated_user = users.find_one_and_update(
            {"id": user_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )

        # If the update operation did not find the user, return a 404 Not Found response
        if updated_user is None:
            abort(404, description="User not found after attempting update")

        # Convert ObjectId to string for the response
        updated_user['_id'] = str(updated_user['_id'])

        # Exclude sensitive data like password from the response
        updated_user.pop('password', None)

        # Return the updated user data
        return jsonify(updated_user), 200
    except Exception as e:
        # If an error occurs during the update, return a 500 Internal Server Error response
        abort(500, description=str(e))


@user_bp.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Check if the user exists
    if users.find_one({"id": user_id}) is None:
        # If no user is found, return a 404 Not Found response
        abort(404, description="User not found")

    # Delete the user from the MongoDB collection
    users.delete_one({"id": user_id})

    # Return a success message
    return jsonify({"message": "User deleted successfully"}), 200


@user_bp.route('/password', methods=['POST'])
def check_user_password():
    # Retrieve ID and password from request JSON
    user_data = request.get_json()

    # Validate if both ID and password are provided
    if not user_data or 'id' not in user_data or 'password' not in user_data:
        return jsonify({"error": "ID and password are required"}), 400

    # Use the get_user_by_id function to fetch the user
    response = get_user_by_id(user_data['id'])

    # If the user is not found, response will have status code 404
    if response.status_code == 404:
        return jsonify({"result": "False"}), 404

    # Get the user object from the response
    user = response.get_json()

    # Check if the password matches
    if user.get('password') == user_data['password']:
        return jsonify({"result": "True"}), 200
    else:
        return jsonify({"result": "False"}), 404
