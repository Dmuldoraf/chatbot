import mysql.connector
import os
from mysql.connector import Error

def insert_chat_message(session_id, sender, message, is_error=False):
    try:
        # Establish connection
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        cnx = mysql.connector.connect(
            user="gpsshbubsq",
            password=DB_PASSWORD,
            host="7a99ab4865-dbserver.mysql.database.azure.com",
            port=3306,
            database="chat_requests",
            # ssl_ca="path/to/DigiCertGlobalRootCA.crt.pem",  # Replace with actual CA cert path
            # ssl_disabled=False
        )

        cursor = cnx.cursor()

        # Prepare SQL insert
        sql = """
        INSERT INTO chat_messages (session_id, sender, message, is_error)
        VALUES (%s, %s, %s, %s)
        """
        values = (session_id, sender, message, is_error)

        cursor.execute(sql, values)
        cnx.commit()

        print("✅ Message inserted successfully.")
        return True
    except Error as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
