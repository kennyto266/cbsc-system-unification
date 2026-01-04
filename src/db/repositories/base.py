"""
Base Repository

Abstract base class for all repositories with common CRUD operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Type

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from ..models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
logger = logging.getLogger(__name__)


class BaseRepository(ABC, Generic[ModelType]):
    """Base repository interface with common CRUD operations"""

    def __init__(self, session: Session, model: Type[ModelType]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model
        self.logger = logger

    def get(self, id: str) -> Optional[ModelType]:
        """
        Get single record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None
        """
        return self.session.query(self.model).filter(
            self.model.id == id
        ).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Filter conditions as dict
            order_by: Field to order by
            order_desc: Order direction (True for descending)

        Returns:
            List of model instances
        """
        query = self.session.query(self.model)

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            query = query.order_by(desc(order_field) if order_desc else asc(order_field))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create new record.

        Args:
            obj_in: Dictionary with field values

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        self.logger.debug(f"Created {self.model.__name__}: {db_obj.id}")
        return db_obj

    def create_many(self, objects_in: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            objects_in: List of dictionaries with field values

        Returns:
            List of created model instances
        """
        db_objects = [self.model(**obj_in) for obj_in in objects_in]
        self.session.add_all(db_objects)
        self.session.commit()
        for obj in db_objects:
            self.session.refresh(obj)
        self.logger.debug(f"Created {len(db_objects)} {self.model.__name__} records")
        return db_objects

    def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update record by ID.

        Args:
            id: Record ID
            obj_in: Dictionary with field values to update

        Returns:
            Updated model instance or None
        """
        db_obj = self.get(id)
        if db_obj:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            self.session.commit()
            self.session.refresh(db_obj)
            self.logger.debug(f"Updated {self.model.__name__}: {id}")
        return db_obj

    def delete(self, id: str) -> bool:
        """
        Delete record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if db_obj:
            self.session.delete(db_obj)
            self.session.commit()
            self.logger.debug(f"Deleted {self.model.__name__}: {id}")
            return True
        return False

    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records.

        Args:
            filters: Filter conditions as dict

        Returns:
            Number of records
        """
        query = self.session.query(func.count(self.model.id))
        if filters:
            query = self._apply_filters(query, filters)
        return query.scalar()

    def exists(self, id: str) -> bool:
        """
        Check if record exists.

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        return self.session.query(
            self.session.query(self.model).filter(self.model.id == id).exists()
        ).scalar()

    def bulk_delete(self, ids: List[str]) -> int:
        """
        Delete multiple records by IDs.

        Args:
            ids: List of record IDs

        Returns:
            Number of deleted records
        """
        count = self.session.query(self.model).filter(
            self.model.id.in_(ids)
        ).delete(synchronize_session=False)
        self.session.commit()
        self.logger.debug(f"Deleted {count} {self.model.__name__} records")
        return count

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filter conditions to query.

        Args:
            query: SQLAlchemy query
            filters: Filter conditions as dict

        Returns:
            Query with filters applied
        """
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, (list, tuple)):
                    # Handle IN clause
                    query = query.filter(getattr(self.model, key).in_(value))
                elif isinstance(value, dict):
                    # Handle complex filters (e.g., {"gt": 10, "lt": 100})
                    for op, val in value.items():
                        field = getattr(self.model, key)
                        if op == "gt":
                            query = query.filter(field > val)
                        elif op == "gte":
                            query = query.filter(field >= val)
                        elif op == "lt":
                            query = query.filter(field < val)
                        elif op == "lte":
                            query = query.filter(field <= val)
                        elif op == "ne":
                            query = query.filter(field != val)
                        elif op == "like":
                            query = query.filter(field.like(val))
                        elif op == "ilike":
                            query = query.filter(field.ilike(val))
                else:
                    # Simple equality
                    query = query.filter(getattr(self.model, key) == value)
        return query

    def get_field_values(self, field: str, distinct: bool = True) -> List[Any]:
        """
        Get all unique values for a field.

        Args:
            field: Field name
            distinct: Return distinct values

        Returns:
            List of field values
        """
        if not hasattr(self.model, field):
            raise ValueError(f"Field '{field}' not found in model")

        query = self.session.query(getattr(self.model, field))
        if distinct:
            query = query.distinct()
        return [r[0] for r in query.all()]

    def refresh(self, db_obj: ModelType) -> ModelType:
        """
        Refresh model instance from database.

        Args:
            db_obj: Model instance to refresh

        Returns:
            Refreshed model instance
        """
        self.session.refresh(db_obj)
        return db_obj

    def flush(self):
        """Flush pending changes to database"""
        self.session.flush()

    def commit(self):
        """Commit transaction"""
        self.session.commit()

    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()

    def __repr__(self):
        return f"<{self.__class__.__name__}(model={self.model.__name__})>"
