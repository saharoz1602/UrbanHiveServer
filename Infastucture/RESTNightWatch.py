from flask import Blueprint, jsonify, request
from database import DataBase
from pymongo.errors import DuplicateKeyError
import uuid

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']
events = db['events']
posting = db['posting']
night_watch = db['night_watch']

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
        return jsonify({"error": "Missing required fields"}), 400

    # Validate that there isn't already a night watch with the same area and date
    existing_watch = night_watch.find_one({"community_area": community_area, "watch_date": watch_date})
    if existing_watch:
        return jsonify({"error": "A night watch is already scheduled for this community area and date"}), 409

    # Check if the initiator is a member of the community
    community = communities.find_one({"area": community_area, "communityMembers.id": initiator_id})
    if not community:
        # If the community does not exist or the user is not a member, return an error
        return jsonify({"error": "Initiator is not a member of the community"}), 404

    # Get user details from the database
    initiator = users.find_one({"id": initiator_id}, {"_id": 0, "id": 1, "name": 1})
    if not initiator:
        # If the user does not exist in the database, return an error
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

    try:
        # Insert the new watch into the night_watch collection
        night_watch.insert_one(watch)
        return jsonify({"message": "Night watch added successfully", "watch_id": watch_id}), 200
    except DuplicateKeyError:
        return jsonify({"error": "Night watch with this ID already exists"}), 409
    except Exception as e:
        # For any other exception, return a database error
        return jsonify({"error": "Database error", "details": str(e)}), 500



