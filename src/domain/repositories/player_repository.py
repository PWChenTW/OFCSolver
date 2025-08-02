"""Player Repository - Placeholder"""

from abc import abstractmethod
from typing import List, Optional

from ..base import Repository
from ..entities.game import Player


class PlayerRepository(Repository[Player, str]):
    """Player repository placeholder."""

    @abstractmethod
    async def find_by_id(self, player_id: str) -> Optional[Player]:
        pass

    @abstractmethod
    async def save(self, player: Player) -> None:
        pass

    @abstractmethod
    async def delete(self, player: Player) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[Player]:
        pass
