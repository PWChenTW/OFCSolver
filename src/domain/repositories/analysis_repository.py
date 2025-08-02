"""Analysis Repository - Placeholder"""

from abc import abstractmethod
from typing import List, Optional

from ..base import Repository
from ..entities.strategy import AnalysisSession


class AnalysisRepository(Repository[AnalysisSession, str]):
    """Analysis repository placeholder."""

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[AnalysisSession]:
        pass

    @abstractmethod
    async def save(self, session: AnalysisSession) -> None:
        pass

    @abstractmethod
    async def delete(self, session: AnalysisSession) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[AnalysisSession]:
        pass
