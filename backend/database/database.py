from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

#loads the current path of the file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#loads the environment variables from the .env file
dotenv_path = os.path.join(BASE_DIR, "..", "..", ".env")
load_dotenv(dotenv_path)

#database url
DB_URL = (
    f"mysql+pymysql://{os.getenv('USERNAME')}:"
    f"{os.getenv('PASSWORD')}@"
    f"{os.getenv('HOST')}:"
    f"{os.getenv('PORT')}/"
    f"{os.getenv('DATABASE')}"
)

#engine for sqlalchemy
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,        # Required for TiDB (auto-reconnect)
    pool_recycle=300,          # Prevent idle timeout disconnects
    pool_size=5,               # Safe default
    max_overflow=10,           # Handle bursts
    echo=False,                # Set True only for debugging
    connect_args={
        "ssl": {
            "ca": os.path.join(BASE_DIR, "..", "CERTS", "isrgrootx1.pem")
        }
    }
)

#creates a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)   

#creates a base model
Base = declarative_base()
