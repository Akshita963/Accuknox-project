# socialnetwork/mongo.py

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['socialnetwork_db']
users_collection = db['users']