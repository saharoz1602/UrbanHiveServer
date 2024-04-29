import json
import sys
import os

# Absolute path to the directory where app.py is located
infrastructure_path = '/Users/saharoz/Desktop/Study/personal/UrbanHiveServer/Infrastructure'

sys.path.insert(0, infrastructure_path)

from Infrastructure.app import create_app  # This should work now that we've added the correct path
from flask_pymongo import PyMongo
from flask_testing import TestCase


class MyTest(TestCase):

    def create_app(self):
        # Create the Flask application using the factory from app.py
        # This function should return the Flask app instance
        app = create_app()
        # Configure the MongoDB settings for testing
        # Ensure to use a separate test database to avoid modifying production data
        app.config["MONGO_URI"] = "mongodb://localhost:27017/UrbanHive"
        app.config['TESTING'] = True
        # Initialize PyMongo with the Flask app
        # This needs to be called with the test instance of the app
        PyMongo(app)
        return app

    def setUp(self):
        # Before each test, set up your database environment such as creating collections
        with self.app.app_context():
            mongo = PyMongo(self.app)
            # mongo.db.users.drop()
            # Mock user data
            user_data = {
                "id": "311156616",
                "name": "danor",
                "email": "danors@gmail.com",
                "password": "Ds0502660865",
                "phoneNumber": "1234567890",
                "location": {"latitude": 37.4219909, "longitude": -122.0839496}
            }
            mongo.db.users.insert_one(user_data)

    def tearDown(self):
        # After each test, clean up the database environment
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.users.drop()

    def test_get_users(self):
        # Call the get_users endpoint
        response = self.client.get('/users')

        # Check if the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Load the response data into a JSON object
        data = json.loads(response.data)

        # Check if the keys "message" and "users" are in the response
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Users fetched successfully')
        self.assertIn('users', data)

        # Check if we have one user in our response
        self.assertEqual(len(data['users']), 1)
        print(data['users'])

        # Check if the user's name and email are correct
        # Ensure you're checking against the user setup in the test database
        self.assertEqual(data['users'][0]['name'], 'danor')
        self.assertEqual(data['users'][0]['email'], 'danors@gmail.com')

        # Verify that the _id field has been converted to a string
        self.assertIsInstance(data['users'][0]['_id'], str)

    def test_add_user_success(self):
        # Mock user data
        user_data = {
            "id": "311285514",
            "name": "sahar",
            "email": "saharo@gmail.com",
            "password": "So0509813056",
            "phoneNumber": "0987654321",
            "location": {"latitude": 37.4219909, "longitude": -122.0839496}
        }
        response = self.client.post('/user/', json=user_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('User added successfully', response.json['message'])

    def test_add_user_missing_field(self):
        # Missing the 'name' field
        user_data = {
            "id": "311285514",
            "email": "saharo@gmail.com",
            "password": "So0509813056",
            "phoneNumber": "0987654321",
            "location": {"latitude": 37.4219909, "longitude": -122.0839496}
        }
        response = self.client.post('/user/', json=user_data)
        self.assertEqual(response.status_code, 400)  # Ensure this is expecting 400, not 500
        self.assertIn('Missing required field(s)', response.json['description'])

    def test_get_user_by_id_found(self):
        # Assuming a user with this ID has been added in the setUp
        response = self.client.get('/user/311156616')  # Use an existing user ID
        self.assertEqual(response.status_code, 200)
        self.assertIn('danor', response.json['name'])

    def test_get_user_by_id_not_found(self):
        response = self.client.get('/user/nonexistentid')
        self.assertEqual(response.status_code, 404)

    def test_delete_user_success(self):
        response = self.client.delete('/user/311156616')  # Use an existing user ID
        self.assertEqual(response.status_code, 200)

    def test_delete_user_not_found(self):
        response = self.client.delete('/user/nonexistentid')
        self.assertEqual(response.status_code, 404)

    def test_check_user_password_correct(self):
        user_data = {"id": "311156616", "password": "Ds0502660865"}
        response = self.client.post('/users/password', json=user_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['result'])

    def test_check_user_password_incorrect(self):
        user_data = {"id": "311156616", "password": "wrongpassword"}
        response = self.client.post('/users/password', json=user_data)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json['result'])

    def test_change_password_success(self):
        password_data = {"id": "311156616", "new_password": "newpassword", "verify_new_password": "newpassword"}
        response = self.client.post('/user/change-password', json=password_data)
        self.assertEqual(response.status_code, 200)

    def test_change_password_mismatch(self):
        password_data = {"id": "311156616", "new_password": "newpassword", "verify_new_password": "differentpassword"}
        response = self.client.post('/user/change-password', json=password_data)
        self.assertEqual(response.status_code, 400)

    def test_update_user_radius_success(self):
        response = self.client.put('/user/311156616/radius', json={"radius": 5.0})
        self.assertEqual(response.status_code, 200)

    def test_update_user_radius_invalid(self):
        response = self.client.put('/user/311156616/radius', json={"radius": "notafloat"})
        self.assertEqual(response.status_code, 400)

    def test_add_friend_success(self):
        user_data = {
            "id": "311285514",
            "name": "sahar",
            "email": "saharo@gmail.com",
            "password": "So0509813056",
            "phoneNumber": "0987654321",
            "location": {"latitude": 37.4219909, "longitude": -122.0839496}
        }
        self.client.post('/user/', json=user_data)
        response = self.client.post('/user/add-friend', json={"sender_id": "311156616", "receiver_id": "311285514"})
        self.assertEqual(response.status_code, 200)

        # checking the request has been added to both data bases of both users (danor from set-up sahar from test)
        response_user = self.client.get('/user/311285514')
        self.assertEqual(response_user.status_code, 200)
        self.assertIn('requests', response_user.json)
        self.assertTrue(any(request['id'] == "311156616" for request in response_user.json['requests']))

        response_user = self.client.get('/user/311156616')
        self.assertEqual(response_user.status_code, 200)
        self.assertIn('requests', response_user.json)
        self.assertTrue(any(request['id'] == "311285514" for request in response_user.json['requests']))

    def test_respond_to_request_accept(self):
        user_data = {
            "id": "311285514",
            "name": "sahar",
            "email": "saharo@gmail.com",
            "password": "So0509813056",
            "phoneNumber": "0987654321",
            "location": {"latitude": 37.4219909, "longitude": -122.0839496}
        }
        self.client.post('/user/', json=user_data)
        self.client.post('/user/add-friend', json={"sender_id": "311156616", "receiver_id": "311285514"})
        response = self.client.post('/user/respond-to-request',
                                    json={"receiver_id": "311156616", "sender_id": "311285514", "response": 1})
        self.assertEqual(response.status_code, 200)

        # Retrieve both users to check friends list
        response_user1 = self.client.get('/user/311156616')
        self.assertEqual(response_user1.status_code, 200)
        self.assertTrue(any(friend['friend id'] == "311285514" for friend in response_user1.json.get('friends', [])))

        response_user2 = self.client.get('/user/311285514')
        self.assertEqual(response_user2.status_code, 200)
        self.assertTrue(any(friend['friend id'] == "311156616" for friend in response_user2.json.get('friends', [])))


# To allow running the tests from the command line
if __name__ == '__main__':
    from flask_testing import LiveServerTestCase
    from unittest import main


    # If your tests need a live server, use LiveServerTestCase
    # Otherwise, just TestCase should be enough
    class MyLiveTest(LiveServerTestCase, MyTest):
        pass


    main()
