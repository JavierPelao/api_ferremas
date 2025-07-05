import pymysql
import pymysql.cursors

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Jav_pelao3266",
        database="ferremas_db",
        cursorclass=pymysql.cursors.DictCursor
    )a