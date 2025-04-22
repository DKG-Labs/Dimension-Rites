import csv
import time
import re
import logging


def read_rail_id(csv_path='data/railid.csv'):
    """
    Reads the first valid 11-character rail_id from a CSV, retrying on error.
    """
    try:
        with open(csv_path, 'r') as f:
            for row in csv.reader(f):
                if row and len(row[0]) == 11:
                    return row[0]
    except Exception as e:
        logging.warning(f"Could not read rail_id: {e}")
        time.sleep(1)
    return None


def parse_shift_grade(rail_id):
    match = re.search(r"U\d{6}([A-Z])\d{3}", rail_id)
    return match.group(1) if match else None