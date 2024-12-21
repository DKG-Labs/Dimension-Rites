import pymongo
import mysql.connector
import json

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
    
# Insert Inspection Record
def insert_inspection(connection, rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, no_of_dimension_variation, distance_from_head):
    if isinstance(defect_type, list):
        defect_type = json.dumps(defect_type)

    cursor = connection.cursor()
    insert_query = """
    INSERT INTO Dimensional_Inspection (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, no_of_dimension_variation, distance_from_head)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, no_of_dimension_variation, distance_from_head))
    connection.commit()