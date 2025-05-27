import pymysql
import pymysql.cursors

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root123",
        database="proyecto_api",
        cursorclass=pymysql.cursors.DictCursor
    )