from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from modelos import User, Data, Base

class DBRepository:
    """
    Repository that allows CRUD operations on any register of the system.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy Session.
        """
        self.session = session

    # READ 
    def register_in_db(self, r_id: int, r_type: type) -> bool:
        """
        Check if a register of the given type with the given id exists in the database.

        Returns:
            bool: True if a register of the given type and id exists in the database, False otherwise.
        """
        try:
            existing_register = self.session.query(r_type).filter_by(id=r_id).first()
            # self.session.close()
            return existing_register is not None
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get_register_by_id(self, r_id: int, r_type: type):
        """
        Get the register of the given type with the given id.

        Returns:
            RegistroType: The register object with the given id and type if it exists in the database, None otherwise.
        """
        try:
            register = self.session.query(r_type).filter_by(id=r_id).first()
            # self.session.close()
            return register
        except NoResultFound:
            # self.session.close()
            return None
        except Exception as e:
            self.session.rollback()
            raise e

    def get_all_registers(self, r_type: type):
        """
        Get all registers of the given type.

        Returns:
            list: A list of RegistroType objects of the given type that exist in the database.
        """
        try:
            registers = self.session.query(r_type).all()
            # self.session.close()
            return registers
        except Exception as e:
            self.session.rollback()
            raise e

    def search_registers(self, r_type: type, filter_: dict):
        """
        Search for registers of the given type that match the given filter.
        
        Returns:
            list: A list of RegistroType objects of the given type that match the given filter and exist in the database.
        """
        try:
            registers = self.session.query(r_type).filter_by(**filter_).all()
            # self.session.close()
            return registers
        except Exception as e:
            self.session.rollback()
            raise e
    
    # UPDATE
    def update_register(self, new_r):
        """
        Update a register in the database with the same id and type as the given register object.
        """
        try:
            r_type = type(new_r)
            existing_register = self.session.query(r_type).filter_by(id=new_r.id).first()
            if existing_register:
                self.session.merge(new_r)
                self.session.commit()
            # self.session.close()
        except Exception as e:
            self.session.rollback()
            # self.session.close() - USAR WITH STATEMENT
            raise e
        
    # DELETE
    def delete_register(self, r_id, r_type):
        try:
            register = self.session.query(r_type).filter_by(id=r_id).first()
            if register:
                self.session.delete(register)
                self.session.commit()
            # self.session.close()
        except Exception as e:
            self.session.rollback()
            # self.session.close() - USAR WITH STATEMENT
            raise e
    
    def insert_register(self, register):
        # Check if register already exists
        if not self.register_in_db(register.id,type(register)):
            self.session.add(register)
            self.session.commit()
            # self.session.close() - USAR WITH STATEMENT