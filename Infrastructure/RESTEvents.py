import os
from datetime import datetime

from flask import Blueprint, jsonify, request, abort

from Infrastructure.Files import config
from database import DataBase
from pymongo.errors import DuplicateKeyError
from Logic.app_logger import setup_logger
import uuid

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']
events = db['events']

# Ensure the log file directory exists
log_file_path = os.path.join(config.application_file_path, "logs/events/events.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Initialize the logger
try:
    events_logger = setup_logger('night_watch_logger', log_file_path)
except Exception as e:
    print(f"Error setting up logger: {e}")

# Create a Flask Blueprint for the event routes
events_bp = Blueprint('events', __name__)


@events_bp.route('/events/add_event', methods=['POST'])
def add_event():
    data = request.json

    # Retrieve event information from the request
    event_initiator_id = data['initiator']
    community_name = data['community_name']
    event_location = data['location']
    event_name = data['event_name']
    event_type = data['event_type']
    start_time = data['start_time']
    end_time = data['end_time']
    guest_list = data['guest_list']

    event_id = str(uuid.uuid4())

    # Create a new event document
    event_doc = {
        'event_id': event_id,
        'initiator': event_initiator_id,
        'community_name': community_name,
        'location': event_location,
        'event_name': event_name,
        'event_type': event_type,
        'start_time': start_time,
        'end_time': end_time,
        'guests': guest_list,
        'attending': []
    }

    # Add event reference to the community document
    try:
        communities.update_one(
            {'area': community_name},
            {'$push': {'events': event_doc}}
        )
        users.update_one(
            {'id': event_initiator_id},
            {'$push': {'events': event_doc}}
        )
    except Exception as e:
        abort(400, str(e))

    # Insert the event into the events database
    event_id = None
    try:
        event_id = events.insert_one(event_doc).inserted_id
    except DuplicateKeyError as e:
        abort(400, str(e))

    # Create the invitation format
    invitation = {
        'event_request': event_name,
        'event_id': event_id,
        'community_name': community_name,
        'location': event_location,
        'event_type': event_type,
        'start_time': start_time,
        'end_time': end_time,
        'status': 'waiting for your response'
    }

    # Send invitations to each guest by their ID
    for guest_id in guest_list:
        try:
            users.update_one(
                {'id': guest_id},  # Query by 'id' field
                {'$push': {'requests': invitation}}
            )
        except Exception as e:
            abort(400, str(e))
    events_logger.info(f"Event created and invitations sent!, event id = {str(event_id)}")
    return jsonify({'message': 'Event created and invitations sent!', 'event_id': str(event_id)}), 201


@events_bp.route('/events/get_all_events', methods=['GET'])
def get_all_events():
    all_events = events.find({})  # Retrieve all documents from the events collection
    # Convert the events to a list of dicts, excluding the '_id' field to make them JSON serializable
    events_list = [{key: value for key, value in event.items() if key != '_id'} for event in all_events]
    events_logger.info(f"Events list : {events_list}")
    return jsonify(events_list), 200


@events_bp.route('/events/respond_to_event_request', methods=['POST'])
def respond_to_event_request():
    # Parse the incoming JSON data
    data = request.get_json()

    # Extract necessary information
    user_id = data.get('user_id')
    community_name = data.get('community_name')
    event_name = data.get('event_name')
    response = data.get('response')  # This could be a boolean where True means accept, False means decline

    # Fetch the user from the users collection
    user = users.find_one({"id": user_id})
    if not user:
        events_logger.error("error : user not found, status code = 404")
        return jsonify({"error": "User not found"}), 404

    # Find the request object that the user is responding to
    event_request = next((req for req in user['requests'] if
                          req['event_request'] == event_name and req['community_name'] == community_name), None)
    if not event_request:
        events_logger.error("error : Event request not found, status code = 404")
        return jsonify({"error": "Event request not found"}), 404

    # Remove the event request from the user's document
    users.update_one(
        {"id": user_id},
        {"$pull": {"requests": event_request}}
    )

    # If the user accepts the invitation
    if response:
        # Add the user to the attending list of the event in both 'events' and 'communities' collections
        events.update_one(
            {"community_name": community_name, "event_name": event_name},
            {"$push": {"attending": user_id}}
        )
        communities.update_one(
            {"area": community_name, "events.event_name": event_name},
            {"$push": {"events.$.attending": user_id}}
        )

        # Add the event data to the user's events array
        users.update_one(
            {"id": user_id},
            {"$push": {"events": event_request}}
        )
    events_logger.info("Event response recorded and request removed, status code = 200")
    return jsonify({"message": "Event response recorded and request removed"}), 200


@events_bp.route('/events/delete_event', methods=['POST'])
def delete_event():
    data = request.json
    event_id_to_delete = data['event_id']

    # Check if the event exists in the 'events' collection
    if not events.find_one({'event_id': event_id_to_delete}):
        events_logger.error("Error: Event not found, status code = 404")
        return jsonify({'error': 'Event not found'}), 404

    # Delete the event from the 'events' collection
    events.delete_one({'event_id': event_id_to_delete})

    # Remove the event from the 'communities' documents
    communities.update_many(
        {},
        {'$pull': {'events': {'event_id': event_id_to_delete}}}
    )

    # Remove the event from the 'users' documents
    users.update_many(
        {},
        {'$pull': {'events': {'event_id': event_id_to_delete}}}
    )

    # Remove any requests associated with this event from users' documents
    users.update_many(
        {},
        {'$pull': {'requests': {'event_id': event_id_to_delete}}}
    )
    events_logger.info("Event deleted successfully!, status code = 200")
    return jsonify({'message': 'Event deleted successfully!'}), 200


@events_bp.route('/events/request_to_join_events', methods=['POST'])
def request_to_join_events():
    # Parse the incoming JSON data
    data = request.get_json()

    # Extract necessary information
    user_id = data.get('user_id')
    community_name = data.get('community_name')
    event_id = data.get('event_id')

    # Get the current date and time
    current_date = datetime.utcnow()

    # Verify the user exists and is part of the community
    user = db.users.find_one({"id": user_id, "communityRequest.community_name": community_name})
    if not user:
        events_logger.error("User not found or not part of the community, status code = 404")
        return jsonify({"error": "User not found or not part of the community"}), 404

    # Verify the event exists within the specified community in the events collection
    event = db.events.find_one({"event_id": event_id, "community_name": community_name})
    if not event:
        events_logger.error("Event not found in the specified community, status code = 404")
        return jsonify({"error": "Event not found in the specified community"}), 404

    # Create the request object
    request_to_join = {
        "user_id": user_id,
        "event_id": event_id,
        "community_name": community_name,
        "date": current_date,
        "status": "pending"
    }

    # Add the request to join to the event's requests_to_join array
    db.events.update_one(
        {"event_id": event_id},
        {"$push": {"requests_to_join": request_to_join}}
    )

    # Update the user's document with the request
    db.users.update_one(
        {"id": user_id},
        {"$push": {"requests": {"event_id": event_id, "date": current_date, "status": "pending"}}}
    )

    # Update the community's document with the request
    db.communities.update_one(
        {"community_name": community_name, "events.event_id": event_id},
        {"$push": {"events.$.requests_to_join": request_to_join}}
    )

    return jsonify({"message": "Request to join event has been submitted"}), 200


@events_bp.route('/events/confirm_or_decline_event_request', methods=['POST'])
def confirm_or_decline_event_request():
    # Parse the incoming JSON data
    data = request.get_json()

    # Extract necessary information
    manager_id = data.get('manager_id')
    event_id = data.get('event_id')
    user_id = data.get('user_id')
    community_name = data.get('community_name')
    response = data.get('response')  # 1 for confirm, 0 for decline

    # Validate manager existence and authorization
    manager = db.users.find_one({"id": manager_id})
    if not manager:
        return jsonify({"error": "Manager not found or not authorized"}), 404

    # Validate event existence
    event = db.events.find_one({"event_id": event_id, "community_name": community_name})
    if not event:
        return jsonify({"error": "Event not found in the specified community"}), 404

    # Validate user existence
    user = db.users.find_one({"id": user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404
    # Check if user has requested to join the event
    request_to_join = next((request for requests in event['requests_to_join'] if requests['user_id'] == user_id), None)
    if not request_to_join:
        return jsonify({"error": "User has not requested to join the event"}), 400

    # Update databases based on response (confirm or decline)
    if response == 1:  # Confirm
        # Add user to the event's attendees list
        db.events.update_one(
            {"event_id": event_id},
            {"$push": {"attendees": user_id}}
        )
        # Remove request from event's requests_to_join list
        db.events.update_one(
            {"event_id": event_id},
            {"$pull": {"requests_to_join": {"user_id": user_id}}}
        )
        # Update user's status for the event to attending
        db.users.update_one(
            {"id": user_id},
            {"$push": {"attending_events": event_id}, "$pull": {"requests": {"event_id": event_id}}}
        )
        return jsonify({"message": "Event request has been confirmed successfully"}), 200
    elif response == 0:  # Decline
        # Remove request from event's requests_to_join list
        db.events.update_one(
            {"event_id": event_id},
            {"$pull": {"requests_to_join": {"user_id": user_id}}}
        )
        # Remove request from user's requests list
        db.users.update_one(
            {"id": user_id},
            {"$pull": {"requests": {"event_id": event_id}}}
        )
        return jsonify({"message": "Event request has been declined successfully"}), 200






