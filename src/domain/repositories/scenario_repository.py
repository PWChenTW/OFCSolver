"""Scenario Repository - Placeholder"""
from abc import abstractmethod
from typing import List, Optional
from ..base import Repository
from ..entities.training import Scenario

class ScenarioRepository(Repository[Scenario, str]):
    """Scenario repository placeholder."""
    @abstractmethod
    async def find_by_id(self, scenario_id: str) -> Optional[Scenario]: pass
    @abstractmethod
    async def save(self, scenario: Scenario) -> None: pass
    @abstractmethod
    async def delete(self, scenario: Scenario) -> None: pass
    @abstractmethod
    async def find_all(self) -> List[Scenario]: pass