from flask import Blueprint, jsonify, request, abort
from database import DataBase  # Ensure this is accessible from this module
from pymongo.errors import DuplicateKeyError
import uuid

# Initialize database connection
dbase = DataBase()
db = dbase.db
communities = db['communities']
users = db['users']
events = db['events']

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
        'event_id' : event_id,
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

    return jsonify({'message': 'Event created and invitations sent!', 'event_id': str(event_id)}), 201


@events_bp.route('/events/get_all_events', methods=['GET'])
def get_all_events():
    all_events = events.find({})  # Retrieve all documents from the events collection
    # Convert the events to a list of dicts, excluding the '_id' field to make them JSON serializable
    events_list = [{key: value for key, value in event.items() if key != '_id'} for event in all_events]
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
        return jsonify({"error": "User not found"}), 404

    # Find the request object that the user is responding to
    event_request = next((req for req in user['requests'] if
                          req['event_request'] == event_name and req['community_name'] == community_name), None)
    if not event_request:
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

    return jsonify({"message": "Event response recorded and request removed"}), 200

@events_bp.route('/events/delete_event', methods=['POST'])
def delete_event():
    data = request.json
    event_id_to_delete = data['event_id']

    # Check if the event exists in the 'events' collection
    if not events.find_one({'event_id': event_id_to_delete}):
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

    # Optionally, remove any requests associated with this event from users' documents
    users.update_many(
        {},
        {'$pull': {'requests': {'event_id': event_id_to_delete}}}
    )

    return jsonify({'message': 'Event deleted successfully!'}), 200


