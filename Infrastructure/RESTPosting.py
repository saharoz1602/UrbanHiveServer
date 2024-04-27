import os

from flask import Blueprint, jsonify, request

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
posting = db['posting']


# Ensure the log file directory exists
log_file_path = os.path.join(config.application_file_path, "logs/posting/posting.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Initialize the logger
try:
    posting_logger = setup_logger('night_watch_logger', log_file_path)
except Exception as e:
    print(f"Error setting up logger: {e}")



# Create a Flask Blueprint for the posting routes
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
        posting_logger.error(f"Missing required fields, status code is 400")
        return jsonify({"error": "Missing required fields"}), 400

    # Check if the user is a member of the community
    community = communities.find_one({"area": community_area, "communityMembers.id": user_id})
    if not community:
        # If the community does not exist or the user is not a member, return an error
        posting_logger.error(f"User is not a member of the community, status code is 404")
        return jsonify({"error": "User is not a member of the community"}), 404

    # Get user details from the database
    user = users.find_one({"id": user_id}, {"_id": 0, "id": 1, "name": 1})
    if not user:
        # If the user does not exist in the database, return an error
        posting_logger.error(f"User not found, status code is 404")
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
        posting_logger.info(f"Post added successfully, post id is {post_id}, status code is 201")
        return jsonify({"message": "Post added successfully", "post_id": post_id}), 201
    except DuplicateKeyError:
        posting_logger.error(f"Post with this data already exists, status code is 409")
        return jsonify({"error": "Post with this data already exists"}), 409
    except Exception as e:
        posting_logger.error(f"error: {str(e)},status code is 500")
        return jsonify({"error": str(e)}), 500


@posting_bp.route('/posting/delete_post', methods=['DELETE'])
def delete_post():
    # Parse the JSON data from the request
    data = request.get_json()

    # Extract post_id
    post_id = data.get('post_id')

    if not post_id:
        # If the post_id is missing, return an error
        posting_logger.error(f"Missing required fields: post_id, status code is 400")
        return jsonify({"error": "Missing required field: post_id"}), 400

    # Delete the post from the 'posting' collection
    post_delete_result = posting.delete_one({"post_id": post_id})
    if post_delete_result.deleted_count == 0:
        # If the post was not found in the posting collection, return an error
        posting_logger.error(f"Post not found or already deleted, status code is 404")
        return jsonify({"error": "Post not found or already deleted"}), 404

    # Remove the post from the community document's posts array
    community_update_result = communities.update_one(
        {"posts.post_id": post_id},
        {"$pull": {"posts": {"post_id": post_id}}}
    )

    # Check if the post was successfully deleted from both collections
    if community_update_result.modified_count == 0:
        # If the post was not found in any community, return a message indicating it
        posting_logger.info(f"Post deleted from postings, but not found in any community, status code is 200")
        return jsonify({"message": "Post deleted from postings, but not found in any community"}), 200
    posting_logger.info(f"Post deleted successfully")
    return jsonify({"message": "Post deleted successfully"}), 200


@posting_bp.route('/posting/add_comment_to_post', methods=['POST'])
def add_comment_to_post():
    # Parse the JSON data from the request
    data = request.get_json()

    # Extract required fields
    post_id = data.get('post_id')
    comment_text = data.get('comment_text')  # Text of the comment
    user_id = data.get('user_id')
    user_name = data.get('user_name')

    if not all([post_id, comment_text, user_id, user_name]):
        # If any required field is missing, return an error
        posting_logger.error(f"Missing required fields, status code is 400")
        return jsonify({"error": "Missing required fields"}), 400

    # Generate a unique comment_id
    comment_id = str(uuid.uuid4())

    # Create the comment object
    comment = {
        "comment_id": comment_id,
        "text": comment_text,
        "user_id": user_id,
        "user_name": user_name
    }

    # Update the post in the 'posting' collection with the new comment
    post_update_result = posting.update_one(
        {"post_id": post_id},
        {"$push": {"comments": comment}}
    )

    if post_update_result.matched_count == 0:
        # If the post is not found in 'posting' collection, return an error
        posting_logger.error(f"Post not found in postings, status code is 404")
        return jsonify({"error": "Post not found in postings"}), 404

    # Update the corresponding post in the community document's posts array
    community_update_result = communities.update_one(
        {"posts.post_id": post_id},
        {"$push": {"posts.$.comments": comment}}
    )

    if community_update_result.matched_count == 0:
        # If the post is not found in any community, return a different message
        posting_logger.info(f"Post updated in postings but not found in any community, status code is 200")
        return jsonify({"warning": "Post updated in postings but not found in any community"}), 200
    posting_logger.info(f"Comment added successfully, status code is 201")
    return jsonify({"message": "Comment added successfully", "comment_id": comment_id}), 201


@posting_bp.route('/posting/delete_comment_from_post', methods=['DELETE'])
def delete_comment_from_post():
    # Parse the JSON data from the request
    data = request.get_json()

    # Extract the post_id and comment_id
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')

    if not post_id or not comment_id:
        # If post_id or comment_id is missing, return an error
        posting_logger.error(f"Missing post_id or comment_id, status code is 400")
        return jsonify({"error": "Missing post_id or comment_id"}), 400

    # Remove the comment from the 'posting' collection
    post_update_result = posting.update_one(
        {"post_id": post_id},
        {"$pull": {"comments": {"comment_id": comment_id}}}
    )

    if post_update_result.matched_count == 0:
        # If the post is not found, return an error
        posting_logger.error(f"Post not found, status code is 404")
        return jsonify({"error": "Post not found"}), 404
    elif post_update_result.modified_count == 0:
        # If the comment is not found, return an error
        posting_logger.error(f"Comment not found or already deleted, status code is 404")
        return jsonify({"error": "Comment not found or already deleted"}), 404

    # Remove the comment from the corresponding community document's post
    community_update_result = communities.update_one(
        {"posts.post_id": post_id},
        {"$pull": {"posts.$.comments": {"comment_id": comment_id}}}
    )

    if community_update_result.matched_count == 0:
        # If the post is not found in the community, return a message indicating it
        posting_logger.info(f"Post found in postings but not in any community status code is 200")
        return jsonify({"warning": "Post found in postings but not in any community"}), 200
    elif community_update_result.modified_count == 0:
        # If the comment is not found in the community, return a message indicating it
        posting_logger.info(f"Comment not found or already deleted from community status code is 200")
        return jsonify({"warning": "Comment not found or already deleted from community"}), 200

    posting_logger.info(f"Comment deleted successfully, status code is 200")
    return jsonify({"message": "Comment deleted successfully"}), 200


