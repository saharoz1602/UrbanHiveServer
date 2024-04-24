import os

from flask import Blueprint, jsonify, request, abort
from database import DataBase
from pymongo import ReturnDocument, errors
from Logic.app_logger import setup_logger
from Infrastructure.Files import config

# Initialize database connection
dbase = DataBase()
db = dbase.db
users = db['users']

log_file_path = os.path.join(config.application_file_path, "user.log")
user_logger = setup_logger('user_logger', log_file_path)

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

        user_logger.info(f"Users fetched successfully, users : {users_list}, status code is 200")
        return jsonify({"message": "Users fetched successfully", "users": users_list}), 200
    except Exception as e:
        # Handle exceptions
        user_logger.error(f"error {str(e)}")
        return jsonify({"error": str(e)}), 500


@user_bp.route('/user/', methods=['POST'])
def add_user():
    try:
        user_data = request.get_json()

        required_fields = ["id", "name", "email", "password", "phoneNumber", "location"]
        if not all(field in user_data for field in required_fields):
            return jsonify({"description": "Missing required field(s)"}), 400

        if not all(field in user_data["location"] for field in ["latitude", "longitude"]):
            return jsonify({"description": "Missing required field(s)"}), 400

        if not isinstance(user_data["location"]["latitude"], (float, int)) or \
                not isinstance(user_data["location"]["longitude"], (float, int)):
            return jsonify({"description": "Invalid data type for latitude or longitude"}), 400

        user_data["friends"] = []
        user_data["requests"] = []
        user_data["radius"] = None

        if users.find_one({"$or": [{"id": user_data["id"]}, {"email": user_data["email"]}]}):
            user_logger.error("User with this ID or email already exists, status code is 409")
            return jsonify({"message": "User with this ID or email already exists"}), 409

        inserted = users.insert_one(user_data)
        user_data.pop("password", None)
        user_data["_id"] = str(inserted.inserted_id)
        user_logger.info("User added successfully, status code is 201")
        return jsonify({"message": "User added successfully", "user": user_data}), 201
    except Exception as e:
        user_logger.error(f"Unexpected error occurred: {str(e)}")
        return jsonify({"error": "Internal Server Error", "detail": str(e)}), 500


