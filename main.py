import sys
import time
import logging

from db.mysql_connector import connect_mysql
from db.mongodb_connector import get_mongodb_collection
from utils.logging_config import setup_logging
from utils.rail_id_utils import read_rail_id
from services.inspection_service import process_rail_data


def main():
    setup_logging()
    conn = connect_mysql()
    if not conn:
        logging.error("Cannot connect to MySQL; exiting.")
        sys.exit(1)

    collection = get_mongodb_collection()
    rail_queue = []
    prev_id = None
    pending = collection.distinct("rail_id", {"DD_inference": False})

    while True:
        current = read_rail_id()
        if current and current not in rail_queue:
            rail_queue.append(current)

        if prev_id and prev_id != current:
            rid = prev_id
        elif len(rail_queue) > 2:
            rid = rail_queue.pop(0)
        else:
            rid = current

        prev_id = current
        if not rid:
            time.sleep(1)
            continue

        records = list(collection.find(
            {"rail_id": rid, "DD_inference": False},
            {"file_path":1, "distance":1, "camera":1}
        ))

        if records:
            logging.info(f"Processing {rid}")
            process_rail_data(records, rid, conn)
        elif pending:
            for rid in pending:
                recs = list(collection.find(
                    {"rail_id": rid, "DD_inference": False},
                    {"file_path":1, "distance":1, "camera":1}
                ))
                if recs:
                    logging.info(f"Processing pending {rid}")
                    process_rail_data(recs, rid, conn)
                    pending.remove(rid)
                    break
        else:
            time.sleep(60)


if __name__ == "__main__":
    main()