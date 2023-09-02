from pymongo import MongoClient

class database:

    def __init__(self):
        # Connect to the local MongoDB instance running on the default port 27017
        self.client = MongoClient('mongodb://localhost:27017/UrbanHive')

        # Access a database named 'UrbanHive'
        self.db = self.client['UrbanHive']
