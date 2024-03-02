from flask import Blueprint, jsonify, request, abort
from database import DataBase  # Ensure this is accessible from this module
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument, errors

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']  # Assuming users collection is also accessible

# Create a Flask Blueprint for the community routes
community_bp = Blueprint('community', __name__)


@community_bp.route('/communities/add_community', methods=['POST'])
def add_community():
    data = request.json
    manager_id = data.get('manager_id')
    area = data.get('area')

    # Fetch manager's details
    manager = users.find_one({"id": manager_id}, {"_id": 0, "id": 1, "name": 1, "location": 1})
    if not manager:
        return jsonify({"error": "Manager not found"}), 404

    # Prepare community object
    community = {
        "area": area,
        "rules": [],
        "communityMembers": [manager],  # Add manager to community members
        "communityManagers": [manager],  # Add manager as the community manager
        "events": []
    }

    try:
        result = communities.insert_one(community)
        return jsonify({"message": "Community added", "id": str(result.inserted_id)}), 201
    except DuplicateKeyError:
        return jsonify({"error": "Community already exists"}), 400
    except errors.PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


@community_bp.route('/communities/add_user_to_community', methods=['POST'])
def add_user_to_community():
    data = request.json
    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')
    area = data.get('community area')

    # Prepare the updates for receiver and sender
    receiver_update = {
        "community request": area,
        "status": "waiting for your response"
    }
    sender_update = {
        "community request": area,
        "status": f"pending from {receiver_id}"
    }

    try:
        # Update receiver's community request
        users.update_one({"id": receiver_id}, {"$set": {"communityRequest": receiver_update}})

        # Update sender's community request
        users.update_one({"id": sender_id}, {"$set": {"communityRequest": sender_update}})

        return jsonify({"message": "Community request updated for both users"}), 200
    except errors.PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


@community_bp.route('/communities/respond_to_community_request', methods=['POST'])
def respond_to_community_request():
    data = request.json
    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')
    response = data.get('response')
    area = data.get('area')

    if response == 1:
        # Confirming the community request
        try:
            # Retrieve receiver's name and location
            receiver_user = users.find_one({"id": receiver_id}, {"name": 1, "location": 1})
            if not receiver_user:
                return jsonify({"error": "Receiver user not found"}), 404

            receiver_name = receiver_user.get('name')
            receiver_location = receiver_user.get('location')

            # Add receiver to community's members list with id, name, and location
            community_member_info = {"id": receiver_id, "name": receiver_name, "location": receiver_location}
            communities.update_one({"area": area}, {"$push": {"communityMembers": community_member_info}})

            # Add location to communities collection for the receiver
            if receiver_location:  # Ensure the location exists
                communities.update_one({"area": area}, {"$addToSet": {"locations": receiver_location}})

            # Update both users' communities list
            users.update_one({"id": receiver_id}, {"$push": {"communities": area}})
            users.update_one({"id": sender_id}, {"$push": {"communities": area}})

            # Remove community request for both users
            users.update_one({"id": receiver_id}, {"$unset": {"communityRequest": ""}})
            users.update_one({"id": sender_id}, {"$unset": {"communityRequest": ""}})

            return jsonify(
                {"message": "Community request confirmed, users updated, and location added to community"}), 200
        except errors.PyMongoError as e:
            return jsonify({"error": "Database error", "details": str(e)}), 500
    elif response == 0:
        # Declining the community request
        try:
            # Remove community request for both users
            users.update_one({"id": receiver_id}, {"$unset": {"communityRequest": ""}})
            users.update_one({"id": sender_id}, {"$unset": {"communityRequest": ""}})

            return jsonify({"message": "Community request declined and removed"}), 200
        except errors.PyMongoError as e:
            return jsonify({"error": "Database error", "details": str(e)}), 500


# @community_bp.route('/communities/respond_to_community_request', methods=['POST'])
# def respond_to_community_request():
#     data = request.json
#     receiver_id = data.get('receiver_id')
#     sender_id = data.get('sender_id')
#     response = data.get('response')
#     area = data.get('area')
#
#     if response == 1:
#         # Confirming the community request
#         try:
#             # Retrieve receiver's name
#             receiver_user = users.find_one({"id": receiver_id}, {"name": 1})
#             if not receiver_user:
#                 return jsonify({"error": "Receiver user not found"}), 404
#             receiver_name = receiver_user.get('name')
#
#             # Add receiver to community's members list with id and name
#             community_member_info = {"id": receiver_id, "name": receiver_name}
#             communities.update_one({"area": area}, {"$push": {"communityMembers": community_member_info}})
#
#             # Update both users' communities list
#             users.update_one({"id": receiver_id}, {"$push": {"communities": area}})
#             users.update_one({"id": sender_id}, {"$push": {"communities": area}})
#
#             # Remove community request for both users
#             users.update_one({"id": receiver_id}, {"$unset": {"communityRequest": ""}})
#             users.update_one({"id": sender_id}, {"$unset": {"communityRequest": ""}})
#
#             return jsonify({"message": "Community request confirmed and users updated"}), 200
#         except errors.PyMongoError as e:
#             return jsonify({"error": "Database error", "details": str(e)}), 500
#     elif response == 0:
#         # Declining the community request
#         try:
#             # Remove community request for both users
#             users.update_one({"id": receiver_id}, {"$unset": {"communityRequest": ""}})
#             users.update_one({"id": sender_id}, {"$unset": {"communityRequest": ""}})
#
#             return jsonify({"message": "Community request declined and removed"}), 200
#         except errors.PyMongoError as e:
#             return jsonify({"error": "Database error", "details": str(e)}), 500


@community_bp.route('/communities/delete_user_from_community', methods=['POST'])
def delete_user_from_community():
    data = request.json
    user_to_delete_id = data.get('user_to_delete_id')
    area = data.get('area')

    try:
        # Adjusted to match only the 'id' field inside the 'communityMembers' objects
        communities.update_one({"area": area}, {"$pull": {"communityMembers": {"id": user_to_delete_id}}})

        # Remove community from user's list of communities
        users.update_one({"id": user_to_delete_id}, {"$pull": {"communities": area}})

        return jsonify({"message": "User removed from community successfully"}), 200
    except errors.PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
