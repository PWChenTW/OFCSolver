"""Strategy Repository - Placeholder"""
from abc import abstractmethod
from typing import List, Optional
from ..base import Repository

class StrategyRepository(Repository):
    """Strategy repository placeholder."""
    @abstractmethod
    async def find_by_id(self, strategy_id: str) -> Optional: pass
    @abstractmethod
    async def save(self, strategy) -> None: pass
    @abstractmethod
    async def delete(self, strategy) -> None: pass
    @abstractmethod
    async def find_all(self) -> List: pass