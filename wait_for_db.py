# wait_for_db.py
import time
import pymysql
from pymysql.err import OperationalError

print("⏳ Esperando a que MySQL esté listo...")

while True:
    try:
        connection = pymysql.connect(
            host="db",
            user="root",
            password="1234",
            database="juego_db"
        )
        print("✅ Conexión establecida con MySQL")
        connection.close()
        break
    except OperationalError:
        print("❌ MySQL no está listo aún, reintentando en 3s...")
        time.sleep(3)
