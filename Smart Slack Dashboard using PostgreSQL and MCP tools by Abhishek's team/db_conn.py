from sqlalchemy import create_engine

def get_connection():
    """
    Returns a SQLAlchemy engine. Pandas can use this directly
    and no ‘only supports SQLAlchemy connectable’ warning appears.
    """
    return create_engine("postgresql+psycopg2://postgres:root@localhost:5432/database")
