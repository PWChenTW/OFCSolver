"""Training Repository - Placeholder"""

from abc import abstractmethod
from typing import List, Optional

from ..base import Repository
from ..entities.training import TrainingSession


class TrainingRepository(Repository[TrainingSession, str]):
    """Training repository placeholder."""

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[TrainingSession]:
        pass

    @abstractmethod
    async def save(self, session: TrainingSession) -> None:
        pass

    @abstractmethod
    async def delete(self, session: TrainingSession) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[TrainingSession]:
        pass
