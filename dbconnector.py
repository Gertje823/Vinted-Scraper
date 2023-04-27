from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from modelos import Base


class DatabaseConnection:

    @staticmethod
    def get_engine():
        db_url = 'sqlite:///data.sqlite'  # SQLAlchemy syntax
        return create_engine(db_url)

    @staticmethod
    def initialize_db(engine):
        try:
            # Intentar crear las tablas
            Base.metadata.create_all(engine)
        except:
            # Si ocurre un error de conexión, la base de datos no existe
            # y se debe crear
            raise ValueError("Unable to create")

    @staticmethod
    @contextmanager
    def get_session(engine):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            # Código para configurar y usar la sesión
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()