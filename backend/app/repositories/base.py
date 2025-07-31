from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc
from app.core.database import Base
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            raise
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID (alias for get method)."""
        return self.get(id)
    
    def get_or_404(self, id: int) -> ModelType:
        """Get a single record by ID or raise NotFoundError."""
        obj = self.get(id)
        if not obj:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return obj
    
    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a single record by field value."""
        try:
            return self.db.query(self.model).filter(getattr(self.model, field) == value).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by {field}={value}: {e}")
            raise
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get multiple records with optional filtering and pagination."""
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field).in_(value))
                        else:
                            query = query.filter(getattr(self.model, field) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                if order_desc:
                    query = query.order_by(desc(getattr(self.model, order_by)))
                else:
                    query = query.order_by(asc(getattr(self.model, order_by)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} records: {e}")
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field).in_(value))
                        else:
                            query = query.filter(getattr(self.model, field) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} records: {e}")
            raise
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def update(self, id: int, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing record."""
        try:
            db_obj = self.get_or_404(id)
            for field, value in obj_in.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} with id {id}: {e}")
            raise
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        try:
            db_obj = self.get_or_404(id)
            self.db.delete(db_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            raise
    
    def exists(self, id: int) -> bool:
        """Check if a record exists by ID."""
        return self.get(id) is not None
    
    def exists_by_field(self, field: str, value: Any) -> bool:
        """Check if a record exists by field value."""
        return self.get_by_field(field, value) is not None
