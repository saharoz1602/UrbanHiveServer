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


class TestRESTEvents(TestCase):

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
                "name": "John Doe",
                "events": [],
                "requests": []
            }
            self.community = {
                "area": "TestArea",
                "events": []
            }
            self.event = {
                "initiator": "user001",
                "community_name": "TestArea",
                "location": {"latitude": 37.4219909, "longitude": -122.0839496},
                "event_name": "Spring Fest",
                "event_type": "Festival",
                "start_time": "2022-04-01T09:00:00Z",
                "end_time": "2022-04-01T18:00:00Z",
                "guest_list": ["user002"]
            }
            mongo.db.users.insert_one(self.user)
            mongo.db.communities.insert_one(self.community)
            mongo.db.events.insert_one(self.event)

    def tearDown(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.users.drop()
            mongo.db.communities.drop()
            mongo.db.events.drop()

    def test_add_event(self):
        event_data = {
            "initiator": "user001",
            "community_name": "TestArea",
            "location": {"latitude": 37.4220000, "longitude": -122.0840000},
            "event_name": "Summer Gala",
            "event_type": "Gala",
            "start_time": "2022-06-01T19:00:00Z",
            "end_time": "2022-06-02T00:00:00Z",
            "guest_list": ["user002", "user003"]
        }
        response = self.client.post('/events/add_event', json=event_data)
        self.assertEqual(response.status_code, 201)

    def test_get_all_events(self):
        response = self.client.get('/events/get_all_events')
        self.assertEqual(response.status_code, 200)
        events = json.loads(response.data)
        self.assertIsInstance(events, list)
        self.assertTrue(any(event['event_name'] == "Spring Fest" for event in events))

    def test_delete_event(self):
        # First, add an event using the API
        event_data = {
            "initiator": "user001",
            "community_name": "TestArea",
            "location": {"latitude": 37.4220000, "longitude": -122.0840000},
            "event_name": "End of Year Party",
            "event_type": "Party",
            "start_time": "2022-12-31T19:00:00Z",
            "end_time": "2023-01-01T01:00:00Z",
            "guest_list": ["user002", "user003"]
        }
        add_event_response = self.client.post('/events/add_event', json=event_data)
        self.assertEqual(add_event_response.status_code, 201)

        # Retrieve the newly added event from the database to get the event_id
        with self.app.app_context():
            mongo = PyMongo(self.app)
            event = mongo.db.events.find_one({"event_name": "End of Year Party"})
            event_id = event['event_id']  # Get the actual event_id

        # Now, delete the event using the fetched event_id
        response = self.client.post('/events/delete_event', json={"event_id": event_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Event deleted successfully!', response.get_json()['message'])

        # Optionally, verify that the event is indeed removed from the database
        with self.app.app_context():
            mongo = PyMongo(self.app)
            event_after_deletion = mongo.db.events.find_one({"event_id": event_id})
            self.assertIsNone(event_after_deletion, "The event should be deleted from the database")
            community = mongo.db.communities.find_one({"area": "TestArea"})
            print(community)
            # Check if there is an event in the community's events array with the created event_id
            self.assertIsNotNone(community, "Community should exist")

            if len(community['events']) is 0:  # in case that the deleted event was the only
                self.assertTrue(True, True)
            else:  # in case it is not the single event we make sure that the deleted events is no longer exists we
                # checking it by id
                self.assertTrue(any(event['event_id'] == event_id for event in community['events']),
                                "The new event should be added to the community's events array")


# To allow running the tests from the command line
if __name__ == '__main__':
    from unittest import main

    main()
