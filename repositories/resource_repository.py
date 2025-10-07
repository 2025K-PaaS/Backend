# repositories/resource_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.resource import Resource

class ResourceRepository:
    def create(self, db: Session, *, user_id: int, **kwargs) -> Resource:
        obj = Resource(user_id=user_id, **kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def list_by_user(self, db: Session, user_id: int):
        stmt = select(Resource).where(Resource.user_id == user_id)
        return db.execute(stmt).scalars().all()

    def get(self, db: Session, resource_id: int) -> Resource | None:
        return db.get(Resource, resource_id)
