import os
import pymysql
from dotenv import load_dotenv

# --- Robust Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Try loading .env from current dir or parent dir
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", 4000))
USER = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DATABASE")
SSL_CA = os.getenv("SSL_CA")

# Resolve SSL_CA path relative to the script location
if SSL_CA and (not os.path.isabs(SSL_CA)):
    # If it starts with ./ removes it
    clean_path = SSL_CA[2:] if SSL_CA.startswith("./") else SSL_CA
    SSL_CA = os.path.join(BASE_DIR, clean_path)

print("🔍 Testing TiDB connection...")
print("Host:", HOST)
print("Database:", DB)
print("SSL Cert Path:", SSL_CA)

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
