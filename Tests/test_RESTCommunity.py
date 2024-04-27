import json
import sys
import uuid
import os

# Absolute path to the directory where app2.py is located
infrastructure_path = '/Users/saharoz/Desktop/Study/personal/UrbanHiveServer/Infrastructure'

sys.path.insert(0, infrastructure_path)

from Infrastructure.app2 import create_app  # This should work now that we've added the correct path
from flask_pymongo import PyMongo
from flask_testing import TestCase


class TestRESTCommunity(TestCase):

    def create_app(self):
        app = create_app()
        app.config["MONGO_URI"] = "mongodb://localhost:27017/UrbanHive"
        app.config['TESTING'] = True
        PyMongo(app)
        return app

    def setUp(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            # Set up initial data state here, adding users and communities
            user_data_danor = {
                "id": "311156616",
                "name": "danor",
                "email": "danors@gmail.com",
                "password": "Ds0502660865",
                "phoneNumber": "1234567890",
                "location": {"latitude": 37.4219909, "longitude": -122.0839496}
            }
            mongo.db.users.insert_one(user_data_danor)

            user_data_sahar = {
                "id": "311285514",
                "name": "sahar",
                "email": "saharo@gmail.com",
                "password": "So0509813056",
                "phoneNumber": "0987654321",
                "location": {"latitude": 37.4219911, "longitude": -122.0839476}
            }
            mongo.db.users.insert_one(user_data_sahar)

            community_data = {
                "community_id": str(uuid.uuid4()),
                "area": "TestArea",
                "location": {"latitude": 37.4219909, "longitude": -122.0839496},
                "rules": ["No loud noises", "No pets"],
                "communityMembers": [user_data_danor],
                "communityManagers": [user_data_danor],
                "events": []
            }
            mongo.db.communities.insert_one(community_data)

    def tearDown(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.users.drop()
            mongo.db.communities.drop()

    def test_add_and_get_communities(self):
        # Deleting the community database for the test
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.communities.drop()

        # Simulate adding a community 1 with the user danor
        community_data = {
            "manager_id": "311156616",
            "area": "NewArea",
            "location": {"latitude": 37.4220000, "longitude": -122.0840000}
        }
        response = self.client.post('/communities/add_community', json=community_data)
        self.assertEqual(response.status_code, 201)

        # Simulate adding a community 2 with the user sahar
        community_data = {
            "manager_id": "311285514",
            "area": "NewArea2",
            "location": {"latitude": 37.4220001, "longitude": -122.0840001}
        }
        response = self.client.post('/communities/add_community', json=community_data)
        self.assertEqual(response.status_code, 201)

        # Validate the community has been added to the database
        response = self.client.get('/communities/get_all')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        print(data)
        self.assertTrue(isinstance(data['communities'], list))
        self.assertTrue(any(community['area'] == "NewArea" for community in data['communities']),
                        "The new community should be in the database.")

        self.assertTrue(any(community['area'] == "NewArea2" for community in data['communities']),
                        "The new community should be in the database.")

    def test_add_user_to_community(self):
        # Simulate adding a user to a community
        data = {
            "receiver_id": "311285514",
            "sender_id": "311156616",
            "community area": "TestArea"
        }
        response = self.client.post('/communities/add_user_to_community', json=data)
        self.assertEqual(response.status_code, 200)

        # Fetch both users from the database to check their community requests
        with self.app.app_context():
            mongo = PyMongo(self.app)
            sender_user = mongo.db.users.find_one({"id": data['sender_id']})
            receiver_user = mongo.db.users.find_one({"id": data['receiver_id']})

            # Validate that the community request was added correctly
            # Assuming community_requests attribute stores the requests, change as per actual implementation
            self.assertIn('communityRequest', sender_user)
            self.assertIn('communityRequest', receiver_user)

            # Validate the details of the request stored in the community_requests attribute
            # Here you will check if the details of the request including the ids and statuses are correct
            sender_request = sender_user['communityRequest']
            receiver_request = receiver_user['communityRequest']

            self.assertEqual(sender_request['community request'], 'TestArea')
            self.assertEqual(sender_request['status'], 'pending from 311285514')

            self.assertEqual(receiver_request['community request'], 'TestArea')
            self.assertEqual(receiver_request['status'], 'waiting for your response')

    def test_delete_user_from_community(self):
        # First, add a user to a community to ensure there's something to delete
        self.client.post('/communities/add_user_to_community', json={
            "receiver_id": "311285514",
            "sender_id": "311156616",
            "community area": "TestArea"
        })

        # Delete a user from a community
        response = self.client.post('/communities/delete_user_from_community', json={
            "user_to_delete_id": "311285514",
            "area": "TestArea"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("User removed from community successfully", response.get_json()["message"])

        # Verify that the user has been removed from the community
        with self.app.app_context():
            mongo = PyMongo(self.app)
            community = mongo.db.communities.find_one({"area": "TestArea"})
            # Check if the user is not in the communityMembers list
            self.assertNotIn("311285514", [member['id'] for member in community.get("communityMembers", [])])

            # Optionally, check that the user's list of communities does not include this area
            user = mongo.db.users.find_one({"id": "311285514"})
            self.assertNotIn("TestArea", user.get("communities", []))



# To allow running the tests from the command line
if __name__ == '__main__':
    from unittest import main

    main()
