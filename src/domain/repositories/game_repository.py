"""
Game Repository Interface

Abstract interface for game persistence operations.
"""

from abc import abstractmethod
from typing import List, Optional

from ..base import Repository
from ..entities.game import Game


class GameRepository(Repository[Game, str]):
    """
    Repository interface for Game aggregate.
    
    Provides persistence operations for games including
    saving, loading, and querying game data.
    """
    
    @abstractmethod
    async def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find game by ID."""
        pass
    
    @abstractmethod
    async def save(self, game: Game) -> None:
        """Save game to repository."""
        pass
    
    @abstractmethod
    async def delete(self, game: Game) -> None:
        """Delete game from repository."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Game]:
        """Find all games."""
        pass
    
    @abstractmethod
    async def find_active_games(self) -> List[Game]:
        """Find all active (non-completed) games."""
        pass
    
    @abstractmethod
    async def find_games_by_player(self, player_id: str) -> List[Game]:
        """Find games involving specific player."""
        pass
    
    @abstractmethod
    async def find_recent_games(self, limit: int = 10) -> List[Game]:
        """Find most recently created games."""
        pass
    
    @abstractmethod
    async def count_active_games(self) -> int:
        """Count number of active games."""
        pass