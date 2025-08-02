"""Strategy Repository - Placeholder"""

from abc import abstractmethod
from typing import Any, List, Optional

from ..base import Repository


class StrategyRepository(Repository[Any, str]):
    """Strategy repository placeholder."""

    @abstractmethod
    async def find_by_id(self, strategy_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def save(self, strategy: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, strategy: Any) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[Any]:
        pass
