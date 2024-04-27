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


class TestRESTPosting(TestCase):

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
                "posts": []
            }
            mongo.db.users.insert_one(self.user)
            mongo.db.communities.insert_one(self.community)

    def tearDown(self):
        with self.app.app_context():
            mongo = PyMongo(self.app)
            mongo.db.users.drop()
            mongo.db.communities.drop()
            mongo.db.posting.drop()

    def test_add_post(self):
        post_data = {
            "user_id": "user001",
            "community_area": "TestArea",
            "post_content": {"header": "Event Update", "body": "The event is scheduled for next week."},
            "post_date": "2022-06-01T19:00:00Z"
        }
        response = self.client.post('/posting/add_post', json=post_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Post added successfully', response.get_json()['message'])

        # Retrieve the post from the database to confirm it was added
        with self.app.app_context():
            mongo = PyMongo(self.app)
            post = mongo.db.posting.find_one({"user_id": "user001"})
            self.assertIsNotNone(post, "The post should exist in the database")

    def test_delete_post(self):
        # First, add a post to delete
        post_data = {
            "user_id": "user001",
            "community_area": "TestArea",
            "post_content": {"header": "Important", "body": "Meeting at 10AM"},
            "post_date": "2022-07-01T10:00:00Z"
        }
        add_response = self.client.post('/posting/add_post', json=post_data)
        self.assertEqual(add_response.status_code, 201)
        post_id = add_response.get_json()['post_id']
        print("Added post_id:", post_id)

        # Now delete the post using the API with the retrieved post_id
        delete_response = self.client.delete('/posting/delete_post', json={"post_id": post_id})
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn('Post deleted successfully', delete_response.get_json()['message'])

        # Confirm the post is removed from the database
        with self.app.app_context():
            mongo = PyMongo(self.app)
            post = mongo.db.posting.find_one({"post_id": post_id})
            self.assertIsNone(post, "The post should be deleted from the database")

    def test_add_comment_to_post(self):
        # First, add a post to comment on
        post_data = {
            "user_id": "user001",
            "community_area": "TestArea",
            "post_content": {"header": "Important", "body": "Meeting at 10AM"},
            "post_date": "2022-07-01T10:00:00Z"
        }
        add_response = self.client.post('/posting/add_post', json=post_data)

        post_id = add_response.get_json()['post_id']

        # Add a comment to the post
        comment_data = {
            "post_id": post_id,
            "comment_text": "This is great news!",
            "user_id": "user001",
            "user_name": "John Doe"
        }
        response = self.client.post('/posting/add_comment_to_post', json=comment_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Comment added successfully', response.get_json()['message'])

    def test_delete_comment_from_post(self):
        # First, add a post to comment on
        post_data = {
            "user_id": "user001",
            "community_area": "TestArea",
            "post_content": {"header": "Important", "body": "Meeting at 10AM"},
            "post_date": "2022-07-01T10:00:00Z"
        }
        add_response = self.client.post('/posting/add_post', json=post_data)

        post_id = add_response.get_json()['post_id']

        # Add a comment to the post
        comment_data = {
            "post_id": post_id,
            "comment_text": "This is great news!",
            "user_id": "user001",
            "user_name": "John Doe"
        }
        response = self.client.post('/posting/add_comment_to_post', json=comment_data)
        comment_id = response.get_json()['comment_id']
        # Delete the comment from the post
        response = self.client.delete('/posting/delete_comment_from_post',
                                      json={"post_id": post_id, "comment_id": comment_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Comment deleted successfully', response.get_json()['message'])


# To allow running the tests from the command line
if __name__ == '__main__':
    from unittest import main

    main()
