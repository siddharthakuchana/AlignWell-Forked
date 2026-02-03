from .database import SessionLocal

#dependency for database(necessary for sqlalchemy)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
