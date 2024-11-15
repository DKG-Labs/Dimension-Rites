import csv
import time
import re

# Function to read rail_id from the CSV file
def read_rail_id():
    while True:
        try:
            with open("D:/railid/railid.csv", mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    rail_id = row[0]
                    if rail_id and len(rail_id) == 11:
                        return rail_id
        except Exception as e:
            time.sleep(1)
 
def parse_rail_id_info(rail_id):
    # Extract shift_grade as the character after the date
    shift_grade_match = re.search(r"U\d{6}([A-Z])\d{3}", rail_id)
    shift_grade = shift_grade_match.group(1) if shift_grade_match else None
    return shift_grade