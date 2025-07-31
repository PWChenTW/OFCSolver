"""Calculation Repository - Placeholder"""
from abc import abstractmethod
from typing import List, Optional
from ..base import Repository
from ..entities.strategy import Calculation

class CalculationRepository(Repository[Calculation, str]):
    """Calculation repository placeholder."""
    @abstractmethod
    async def find_by_id(self, calc_id: str) -> Optional[Calculation]: pass
    @abstractmethod
    async def save(self, calc: Calculation) -> None: pass
    @abstractmethod
    async def delete(self, calc: Calculation) -> None: pass
    @abstractmethod
    async def find_all(self) -> List[Calculation]: pass