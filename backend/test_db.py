import os
import pymysql
from dotenv import load_dotenv

# Load .env file
load_dotenv()

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", 4000))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")
SSL_CA = os.getenv("SSL_CA")

print("🔍 Testing TiDB connection...")
print("Host:", HOST)
print("Database:", DB)

try:
    conn = pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DB,
        port=PORT,
        ssl={"ca": SSL_CA},
        connect_timeout=10
    )

    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]

        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]

    conn.close()

    print("\n✅ Connection SUCCESS")
    print("🔐 TiDB Version:", version)
    print("🗄 Connected Database:", db_name)

except Exception as e:
    print("\n❌ Connection FAILED")
    print(type(e).__name__, ":", e)
