# Change these based at your references

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ritesai',
    'database': 'rites'
}

MONGODB_URI = 'mongodb://localhost:27017/'
MONGODB_DB = 'Rail'
MONGODB_COLLECTION = 'camera'

PPI = 9268  # Pixels per inch
RESOLUTION = 1 / (PPI / 25.4)  # mm/pixel

# Thresholds
DIFF_THRESHOLD = 50  # pixel‐difference threshold for pass/fail