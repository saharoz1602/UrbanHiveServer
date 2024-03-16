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
posting = db['posting']

# Create a Flask Blueprint for the event routes
posting_bp = Blueprint('posting', __name__)


@posting_bp.route('/posting/add_post', methods=['POST'])
def add_post():
    # Parse the JSON data from the request
    data = request.get_json()

    # Extract user ID, community area, post content, and post date
    user_id = data.get('user_id')
    community_area = data.get('community_area')
    post_content = data.get('post_content')  # Assumes this is a dict with 'header' and 'body'
    post_date = data.get('post_date')  # Assumes date is a string in ISO format or similar

    if not all([user_id, community_area, post_content, post_date]):
        # If any of the required fields are missing, return an error
        return jsonify({"error": "Missing required fields"}), 400

    # Check if the user is a member of the community
    community = communities.find_one({"area": community_area, "communityMembers.id": user_id})
    if not community:
        # If the community does not exist or the user is not a member, return an error
        return jsonify({"error": "User is not a member of the community"}), 404

    # Get user details from the database
    user = users.find_one({"id": user_id}, {"_id": 0, "id": 1, "name": 1})
    if not user:
        # If the user does not exist in the database, return an error
        return jsonify({"error": "User not found"}), 404

    # Generate a unique post_id
    post_id = str(uuid.uuid4())

    # Prepare the post object to be inserted
    post = {
        "post_id": post_id,
        "user_id": user['id'],
        "user_name": user['name'],
        "community_area": community_area,
        "post_content": post_content,
        "post_date": post_date
    }

    # Add the post to the community document
    communities.update_one(
        {"area": community_area},
        {"$push": {"posts": post}}
    )

    # Add the post to the 'posting' collection
    try:
        posting.insert_one(post)
        return jsonify({"message": "Post added successfully", "post_id": post_id}), 201
    except DuplicateKeyError:
        return jsonify({"error": "Post with this data already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@posting_bp.route('/posting/delete_post', methods=['DELETE'])
def delete_post():
    # Parse the JSON data from the request
    data = request.get_json()

    # Extract post_id
    post_id = data.get('post_id')

    if not post_id:
        # If the post_id is missing, return an error
        return jsonify({"error": "Missing required field: post_id"}), 400

    # Delete the post from the 'posting' collection
    post_delete_result = posting.delete_one({"post_id": post_id})
    if post_delete_result.deleted_count == 0:
        # If the post was not found in the posting collection, return an error
        return jsonify({"error": "Post not found or already deleted"}), 404

    # Remove the post from the community document's posts array
    community_update_result = communities.update_one(
        {"posts.post_id": post_id},
        {"$pull": {"posts": {"post_id": post_id}}}
    )

    # Check if the post was successfully deleted from both collections
    if community_update_result.modified_count == 0:
        # If the post was not found in any community, return a message indicating it
        return jsonify({"message": "Post deleted from postings, but not found in any community"}), 200

    return jsonify({"message": "Post deleted successfully"}), 200


