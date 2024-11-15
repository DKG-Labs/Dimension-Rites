import cv2
import os
import sys
import time
from .db_connection import connect_db
from .image_processing import mask_image, mse
from .rail_id_processing import read_rail_id, parse_rail_id_info
from .db_connection import collection

# Insert Inspection Record    
def insert_inspection(connection, rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO Dimensional_Inspection (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head))
    connection.commit()

def process_camera_folder(connection, rail_id, camera_id, good_image_paths, image_paths):
    reference_img_path = good_image_paths[0]
    reference_img_gray = cv2.cvtColor(cv2.imread(reference_img_path), cv2.COLOR_BGR2GRAY)
 
    shift = parse_rail_id_info(rail_id)
    defect_type = None
 
    # Compare the reference image with other good images
    for other_img_path in good_image_paths:
        if reference_img_path == other_img_path:
            continue  # Skip comparison with itself
        other_img_gray = cv2.cvtColor(cv2.imread(other_img_path), cv2.COLOR_BGR2GRAY)
        _, mask1 = mask_image(reference_img_path)
        _, mask2 = mask_image(other_img_path)
        edge_diff, _ = mse(mask1, mask2)
        image_diff, _ = mse(reference_img_gray, other_img_gray)
        actual_status = os.path.basename(os.path.dirname(os.path.dirname(other_img_path))).split('_')[0]
 
        result_status = ''
        if image_diff > 50:
            result_status = 'fail'
        else:
            result_status = 'pass'
 
        confusion_classifier = ''
        if actual_status == 'good' and result_status == 'pass':
            confusion_classifier = 'TP'
        else:
            confusion_classifier = 'FN'
        good_rail_id = "0000000000"
        insert_inspection(connection, good_rail_id, camera_id, reference_img_path, other_img_path, edge_diff, 0, image_diff, actual_status, result_status, confusion_classifier, 'operator_id', 'duty_id', shift, '', 0)
 
    # Compare the reference image with all bad images
    for bad_img_path in image_paths:
        bad_img_gray = cv2.cvtColor(cv2.imread(bad_img_path), cv2.COLOR_BGR2GRAY)
        _, mask1 = mask_image(reference_img_path)
        _, mask2 = mask_image(bad_img_path)
        edge_diff, _ = mse(mask1, mask2)
        image_diff, _ = mse(reference_img_gray, bad_img_gray)
        actual_status = os.path.basename(os.path.dirname(os.path.dirname(bad_img_path))).split('_')[0]
 
        result_status = ''
        if image_diff > 50:
            result_status = 'fail'
        else:
            result_status = 'pass'
 
        confusion_classifier = ''
        if actual_status == 'bad' and result_status == 'pass':
            confusion_classifier = 'FP'
        else:
            confusion_classifier = 'TN'
 
        insert_inspection(connection, rail_id, camera_id, reference_img_path, bad_img_path, edge_diff, 0, image_diff, actual_status, result_status, confusion_classifier, 'operator_id', 'duty_id', shift, defect_type, 0)
 
    pass
 
def process_rail_data(rail_data, good_rail_data, rail_id, db_connection):
    cameras = ['40522337', '40522346', '40522366', '40522375', '40522378', '40525413']
    for cam in cameras:
        filtered_rail_data = [data for data in rail_data if data["camera"] == cam]
        filtered_good_rail_data = [data for data in good_rail_data if data["camera"] == cam]
        if filtered_rail_data:
            # Extract relevant data for the filtered camera
            filtered_image_paths = [data["file_path"] for data in filtered_rail_data]
            filtered_distances = [data["distance"] for data in filtered_rail_data]
            filtered_good_image_paths = [data["file_path"] for data in filtered_good_rail_data]
            # Process the camera folder with the filtered data
            process_camera_folder(db_connection, rail_id, cam, filtered_good_image_paths, filtered_image_paths, filtered_distances)
 
def main_job():
    db_connection = connect_db()
    if not db_connection:
        print("Database connection failed. Exiting.")
        sys.exit()
 
    rail_ids = []
    previous_rail_id = None
    pending_rail_ids = list(collection.distinct("rail_id", {"DD_inference":False}))    
    good_rail_data = list(collection.find({"rail_id": "00000000"}, {"file_path": 1, "camera": 1}))
 
    while True:
        current_rail_id = read_rail_id()
        if current_rail_id not in rail_ids:
            rail_ids.append(current_rail_id)
 
        if previous_rail_id is not None and previous_rail_id != current_rail_id:
            rail_data = list(collection.find({"rail_id": previous_rail_id, "DD_inference":False},{"file_path": 1, "distance": 1, "camera":1}))
            rail_id = previous_rail_id
        else:
            if len(rail_ids) > 2:
                rail_data = list(collection.find({"rail_id": rail_ids[0], "DD_inference": False}, {"file_path": 1, "distance": 1, "camera":1}))
                rail_id = rail_ids[0]
                rail_ids.pop(0)
            else:
                rail_data = list(collection.find({"rail_id": current_rail_id, "DD_inference": False}, {"file_path": 1, "distance": 1, "camera":1}))
                rail_id = current_rail_id
        previous_rail_id = current_rail_id
 
        if rail_data:
            process_rail_data(rail_data, good_rail_data, rail_id, db_connection)
               
        else:
            if pending_rail_ids:
                for rail_id in pending_rail_ids:
                    rail_data = list(collection.find({"rail_id": rail_id, "DD_inference": False}, {"file_path": 1, "distance": 1, "camera":1}))
                    if rail_data:
                        process_rail_data(rail_data, good_rail_data, rail_id, db_connection)
                        pending_rail_ids.pop(0)
                        break
            else:
                time.sleep(60)

if __name__ == "__main__":
    main_job()