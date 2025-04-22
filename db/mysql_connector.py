import mysql.connector
from config import MYSQL_CONFIG
import logging

def connect_mysql():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"MySQL Connection Error: {err}")
        return None
