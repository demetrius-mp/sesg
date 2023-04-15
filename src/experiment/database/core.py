import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("Must set DATABASE_URL environment variable.")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    if DATABASE_URL is None:
        raise RuntimeError("Must set DATABASE_URL environment variable.")

    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(DATABASE_URL)
Session = sessionmaker(engine)


def create_tables():
    from .m import Base

    Base.metadata.create_all(engine)
