# В отдельном файле init_db.py
from app.database import engine, Base
from app import models

def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()