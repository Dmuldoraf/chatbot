import mysql.connector
from mysql.connector import Error

def insert_chat_message(session_id, sender, message, is_error=False, pwd=None):
    try:
        # Establish connection
        # DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        cnx = mysql.connector.connect(
            user="gpsshbubsq",
            password=pwd,
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
        return e

    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

def get_all_chat_requests(pwd=None):
    try:
        # DB_PASSWORD = os.environ.get('DB_PASSWORD', 'default')
        print(f"🔑 Using DB_PASSWORD: {pwd}")  # Debugging line to check password
        cnx = mysql.connector.connect(
            user="gpsshbubsq",
            password=pwd,
            host="7a99ab4865-dbserver.mysql.database.azure.com",
            port=3306,
            database="chat_requests",
        )
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chat_messages")
        results = cursor.fetchall()
        cursor.close()
        return results
    except Error as e:
        print(f"❌ Error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()