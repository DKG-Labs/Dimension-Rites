import threading
import json
import logging
import cv2
from db.mongodb_connector import get_mongodb_collection
from config import DIFF_THRESHOLD
from utils.image_processing import mask_image, mse_diff, find_largest_cluster
from utils.rail_id_utils import parse_shift_grade
from db.mysql_connector import connect_mysql

collection = get_mongodb_collection()

# Map camera IDs → defect lists
DEFECT_MAP = {
    '40522378': ["ASY (+)", "ASY (-)", "CP (+)", "CP (-)"],
    '40525413': ["OHT", "UHT", "TF (+)", "TF (-)", "TNW", "TKW"],
    '40522337': ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"],
    '40522346': ["NF", "WF", "FBC", "FBCx"],
    '40522366': ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"]
}
DEFAULT_DEFECT = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW"]

INSERT_SQL = """
INSERT INTO Dimensional_Inspection (
    rail_id, camera_id, camera_name, base_image_path, inspected_image_path,
    edge_diff, chop_diff, image_diff, dimension_deviation,
    actual_status, result_status, confusion_classifier,
    operator_id, duty_id, shift, defect_type,
    no_of_dimension_variation, distance_from_head
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def insert_inspection(conn, record):
    # Serialize defect list
    if isinstance(record[14], list):
        record = list(record)
        record[14] = json.dumps(record[14])
    cur = conn.cursor()
    cur.execute(INSERT_SQL, record)
    conn.commit()


def mark_done(rail_id, paths):
    try:
        collection.update_many(
            {"rail_id": rail_id, "file_path": {"$in": paths}},
            {"$set": {"DD_inference": True}}
        )
    except Exception as e:
        logging.error(f"MongoDB update failed: {e}")


def process_camera(conn, rail_id, cam_id, cam_name, paths, dists):
    base = paths[0]
    base_gray = cv2.cvtColor(cv2.imread(base), cv2.COLOR_BGR2GRAY)
    shift = parse_shift_grade(rail_id)
    for p, dist in zip(paths, dists):
        if p == base: continue
        try:
            img_gray = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
            mask1 = mask_image(base)
            mask2 = mask_image(p)
            edge_diff, _ = mse_diff(mask1, mask2)
            img_diff, diff_mat = mse_diff(base_gray, img_gray)
            deviation = find_largest_cluster(diff_mat)

            status = 'fail' if img_diff>DIFF_THRESHOLD else 'pass'
            confusion = 'FP' if status=='pass' else 'TN'
            defects = DEFECT_MAP.get(cam_id, DEFAULT_DEFECT)

            rec = (
                rail_id, cam_id, cam_name, base, p,
                edge_diff, 0, img_diff, deviation,
                '', status, confusion,
                'operator_id', 'duty_id', shift,
                defects, 1, dist
            )
            insert_inspection(conn, rec)
        except Exception as exc:
            logging.error(f"Error {cam_id}:{p} → {exc}")


def process_rail_data(records, rail_id, cam_name, conn):
    cameras = ['40522337','40522346','40522366','40522375','40522378','40525413']
    for cam in cameras:
        group = [r for r in records if r['camera']==cam]
        if not group: continue
        paths = [r['file_path'] for r in group]
        dists = [r['distance'] for r in group]
        process_camera(conn, rail_id, cam, cam_name, paths, dists)
        threading.Thread(target=mark_done, args=(rail_id, paths), daemon=True).start()