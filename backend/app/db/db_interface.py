import abc
from typing import Any, Callable

class DBInterface(abc.ABC):
    @abc.abstractmethod
    def read(self, collection_path: str) -> Any:
        pass

    @abc.abstractmethod
    def write(self, collection_path: str, data: Any) -> None:
        pass

    @abc.abstractmethod
    def update(self, collection_path: str, update_fn: Callable[[Any], Any]) -> Any:
        pass

class SQLDBInterface(DBInterface):
    """
    Future implementation for SQL-based persistence.
    DO NOT IMPLEMENT SQL YET. This is an architectural placeholder.
    """
    def read(self, collection_path: str) -> Any:
        raise NotImplementedError("SQL DB not implemented yet")

    def write(self, collection_path: str, data: Any) -> None:
        raise NotImplementedError("SQL DB not implemented yet")

    def update(self, collection_path: str, update_fn: Callable[[Any], Any]) -> Any:
        raise NotImplementedError("SQL DB not implemented yet")
