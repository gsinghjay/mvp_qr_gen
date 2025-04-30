"""
Base repository module providing generic CRUD operations.
"""

import logging
from typing import Generic, List, Optional, Type, TypeVar, Any, Dict

from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import DatabaseError
from ..database import Base, with_retry

# Define a generic type variable bound to the SQLAlchemy Base model
ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with generic CRUD operations for SQLAlchemy models.
    
    Type Parameters:
        ModelType: The SQLAlchemy model type this repository handles
    
    Attributes:
        db: SQLAlchemy database session
        model_class: The SQLAlchemy model class this repository handles
    """

    def __init__(self, db: Session, model_class: Type[ModelType]):
        """
        Initialize the base repository.
        
        Args:
            db: SQLAlchemy database session
            model_class: The SQLAlchemy model class this repository handles
        """
        self.db = db
        self.model_class = model_class

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a model instance by its ID.
        
        Args:
            id: The ID of the model to retrieve
            
        Returns:
            The model instance if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(self.model_class).filter(self.model_class.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving {self.model_class.__name__} with ID {id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving {self.model_class.__name__}: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get a list of model instances with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(self.model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Database error retrieving all {self.model_class.__name__}: {str(e)}")

    def create(self, model_data: Dict[str, Any]) -> ModelType:
        """
        Create a new model instance.
        
        Args:
            model_data: Dictionary of model attributes to create the instance
            
        Returns:
            The created model instance
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            model_instance = self.model_class(**model_data)
            self.db.add(model_instance)
            self.db.commit()
            self.db.refresh(model_instance)
            return model_instance
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Database error creating {self.model_class.__name__}: {str(e)}")

    @with_retry(max_retries=3, retry_delay=0.2)
    def update(self, id: Any, update_data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a model instance by its ID.
        
        Args:
            id: The ID of the model to update
            update_data: Dictionary of model attributes to update
            
        Returns:
            The updated model instance if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Perform update operation
            stmt = (
                update(self.model_class)
                .where(self.model_class.id == id)
                .values(**update_data)
                .execution_options(synchronize_session="fetch")
            )
            self.db.execute(stmt)
            
            # Commit changes
            self.db.commit()
            
            # Return updated instance
            return self.get_by_id(id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating {self.model_class.__name__} with ID {id}: {str(e)}")
            raise DatabaseError(f"Database error updating {self.model_class.__name__}: {str(e)}")

    @with_retry(max_retries=3, retry_delay=0.2)
    def delete(self, id: Any) -> bool:
        """
        Delete a model instance by its ID.
        
        Args:
            id: The ID of the model to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Check if entity exists
            model_instance = self.get_by_id(id)
            if not model_instance:
                return False
            
            # Delete the entity
            self.db.delete(model_instance)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting {self.model_class.__name__} with ID {id}: {str(e)}")
            raise DatabaseError(f"Database error deleting {self.model_class.__name__}: {str(e)}")

    def count_all(self) -> int:
        """
        Count all model instances.
        
        Returns:
            Total count of model instances
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(self.model_class).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting all {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Database error counting all {self.model_class.__name__}: {str(e)}") 