@user_bp.route('/user/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    # Fetch the user from the MongoDB collection using the provided id
    user = users.find_one({"id": user_id})

    # Check if the user exists
    if user is None:
        # If no user is found, return a 404 Not Found response
        return jsonify({"error": "User not found!"}), 404

    # Convert ObjectId to string for the response
    user["_id"] = str(user["_id"])

    # Return the user data
    # Exclude sensitive data like password from the response
    user.pop('password', None)

    user_logger.info(f"user : {user}, status code is 200")
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
        return jsonify({"error": "User not found!"}), 404

    # Delete the user from the MongoDB collection
    users.delete_one({"id": user_id})

    # Return a success message
    user_logger.info(f"User deleted successfully, status code is 200")
    return jsonify({"message": "User deleted successfully"}), 200


@user_bp.route('/users/password', methods=['POST'])
def check_user_password():
    # Retrieve ID and password from request JSON
    user_data = request.get_json()

    # Validate if both ID and password are provided
    if not user_data or 'id' not in user_data or 'password' not in user_data:
        return jsonify({"error": "ID and password are required"}), 400

    # Fetch the user from the MongoDB collection using the provided id
    user = users.find_one({"id": user_data['id']})

    # If the user is not found, return a 404 Not Found response
    if user is None:
        return jsonify({"result": "False"}), 404

    # Check if the password matches
    if user.get('password') == user_data['password']:
        return jsonify({"result": True}), 200
    else:
        return jsonify({"result": False}), 401  # Changed to 401 to indicate unauthorized access


@user_bp.route('/user/change-password', methods=['POST'])
def change_password():
    # Retrieve the password details and user id from the request JSON
    password_data = request.get_json()

    # Validate if all required fields are provided
    required_fields = ['id', 'new_password', 'verify_new_password']
    if not all(field in password_data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate if the new_password and verify_new_password match
    if password_data['new_password'] != password_data['verify_new_password']:
        return jsonify({"error": "Passwords do not match"}), 400

    # Validate if the password fields are not empty
    if not password_data['new_password'] or not password_data['verify_new_password']:
        return jsonify({"error": "Password cannot be empty"}), 400

    # Fetch the user from the MongoDB collection using the provided id
    user = users.find_one({"id": password_data['id']})

    # If the user is not found, return a 404 Not Found response
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Update the user's password
    try:
        users.update_one(
            {"id": password_data['id']},
            {"$set": {"password": password_data['new_password']}}
        )
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route('/user/<user_id>/radius', methods=['PUT'])
def update_user_radius(user_id):
    # Get the radius from the request JSON
    data = request.get_json()
    radius = data.get('radius')

    # Validate the radius
    if radius is None or not isinstance(radius, float):
        return jsonify({"error": "Invalid or missing 'radius'. A float is required."}), 400

    # Find the user in the MongoDB collection and update the radius
    result = users.find_one_and_update(
        {"id": user_id},
        {"$set": {"radius": radius}},
        return_document=ReturnDocument.AFTER
    )

    # If the user doesn't exist, return a 404 Not Found response
    if result is None:
        abort(404, description="User not found")

    # Convert ObjectId to string for the response
    result['_id'] = str(result['_id'])

    # Exclude sensitive data like password from the response
    result.pop('password', None)

    return jsonify({"message": "Radius updated successfully", "user": result}), 200


@user_bp.route('/user/add-friend', methods=['POST'])
def add_friend():
    data = request.get_json()

    # Extract sender_id and receiver_id from the request data
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')

    # Check if both sender and receiver IDs are provided
    if not sender_id or not receiver_id:
        return jsonify({"error": "Both sender_id and receiver_id are required"}), 400

    # Check if sender and receiver are the same
    if sender_id == receiver_id:
        return jsonify({"error": "Sender and receiver cannot be the same"}), 400

    # Verify both users exist
    sender = users.find_one({"id": sender_id})
    receiver = users.find_one({"id": receiver_id})

    if sender is None or receiver is None:
        return jsonify({"error": "Both users must exist"}), 404

    # Prepare the request objects for sender and receiver
    sender_request = {"id": receiver_id, "name": receiver["name"], "status": "pending"}
    receiver_request = {"id": sender_id, "name": sender["name"], "status": "wait for response"}

    # Update the sender and receiver 'requests' arrays
    try:
        users.update_one({"id": sender_id}, {"$push": {"requests": sender_request}})
        users.update_one({"id": receiver_id}, {"$push": {"requests": receiver_request}})
        return jsonify({"message": "Friend request sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @user_bp.route('/user/respond-to-request', methods=['POST'])
# def respond_to_request():
#     data = request.get_json()
#
#     receiver_id = data.get('receiver_id')
#     sender_id = data.get('sender_id')
#     response = data.get('response')  # 1 for approve, 0 for decline
#
#     # Fetch both sender and receiver from the database
#     sender = users.find_one({"id": sender_id})
#
#     receiver = users.find_one({"id": receiver_id})
#
#     if not sender or not receiver:
#         return jsonify({"error": "Sender and receiver must exist"}), 404
#
#     # Check if the users are already friends or have pending friend requests
#     if any(friend['friend id'] == receiver_id for friend in sender.get('friends', [])) or \
#             any(friend['friend id'] == sender_id for friend in receiver.get('friends', [])) or \
#             any(request['id'] == receiver_id for request in sender.get('requests', [])) or \
#             any(request['id'] == sender_id for request in receiver.get('requests', [])):
#         return jsonify({"error": "Users already connected or have pending friend requests"}), 409
#
#     if response == 1:  # Approve
#         # Prepare friend information for both sender and receiver
#         sender_friend_info = {
#             "friend name": receiver["name"],
#             "friend id": receiver_id,
#             "friend location": receiver["location"]
#         }
#
#         receiver_friend_info = {
#             "friend name": sender["name"],
#             "friend id": sender_id,
#             "friend location": sender["location"]
#         }
#
#         # Add each user to the other's friends list and remove the request
#         users.update_one({"id": sender_id},
#                          {"$push": {"friends": sender_friend_info}, "$pull": {"requests": {"id": receiver_id}}})
#         users.update_one({"id": receiver_id},
#                          {"$push": {"friends": receiver_friend_info}, "$pull": {"requests": {"id": sender_id}}})
#
#     elif response == 0:  # Decline
#         # Just remove the friend request from both users
#         users.update_one({"id": sender_id}, {"$pull": {"requests": {"id": receiver_id}}})
#         users.update_one({"id": receiver_id}, {"$pull": {"requests": {"id": sender_id}}})
#
#     else:
#         return jsonify({"error": "Invalid response"}), 400
#
#     return jsonify({"message": "Response processed successfully"}), 200


@user_bp.route('/user/respond-to-request', methods=['POST'])
def respond_to_request():
    data = request.get_json()

    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')
    response = data.get('response')  # 1 for approve, 0 for decline

    # Fetch both sender and receiver from the database
    sender = users.find_one({"id": sender_id})
    receiver = users.find_one({"id": receiver_id})

    if not sender or not receiver:
        return jsonify({"error": "Sender and receiver must exist"}), 404

    if response == 1:  # Approve
        # Prepare friend information for both sender and receiver
        sender_friend_info = {
            "friend name": receiver["name"],
            "friend id": receiver_id,
            "friend location": receiver["location"]
        }

        receiver_friend_info = {
            "friend name": sender["name"],
            "friend id": sender_id,
            "friend location": sender["location"]
        }

        # Add each user to the other's friends list and remove the request
        users.update_one({"id": sender_id},
                         {"$push": {"friends": sender_friend_info}, "$pull": {"requests": {"id": receiver_id}}})
        users.update_one({"id": receiver_id},
                         {"$push": {"friends": receiver_friend_info}, "$pull": {"requests": {"id": sender_id}}})

    elif response == 0:  # Decline
        # Just remove the friend request from both users
        users.update_one({"id": sender_id}, {"$pull": {"requests": {"id": receiver_id}}})
        users.update_one({"id": receiver_id}, {"$pull": {"requests": {"id": sender_id}}})

    else:
        return jsonify({"error": "Invalid response"}), 400

    return jsonify({"message": "Response processed successfully"}), 200


@user_bp.route('/user/delete-friend', methods=['POST'])
def delete_friend():
    data = request.get_json()

    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')

    # Ensure both sender and receiver IDs are provided
    if not receiver_id or not sender_id:
        return jsonify({"error": "Both receiver_id and sender_id must be provided"}), 400

    # Attempt to delete the receiver from the sender's friends list
    sender_update_result = users.update_one(
        {"id": sender_id},
        {"$pull": {"friends": {"friend id": receiver_id}}}
    )

    # Attempt to delete the sender from the receiver's friends list
    receiver_update_result = users.update_one(
        {"id": receiver_id},
        {"$pull": {"friends": {"friend id": sender_id}}}
    )

    if sender_update_result.modified_count == 0 and receiver_update_result.modified_count == 0:
        # This means neither document was updated; possibly one of the users did not have the other in their friends
        # list
        return jsonify({"error": "No changes made; check if the users are actually friends"}), 404

    return jsonify({"message": "Friendship deleted successfully"}), 200
