from pymongo import MongoClient


class DataBase:
    """
    A class for managing a connection to a MongoDB database and accessing its data.

    Attributes:
        client (MongoClient): A MongoClient object that represents a connection to the MongoDB instance.
        db (Database): A Database object that represents the specific database accessed within MongoDB.

    Methods:
        __init__: Initializes a new DataBase instance, connecting to a MongoDB database.
    """

    def __init__(self):
        """
        Initializes a new instance of the DataBase class, setting up a connection to the MongoDB database
        running on the local machine via the default port.

        The method sets up a client to interact with the MongoDB instance at the specified URI,
        and selects a specific database named 'UrbanHive' for data operations.

        MongoDB URI is predefined as 'mongodb://localhost:27017/UrbanHive'. This URI indicates that
        MongoDB is expected to be running locally on the default MongoDB port, 27017. The 'UrbanHive'
        part of the URI specifies the database to be accessed.

        Note:
            Ensure MongoDB is running on localhost:27017 before initializing this class. The 'UrbanHive'
            database should also exist or should be creatable by the MongoDB permissions set for the
            localhost connection.

        Raises:
            pymongo.errors.ConnectionFailure: If the MongoClient cannot make a connection to the database.
            pymongo.errors.ConfigurationError: If the URI provided is malformed or the database is not reachable.
        """

        # Connect to the local MongoDB instance running on the default port 27017
        self.client = MongoClient('mongodb://localhost:27017/UrbanHive')

        # Access a database named 'UrbanHive'
        self.db = self.client['UrbanHive']
