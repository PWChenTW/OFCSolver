"""Position Repository - Placeholder"""
from abc import abstractmethod
from typing import List, Optional
from ..base import Repository
from ..entities.game import Position

class PositionRepository(Repository[Position, str]):
    """Position repository placeholder."""
    @abstractmethod
    async def find_by_id(self, position_id: str) -> Optional[Position]: pass
    @abstractmethod
    async def save(self, position: Position) -> None: pass
    @abstractmethod
    async def delete(self, position: Position) -> None: pass
    @abstractmethod
    async def find_all(self) -> List[Position]: pass