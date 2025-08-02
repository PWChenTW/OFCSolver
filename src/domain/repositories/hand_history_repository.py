"""Hand History Repository - Placeholder"""

from abc import abstractmethod
from typing import List, Optional

from ..base import Repository
from ..entities.analytics import HandHistory


class HandHistoryRepository(Repository[HandHistory, str]):
    """Hand history repository placeholder."""

    @abstractmethod
    async def find_by_id(self, history_id: str) -> Optional[HandHistory]:
        pass

    @abstractmethod
    async def save(self, history: HandHistory) -> None:
        pass

    @abstractmethod
    async def delete(self, history: HandHistory) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[HandHistory]:
        pass
