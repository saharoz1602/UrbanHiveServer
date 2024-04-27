import json
import sys
import os
import uuid

# Absolute path to the directory where app2.py is located
infrastructure_path = '/Users/saharoz/Desktop/Study/personal/UrbanHiveServer/Infrastructure'

sys.path.insert(0, infrastructure_path)

from Infrastructure.app2 import create_app
from flask_pymongo import PyMongo
from flask_testing import TestCase


class TestRESTNightWatch(TestCase):

    def create_app(self):
        app = create_app()
        app.config["MONGO_URI"] = "mongodb://localhost:27017/UrbanHive"
        app.config['TESTING'] = True
        PyMongo(app)
        return app

    def setUp(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            self.user = {
                "id": "user001",
                "name": "John Doe"
            }
            self.community = {
                "area": "TestArea",
                "communityMembers": [{"id": "user001", "name": "John Doe"}],
                "night_watches": []
            }
            mongo.db.users.insert_one(self.user)
            mongo.db.communities.insert_one(self.community)

    def tearDown(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.users.drop()
            mongo.db.communities.drop()
            mongo.db.night_watch.drop()

    def test_add_new_night_watch(self):
        watch_data = {
            "initiator_id": "user001",
            "community_area": "TestArea",
            "watch_date": "2023-12-31",
            "watch_radius": 100,
            "positions_amount": 5,
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = self.client.post('/night_watch/add_night_watch', json=watch_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Night watch added successfully', response.get_json()['message'])

    def test_join_night_watch(self):
        # First, add a night watch
        with self.app.app_context():
            mongo = PyMongo(self.app)
            watch_id = str(uuid.uuid4())
            watch = {
                "watch_id": watch_id,
                "initiator_id": "user001",
                "community_area": "TestArea",
                "watch_date": "2023-12-31",
                "watch_radius": 100,
                "positions_amount": 5,
                "watch_members": [],
                "location": {"latitude": 37.7749, "longitude": -122.4194}
            }
            mongo.db.night_watch.insert_one(watch)

        # Join the night watch
        join_data = {
            "candidate_id": "user001",
            "night_watch_id": watch_id
        }
        response = self.client.post('/night_watch/join_watch', json=join_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Candidate successfully joined night watch', response.get_json()['message'])

        # Retrieve the night watch from the database to confirm it was added
        with self.app.app_context():
            mongo = PyMongo(self.app)
            night_watch = mongo.db.night_watch.find_one({
                "initiator_id": "user001",
                "community_area": "TestArea",
                "watch_date": "2023-12-31"
            })
            self.assertIsNotNone(night_watch, "The night watch should exist in the database")
            self.assertEqual(night_watch['watch_radius'], 100)
            self.assertEqual(night_watch['positions_amount'], 5)
            self.assertEqual(night_watch['location']['latitude'], 37.7749)
            self.assertEqual(night_watch['location']['longitude'], -122.4194)

    def test_close_night_watch(self):
        # First, add a night watch to close
        with self.app.app_context():
            mongo = PyMongo(self.app)
            watch_id = str(uuid.uuid4())
            watch = {
                "watch_id": watch_id,
                "initiator_id": "user001",
                "community_area": "TestArea",
                "watch_date": "2023-12-31",
                "watch_radius": 100,
                "positions_amount": 5,
                "watch_members": [],
                "location": {"latitude": 37.7749, "longitude": -122.4194}
            }
            mongo.db.night_watch.insert_one(watch)

        # Close the night watch
        close_data = {"watch_id": watch_id}
        response = self.client.post('/night_watch/close_night_watch', json=close_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Night watch closed successfully', response.get_json()['message'])

        # Validate that the night watch has been removed from the database
        with self.app.app_context():
            mongo = PyMongo(self.app)
            watch_after_deletion = mongo.db.night_watch.find_one({"watch_id": watch_id})
            self.assertIsNone(watch_after_deletion, "The night watch should no longer exist in the database")

            # Optionally, verify that the watch is also removed from any associated community documents
            community_after_deletion = mongo.db.communities.find_one({"area": "TestArea"})
            if 'night_watches' in community_after_deletion:
                self.assertNotIn(watch_id,
                                 [watch['watch_id'] for watch in community_after_deletion.get('night_watches', [])],
                                 "The night watch ID should not be in the community's night watches list")

    def test_calculate_position_for_watch(self):
        # Add community via the API
        community_data = {
            "community_name": "TestArea",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        community_response = self.client.post('/community/add_community', json=community_data)
        self.assertEqual(community_response.status_code, 200)
        self.assertIn('Community added successfully', community_response.get_json()['message'])

        # Add users via the API
        user_data1 = {
            "id": "user001",
            "name": "John Doe",
            "community_area": "TestArea"
        }
        user_response1 = self.client.post('/users/add_user', json=user_data1)
        self.assertEqual(user_response1.status_code, 200)
        self.assertIn('User added successfully', user_response1.get_json()['message'])

        user_data2 = {
            "id": "user002",
            "name": "Jane Smith",
            "community_area": "TestArea"
        }
        user_response2 = self.client.post('/users/add_user', json=user_data2)
        self.assertEqual(user_response2.status_code, 200)
        self.assertIn('User added successfully', user_response2.get_json()['message'])

        # Add a night watch via the API
        watch_data = {
            "initiator_id": "user001",
            "community_area": "TestArea",
            "watch_date": "2023-12-31",
            "watch_radius": 100,
            "positions_amount": 5,
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        add_watch_response = self.client.post('/night_watch/add_night_watch', json=watch_data)
        self.assertEqual(add_watch_response.status_code, 200)
        self.assertIn('Night watch added successfully', add_watch_response.get_json()['message'])
        watch_id = add_watch_response.get_json()['watch_id']

        # Join the night watch with multiple members via API
        join_data1 = {
            "candidate_id": "user001",
            "night_watch_id": watch_id
        }
        join_response1 = self.client.post('/night_watch/join_watch', json=join_data1)
        self.assertEqual(join_response1.status_code, 200)

        join_data2 = {
            "candidate_id": "user002",
            "night_watch_id": watch_id
        }
        join_response2 = self.client.post('/night_watch/join_watch', json=join_data2)
        self.assertEqual(join_response2.status_code, 200)

        # Calculate positions using the watch_id
        position_data = {"watch_id": watch_id}
        response = self.client.post('/night_watch/calculate_position_for_watch', json=position_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Positions calculated and members assigned', response.get_json()['message'])


# To allow running the tests from the command line
if __name__ == '__main__':
    from unittest import main

    main()
