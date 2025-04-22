from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

def get_mongodb_collection():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    return collection
