from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path)

# --------------------------------------------------
# Database URL (TiDB / MySQL)
# Format:
# mysql+pymysql://user:password@host:port/database
# --------------------------------------------------
DB_URL = (
    f"mysql+pymysql://{os.getenv('USERNAME')}:"
    f"{os.getenv('PASSWORD')}@"
    f"{os.getenv('HOST')}:"
    f"{os.getenv('PORT')}/"
    f"{os.getenv('DATABASE')}"
)

# --------------------------------------------------
# SQLAlchemy Engine (TiDB-safe configuration)
# --------------------------------------------------
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,        # 🔥 REQUIRED for TiDB (auto-reconnect)
    pool_recycle=300,          # 🔥 Prevent idle timeout disconnects
    pool_size=5,               # Safe default
    max_overflow=10,           # Handle bursts
    echo=False,                # Set True only for debugging
    connect_args={
        "ssl": {
            "ca": os.path.join(BASE_DIR, "CERTS", "isrgrootx1.pem")
        }
    }
)

# --------------------------------------------------
# Session factory
# --------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --------------------------------------------------
# Base model
# --------------------------------------------------
Base = declarative_base()
