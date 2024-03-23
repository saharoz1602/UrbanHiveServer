import json
import uuid

from flask import Blueprint, jsonify, request
from database import DataBase
from pymongo.errors import DuplicateKeyError
from pymongo import errors
from Logic.RadiusCalculator import RadiusCalculator

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']  # Assuming users collection is also accessible

# Create a Flask Blueprint for t the community routes
community_bp = Blueprint('community', __name__)


@community_bp.route('/communities/add_community', methods=['POST'])
def add_community():
    data = request.json
    manager_id = data.get('manager_id')
    area = data.get('area')
    location = data.get('location')

    find = communities.find_one({"area": area})  # validating there is no community called "area"
    if find:
        return jsonify({"error": "the community with this name is already exists±!!"}), 400

    find = communities.find_one({"location": location})
    if find:
        return jsonify({"error": "the community with this location is already exists±!!"}), 400

    # Fetch manager's details
    manager = users.find_one({"id": manager_id}, {"_id": 0, "id": 1, "name": 1, "location": 1})
    if not manager:
        return jsonify({"error": "Manager not found"}), 404

    community_id = str(uuid.uuid4())

    # Prepare community object
    community = {
        "community_id": community_id,
        "area": area,
        "location": location,
        "rules": [],
        "communityMembers": [manager],  # Add manager to community members
        "communityManagers": [manager],  # Add manager as the community manager
        "events": []
    }

    try:
        users.update_one({"id": manager_id}, {"$push": {"communities": area}})
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


@community_bp.route('/communities/get_communities_by_radius_and_location', methods=['POST'])
def get_communities_by_radius_and_location():
    data = request.json
    rd = RadiusCalculator()
    radius = data["radius"]
    location = data["location"]

    center_location = [float(location["latitude"]), float(location["longitude"])]

    try:
        count = communities.count_documents({})  # getting how many communities in the dn
        copy_communities = []
        for i in range(0, count):  # copy the data in to iterable list
            com = communities.find_one_and_delete({})
            copy_communities.insert(0, com)

        locations = []
        index = 0
        for community in copy_communities:  # extract the locations
            locations.insert(index, community["location"])
            communities.insert_one(copy_communities[index])

        for location in locations:  # cast the locations
            location["latitude"] = float(location["latitude"])
            location["longitude"] = float(location["longitude"])

        # calculate the communities in the area
        local_communities = rd.locations_within_radius(center_location, int(radius), locations)

        communities_to_return = []
        for community in local_communities:
            community_to_add = communities.find_one({"location": community})
            if community_to_add:
                community_to_add['_id'] = str(community_to_add['_id'])  # Convert ObjectId to string
                communities_to_return.append(community_to_add)

        return jsonify({"local_communities": communities_to_return}), 200
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


@community_bp.route('/communities/details_by_area', methods=['POST'])
def get_community_details_by_area_name():
    # Extract area name from query parameter
    area = request.args.get('area')

    if not area:
        return jsonify({"error": "Area name is required"}), 400

    # Find the community by its area name
    community = communities.find_one({"area": area}, {"_id": 0})  # Excluding MongoDB's _id from the response

    if not community:
        return jsonify({"error": "Community not found"}), 404

    # Return the found community details
    return jsonify(community), 200


@community_bp.route('/communities/get_all', methods=['GET'])
def get_communities():
    try:
        # Retrieve all community documents from the database
        all_communities = communities.find({})

        # Convert each MongoDB document into a Python dictionary
        communities_list = []
        for community in all_communities:
            # Optionally, convert the _id field from ObjectId to string if you want to include it
            community['_id'] = str(community['_id'])
            communities_list.append(community)

        # Return the list of communities as JSON
        return jsonify({"communities": communities_list}), 200
    except errors.PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


@community_bp.route('/communities/request_to_join', methods=['POST'])
def request_to_join_community():
    data = request.json
    area = data.get('area')
    sender_id = data.get('sender_id')
    sender_name = data.get('sender_name')

    # Validate sender_id
    sender = users.find_one({"id": sender_id})
    if not sender:
        return jsonify({"error": "Invalid sender ID"}), 404

    # Check if the community exists
    community = communities.find_one({"area": area})
    if not community:
        return jsonify({"error": "Community does not exist"}), 404

    # Generate a unique request ID
    request_id = str(uuid.uuid4())

    # Create the join request object for the user's requests array
    user_join_request = {
        "community_name_request": area,
        "status": "pending"
    }

    # Append the join request to the user's requests array
    users.update_one({"id": sender_id}, {"$push": {"requests": user_join_request}})

    # Create the request object for the community manager
    join_request = {
        "request_id": request_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": "can i join the community?"
    }

    # Update the community document with the join request
    communities.update_one({"area": area}, {"$set": {"join_request": join_request}})

    return jsonify({"message": "Join request sent successfully", "request_id": request_id}), 200


@community_bp.route('/communities/respond_to_join_request', methods=['POST'])
def respond_to_community_join_request():
    data = request.json
    request_id = data.get('request_id')
    response = data.get('response')  # Should be 0 (decline) or 1 (accept)

    # Validate request_id by checking if any community has this join request
    community = communities.find_one({"join_request.request_id": request_id})
    if not community:
        return jsonify({"error": "Invalid request ID"}), 404

    # Get the area name from the community found
    community_area = community['area']
    # Get sender_id from the join_request in the community document
    sender_id = community['join_request']['sender_id']

    # Retrieve the sender's user document
    sender_user = users.find_one({"id": sender_id})
    if not sender_user:
        return jsonify({"error": "Sender user not found"}), 404

    # If response is 1, add the user to the community members and user's communities array
    if response == 1:
        sender_details = {"id": sender_id, "name": sender_user['name']}
        # Add the user to the community members
        communities.update_one({"join_request.request_id": request_id}, {"$push": {"communityMembers": sender_details}})
        # Add the community area name to the user's communities array
        users.update_one({"id": sender_id}, {"$push": {"communities": community_area}})

    # Remove the join request from the community document
    communities.update_one({"join_request.request_id": request_id}, {"$unset": {"join_request": ""}})

    # Remove the request from the user's requests array
    user_join_request = {
        "community_name_request": community_area,
        "status": "pending"
    }
    users.update_one({"id": sender_id}, {"$pull": {"requests": user_join_request}})

    return jsonify({"message": "Response processed successfully"}), 200



