from abc import ABC, abstractmethod
from typing import Any, Dict, List
import os
from pathlib import Path

from sqlalchemy import create_engine, select, update as sql_update, delete as sql_delete, insert as sql_insert

from app.db.json_manager import read_json, update_json
from app.core.logger import app_logger

class DatabaseInterface(ABC):
    @abstractmethod
    def read(self, table: str, filters: dict) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def insert(self, table: str, data: dict) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update(self, table: str, filters: dict, data: dict) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, table: str, filters: dict) -> int:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "db"

class JsonDatabaseAdapter(DatabaseInterface):
    """Wraps json_manager.py to map tables to json files."""
    
    def _get_path(self, table: str) -> str:
        return str(DB_DIR / f"{table}.json")
        
    def _match(self, item: dict, filters: dict) -> bool:
        for k, v in filters.items():
            if item.get(k) != v:
                return False
        return True

    def read(self, table: str, filters: dict) -> List[Dict[str, Any]]:
        items = read_json(self._get_path(table)) or []
        if not filters:
            return items
        return [item for item in items if self._match(item, filters)]

    def insert(self, table: str, data: dict) -> Dict[str, Any]:
        inserted_item = None
        def _insert_fn(items):
            nonlocal inserted_item
            if not items: items = []
            
            if "id" not in data:
                data["id"] = max([int(i.get("id", 0)) for i in items] + [0]) + 1
                
            items.append(data)
            inserted_item = data
            return items
            
        update_json(self._get_path(table), _insert_fn)
        return inserted_item

    def update(self, table: str, filters: dict, data: dict) -> List[Dict[str, Any]]:
        updated_items = []
        def _update_fn(items):
            if not items: return []
            for item in items:
                if self._match(item, filters):
                    item.update(data)
                    updated_items.append(item)
            return items
            
        update_json(self._get_path(table), _update_fn)
        return updated_items

    def delete(self, table: str, filters: dict) -> int:
        deleted_count = 0
        def _delete_fn(items):
            nonlocal deleted_count
            if not items: return []
            new_items = []
            for item in items:
                if self._match(item, filters):
                    deleted_count += 1
                else:
                    new_items.append(item)
            return new_items
            
        update_json(self._get_path(table), _delete_fn)
        return deleted_count

class PostgresDatabaseAdapter(DatabaseInterface):
    """PostgreSQL adapter using SQLAlchemy Core."""
    
    def __init__(self, dsn: str):
        self.engine = create_engine(dsn, pool_pre_ping=True, pool_size=10, max_overflow=20)
        from app.db.models import metadata
        self.metadata = metadata
        
    def _get_table(self, table_name: str):
        if table_name not in self.metadata.tables:
            raise ValueError(f"Table {table_name} not found in metadata")
        return self.metadata.tables[table_name]

    def read(self, table: str, filters: dict) -> List[Dict[str, Any]]:
        table_obj = self._get_table(table)
        stmt = select(table_obj)
        for k, v in filters.items():
            stmt = stmt.where(getattr(table_obj.c, k) == v)
            
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def insert(self, table: str, data: dict) -> Dict[str, Any]:
        table_obj = self._get_table(table)
        stmt = sql_insert(table_obj).values(**data).returning(table_obj)
        
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return dict(result.first()._mapping)

    def update(self, table: str, filters: dict, data: dict) -> List[Dict[str, Any]]:
        table_obj = self._get_table(table)
        stmt = sql_update(table_obj).values(**data).returning(table_obj)
        for k, v in filters.items():
            stmt = stmt.where(getattr(table_obj.c, k) == v)
            
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def delete(self, table: str, filters: dict) -> int:
        table_obj = self._get_table(table)
        stmt = sql_delete(table_obj)
        for k, v in filters.items():
            stmt = stmt.where(getattr(table_obj.c, k) == v)
            
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount

class DualWriteDatabaseAdapter(DatabaseInterface):
    """Zero Downtime Migration Adapter."""
    
    def __init__(self, old_db: DatabaseInterface, new_db: DatabaseInterface):
        self.old_db = old_db
        self.new_db = new_db

    def read(self, table: str, filters: dict) -> List[Dict[str, Any]]:
        return self.old_db.read(table, filters)

    def insert(self, table: str, data: dict) -> Dict[str, Any]:
        result = self.old_db.insert(table, data)
        try:
            if "id" in result:
                data["id"] = result["id"]
            self.new_db.insert(table, data)
        except Exception as e:
            app_logger.error(f"Dual write insertion failed for {table}: {e}")
        return result

    def update(self, table: str, filters: dict, data: dict) -> List[Dict[str, Any]]:
        result = self.old_db.update(table, filters, data)
        try:
            self.new_db.update(table, filters, data)
        except Exception as e:
            app_logger.error(f"Dual write update failed for {table}: {e}")
        return result

    def delete(self, table: str, filters: dict) -> int:
        result = self.old_db.delete(table, filters)
        try:
            self.new_db.delete(table, filters)
        except Exception as e:
            app_logger.error(f"Dual write delete failed for {table}: {e}")
        return result
