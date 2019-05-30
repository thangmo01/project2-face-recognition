import mysql.connector

def connect_db(DB):
    conn = mysql.connector.connect(
                host=DB['HOST'],
                user=DB['USER'],
                password=DB['PASSWORD'],
                db=DB['NAME']
            )
            
    return conn