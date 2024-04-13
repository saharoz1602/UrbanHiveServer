import os

from flask import Blueprint, jsonify, request
from datetime import datetime

from Infastucture.Files import config
from database import DataBase
from pymongo.errors import DuplicateKeyError
from Logic.NightWatchPositionsCalculator import NightWatchPositionsCalculator
from Logic.app_logger import setup_logger
import uuid

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']
events = db['events']
posting = db['posting']
night_watch = db['night_watch']

log_file_path = os.path.join(config.application_file_path, "night_watch.log")
night_watch_logger = setup_logger('night_watch_logger', log_file_path)

# Create a Flask Blueprint for the posting routes
night_watch_bp = Blueprint('night_watch', __name__)


@night_watch_bp.route('/night_watch/add_night_watch', methods=['POST'])
def add_new_night_watch():
    # Parse the JSON data from the request
    data = request.get_json()

    initiator_id = data.get('initiator_id')
    community_area = data.get('community_area')
    watch_date = data.get('watch_date')
    watch_radius = data.get('watch_radius')
    positions_amount = data.get('positions_amount')

    if not all([initiator_id, community_area, watch_date, watch_radius, positions_amount]):
        # If any of the required fields are missing, return an error
        night_watch_logger.error(f"Error: Missing required fields, status code is 404")
        return jsonify({"error": "Missing required fields"}), 400

    # Validate that there isn't already a night watch with the same area and date
    existing_watch = night_watch.find_one({"community_area": community_area, "watch_date": watch_date})
    if existing_watch:
        night_watch_logger.error(f"Error: A night watch is already scheduled for this community area and date, status code is 409")
        return jsonify({"error": "A night watch is already scheduled for this community area and date"}), 409

    # Check if the initiator is a member of the community
    community = communities.find_one({"area": community_area, "communityMembers.id": initiator_id})
    if not community:
        # If the community does not exist or the user is not a member, return an error
        night_watch_logger.error(f"Error: Initiator is not a member of the community status code is 404")
        return jsonify({"error": "Initiator is not a member of the community"}), 404

    # Get user details from the database
    initiator = users.find_one({"id": initiator_id}, {"_id": 0, "id": 1, "name": 1})
    if not initiator:
        # If the user does not exist in the database, return an error
        night_watch_logger.error(f"Error: Initiator not found, status code is 404")
        return jsonify({"error": "Initiator not found"}), 404

    # Generate a unique watch_id
    watch_id = str(uuid.uuid4())

    # Prepare the watch object to be inserted
    watch = {
        "watch_id": watch_id,
        "initiator_id": initiator['id'],
        "initiator_name": initiator['name'],
        "community_area": community_area,
        "watch_date": watch_date,
        "watch_radius": watch_radius,
        "positions_amount": positions_amount,
        "watch_members": []
    }
    # Prepare the night_watch entry for the community document
    community_night_watch_entry = {
        "watch_date": watch_date,
        "watch_id": watch_id
    }

    try:
        # Insert the new watch into the night_watch collection
        night_watch.insert_one(watch)
        # Update the communities collection with the night_watch details
        communities.update_one(
            {"area": community_area},
            {"$push": {"night_watches": community_night_watch_entry}}
        )
        night_watch_logger.info(f"Night watch added successfully, watch id : {watch_id}, status code is 200")
        return jsonify({"message": "Night watch added successfully", "watch_id": watch_id}), 200

    except DuplicateKeyError:
        night_watch_logger.error(f"Night watch with this ID already exists, status code is 409")
        return jsonify({"error": "Night watch with this ID already exists"}), 409
    except Exception as e:
        # For any other exception, return a database error
        night_watch_logger.error(f"Database error : details {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@night_watch_bp.route('/night_watch/join_watch', methods=['POST'])
def join_night_watch():
    # Parse the JSON data from the request
    data = request.get_json()

    candidate_id = data.get('candidate_id')
    night_watch_id = data.get('night_watch_id')

    if not all([candidate_id, night_watch_id]):
        # If any of the required fields are missing, return an error
        night_watch_logger.error(f"Missing required fields, status code is 400")
        return jsonify({"error": "Missing required fields"}), 400

    # Check if the candidate exists
    candidate = users.find_one({"id": candidate_id})
    if not candidate:
        night_watch_logger.error(f"Candidate not found, status code is 404")
        return jsonify({"error": "Candidate not found"}), 404

    # Find the night watch entry
    watch = night_watch.find_one({"watch_id": night_watch_id})
    if not watch:
        night_watch_logger.error(f"Night watch not found, status code is 404")
        return jsonify({"error": "Night watch not found"}), 404

    # Check if there is space available in the watch
    if len(watch['watch_members']) >= int(watch['positions_amount']):
        night_watch_logger.error(f"No positions available in this night watch, status code is 409")
        return jsonify({"error": "No positions available in this night watch"}), 409

    # Add candidate to the night watch
    try:
        night_watch.update_one(
            {"watch_id": night_watch_id},
            {"$push": {"watch_members": {"id": candidate_id, "name": candidate['name']}}}
        )

        # Add night watch info to the candidate's night_watches list
        watch_entry_for_user = {
            "date": watch['watch_date'],
            "community_area": watch['community_area'],
            "watch_id": night_watch_id
        }
        users.update_one(
            {"id": candidate_id},
            {"$push": {"night_watches": watch_entry_for_user}}
        )
        night_watch_logger.info(f"Candidate successfully joined night watch, status code is 200")
        return jsonify({"message": "Candidate successfully joined night watch"}), 200

    except Exception as e:
        night_watch_logger.error(f"Database error: details : {str(e)}, status code is 500")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@night_watch_bp.route('/night_watch/close_night_watch', methods=['POST'])
def close_night_watch():
    data = request.get_json()
    watch_id = data.get('watch_id')

    if not watch_id:
        night_watch_logger.error("Missing watch_id field, status code is 400")
        return jsonify({"error": "Missing watch_id field"}), 400

    # Find the night watch entry to get the details before deletion
    watch = night_watch.find_one({"watch_id": watch_id})
    if not watch:
        night_watch_logger.error("Night watch not found, status code is 404")
        return jsonify({"error": "Night watch not found"}), 404

    # Store community_area and watch_date to remove from the community document
    community_area = watch['community_area']
    watch_date = watch['watch_date']

    # Remove the night watch from the night_watch collection
    night_watch.delete_one({"watch_id": watch_id})

    # Remove the night watch from all users' night_watches list
    users.update_many(
        {},
        {"$pull": {"night_watches": {"watch_id": watch_id}}}
    )

    # Remove the night watch from the community's night_watches list
    communities.update_one(
        {"area": community_area},
        {"$pull": {"night_watches": {"watch_id": watch_id}}}
    )
    night_watch_logger.info("Night watch closed successfully, status code is 200")
    return jsonify({"message": "Night watch closed successfully"}), 200


@night_watch_bp.route('/night_watch/calculate_position_for_watch', methods=['POST'])
def calculate_position_for_watch():
    data = request.get_json()
    watch_id = data.get('watch_id')

    if not watch_id:
        night_watch_logger.error("Missing watch_id field, status code is 400")
        return jsonify({"error": "Missing watch_id field"}), 400

    # Find the night watch entry
    watch = night_watch.find_one({"watch_id": watch_id})
    if not watch:
        night_watch_logger.error("Night watch not found, status code is 404")
        return jsonify({"error": "Night watch not found"}), 404

    position_amount = int(watch['positions_amount'])
    members = watch['watch_members']
    community_area = watch['community_area']
    community = communities.find_one({"area": community_area})
    location = community['location']
    radius = float(watch["watch_radius"])

    position_calculator = NightWatchPositionsCalculator(location)

    # Generate positions
    positions = position_calculator.generate_circle_positions(radius, len(members))

    # Assign members to positions
    inlays = position_calculator.assign_member_to_position(positions, members)

    try:
        # Update the night_watch document with inlays
        night_watch.update_one(
            {"watch_id": watch_id},
            {
                "$set": {
                    "position_inlays": inlays
                }
            }
        )

        if len(members) < position_amount:
            urgent_message = ("The number of volunteers in the watch is less than the number of positions assigned to "
                              "the watch")
            night_watch.update_one({"watch_id": watch_id}, {"$set": {"urgent_message": urgent_message}})

        night_watch_logger.info(f"Positions calculated and members assigned, inlays is {inlays}, status code is 200 ")
        return jsonify({"message": "Positions calculated and members assigned", "inlays": inlays}), 200

    except Exception as e:
        # For any exception, return a database error
        night_watch_logger.error(f"Database error: details : {str(e)}, status code is 500")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@night_watch_bp.route('/night_watch/by_community', methods=['POST'])
def get_night_watches_by_community():
    data = request.get_json()
    community_name = data.get('community_name')

    if not community_name:
        # If community_name is not provided, return an error
        night_watch_logger.error("Missing 'community_name' in request body, status code is 400")
        return jsonify({"error": "Missing 'community_name' in request body"}), 400

    # Get the current date in the same format as your 'watch_date'
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Attempt to find future night watches with the given community_area
    # Ensure your 'watch_date' in the database is stored in a format that allows this type of comparison
    matching_night_watches = list(night_watch.find({
        "community_area": community_name,
        "watch_date": {"$gte": current_date}
    }, {"_id": 0}))

    if not matching_night_watches:
        # If no future night watches are found for the community, check if the community exists
        if not communities.find_one({"area": community_name}):
            night_watch_logger.error(f"Community named '{community_name}' not found, status code is 404")
            return jsonify({"error": "Community not found"}), 404
        else:
            # The community exists but has no future night watches
            night_watch_logger.info(f"No future night watches found for community '{community_name}', status code is 200")
            return jsonify({"message": "No future night watches found for this community"}), 200

    # If future night watches are found, return them
    night_watch_logger.info(f"Found future night watches for community '{community_name}', status code is 200")
    return jsonify({"night_watches": matching_night_watches}), 200

