from flask import jsonify, request
# from flask.logging import create_logger
#
#
# @user_bp.route('/user/', methods=['POST'])
# def add_user():
#     user_logger = create_logger(user_bp)  # Ensure you have a logger configured for your Blueprint
#
#     try:
#         user_data = request.get_json()
#         required_fields = ["id", "name", "email", "password", "phoneNumber", "location"]
#
#         # Check if all required fields are present
#         if not all(field in user_data for field in required_fields):
#             return jsonify({"description": "Missing required field(s)"}), 400
#
#         # Check if location fields are present
#         if not all(field in user_data["location"] for field in ["latitude", "longitude"]):
#             return jsonify({"description": "Missing required location field(s)"}), 400
#
#         # Validate latitude and longitude types
#         if not isinstance(user_data["location"]["latitude"], (float, int)) or \
#                 not isinstance(user_data["location"]["longitude"], (float, int)):
#             return jsonify({"description": "Invalid data type for latitude or longitude"}), 400
#
#         user_data["friends"] = []
#         user_data["requests"] = []
#         user_data["radius"] = None
#
#         # Check if the user already exists
#         if users.find_one({"$or": [{"id": user_data["id"]}, {"email": user_data["email"]}]}):
#             user_logger.error("User with this ID or email already exists, status code is 409")
#             return jsonify({"message": "User with this ID or email already exists"}), 409
#
#         # Insert the new user data
#         inserted = users.insert_one(user_data)
#         user_data.pop("password", None)  # Remove password from the response
#         user_data["_id"] = str(inserted.inserted_id)
#         user_logger.info("User added successfully, status code is 201")
#         return jsonify({"message": "User added successfully", "user": user_data}), 201
#
#     except Exception as e:
#         user_logger.error(f"Unexpected error occurred: {str(e)}")
#         return jsonify({"error": "Internal Server Error", "detail": str(e)}), 500