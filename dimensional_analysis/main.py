import cv2
import os
import threading
import sys
import time
from .image_processing import mask_image, mse
from .rail_id_processing import read_rail_id, parse_rail_id_info, update_dd_inference
from .db_operations import collection, insert_inspection, connect_db
from .clusterDistance import find_largest_cluster

def process_camera_folder(connection, rail_id, camera_id, good_image_paths, image_paths, distance):
    reference_img_path = good_image_paths[0]
    reference_img_gray = cv2.cvtColor(cv2.imread(reference_img_path), cv2.COLOR_BGR2GRAY)
 
    shift = parse_rail_id_info(rail_id)
    defect_type = None
   
    # Compare the reference image with all bad images
    for bad_img_path,dis in zip(image_paths,distance):
        try:
            bad_img = cv2.imread(bad_img_path)
            if bad_img is None:
                raise ValueError(f"Failed to read image at {bad_img_path}")
            bad_img_gray = cv2.cvtColor(bad_img, cv2.COLOR_BGR2GRAY)
        except Exception as e:
                print(f"Error processing image {bad_img_path}: {e}")
                continue
        
        _, mask1 = mask_image(reference_img_path)
        _, mask2 = mask_image(bad_img_path)
        edge_diff, _ = mse(mask1, mask2)
        image_diff, diff = mse(reference_img_gray, bad_img_gray)
        actual_status=''

        PPI = 9268
        resolution = 1 / (PPI / 25.4)  # mm/pixel

        # Calculate total distance using the diff image
        dimension_deviation = find_largest_cluster(diff, resolution)
 
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

        defect_type = ''
        if camera_id == '40522378':
            defect_type = ["ASY (+)", "ASY (-)", "CP (+)", "CP (-)"]
        elif camera_id == '40525413':
            defect_type = ["OHT", "UHT", "TF (+)", "TF (-)", "TNW", "TKW"]
        elif camera_id == '40522337':
            defect_type = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"]
        elif camera_id == '40522346':
            defect_type = ["NF", "WF", "FBC", "FBCx"]
        elif camera_id == '40522366':
            defect_type = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"]
        else: 
            defect_type = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW"]

        insert_inspection(connection, rail_id, camera_id, reference_img_path, bad_img_path, edge_diff, 0, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, 'operator_id', 'duty_id', shift, defect_type, 1, dis)
 
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
            update_thread = threading.Thread(target=update_dd_inference, args=(rail_id, filtered_image_paths))
            update_thread.start()
 
def main_job():
    db_connection = connect_db()
    if not db_connection:
        print("Database connection failed. Exiting.")
        sys.exit()

    rail_ids = []
    previous_rail_id = None
    pending_rail_ids = list(collection.distinct("rail_id", {"DD_inference":False}))
    good_rail_data = list(collection.find({"rail_id": "U191124C090"}, {"file_path": 1, "camera": 1}))

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
            print("Rail_id : ",rail_id)
            process_rail_data(rail_data, good_rail_data, rail_id, db_connection)

        else:
            if pending_rail_ids:
                for rail_id in pending_rail_ids:
                    rail_data = list(collection.find({"rail_id": rail_id, "DD_inference": False}, {"file_path": 1, "distance": 1, "camera":1}))
                    if rail_data:
                        print("Rail_id : ",rail_id)
                        process_rail_data(rail_data, good_rail_data, rail_id, db_connection)
                        pending_rail_ids.pop(0)
                        break
            else:
                time.sleep(60)

if __name__ == "__main__":
    main_job()