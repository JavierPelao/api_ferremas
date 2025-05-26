import pymysql
import pymysql.cursors

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="ferremas_db",
        cursorclass=pymysql.cursors.DictCursor
    )