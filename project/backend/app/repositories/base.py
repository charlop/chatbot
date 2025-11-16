"""
Base repository with generic CRUD operations for all models.
Uses SQLAlchemy async sessions and provides common database operations.
"""

from typing import TypeVar, Generic, Type, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing generic CRUD operations.

    All repository classes should inherit from this base class.
    Supports async operations with SQLAlchemy 2.0.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages

    Example:
        class ContractRepository(BaseRepository[Contract]):
            def __init__(self, session: AsyncSession):
                super().__init__(Contract, session)
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository with model class and database session.

        Args:
            model: The SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create a new entity in the database.

        Args:
            entity: Model instance to create

        Returns:
            Created entity with generated fields populated
        """
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: any) -> ModelType | None:
        """
        Retrieve an entity by its primary key.

        Args:
            entity_id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        return await self.session.get(self.model, entity_id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Retrieve all entities with pagination.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of entities
        """
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, entity: ModelType) -> ModelType:
        """
        Update an existing entity.

        Args:
            entity: Model instance with updated values

        Returns:
            Updated entity
        """
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity_id: any) -> bool:
        """
        Delete an entity by its primary key.

        Args:
            entity_id: Primary key value

        Returns:
            True if entity was deleted, False if not found
        """
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, entity_id: any) -> bool:
        """
        Check if an entity exists by its primary key.

        Args:
            entity_id: Primary key value

        Returns:
            True if entity exists, False otherwise
        """
        entity = await self.get_by_id(entity_id)
        return entity is not None

    async def delete_all(self) -> int:
        """
        Delete all entities of this type.
        Use with caution!

        Returns:
            Number of entities deleted
        """
        stmt = delete(self.model)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
