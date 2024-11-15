import pymongo
import mysql.connector

# MongoDB connection setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Rail"]
collection = db["camera"]
 
# Database connection
def connect_db(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None