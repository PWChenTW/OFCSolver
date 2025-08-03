"""Game state query handlers."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.application.queries import (
    Query, QueryResult, QueryHandler, 
    PaginationParams, PaginatedResult,
    DateRangeFilter
)
from src.domain.entities.game import Game, GameStatus
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position as PlayerPosition
from src.domain.repositories.game_repository import GameRepository
from src.domain.repositories.player_repository import PlayerRepository


# Query Types
@dataclass
class GetGameByIdQuery(Query):
    """Query to get a game by its ID."""
    game_id: UUID
    include_full_history: bool = False


@dataclass
class GetActiveGamesQuery(Query):
    """Query to get all active games."""
    player_id: Optional[UUID] = None
    pagination: Optional[PaginationParams] = None


@dataclass
class GetGameHistoryQuery(Query):
    """Query to get game history with filters."""
    player_id: Optional[UUID] = None
    status_filter: Optional[List[GameStatus]] = None
    date_filter: Optional[DateRangeFilter] = None
    pagination: Optional[PaginationParams] = None


@dataclass
class GetPlayerGamesQuery(Query):
    """Query to get all games for a specific player."""
    player_id: UUID
    include_active_only: bool = False
    pagination: Optional[PaginationParams] = None


@dataclass
class GetGameStatsQuery(Query):
    """Query to get game statistics."""
    player_id: Optional[UUID] = None
    date_filter: Optional[DateRangeFilter] = None


# Query Results
@dataclass
class GameDTO:
    """Data transfer object for game information."""
    id: UUID
    status: GameStatus
    current_player_id: Optional[UUID]
    players: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    current_round: int
    fantasy_land_players: List[UUID]
    
    @classmethod
    def from_domain(cls, game: Game) -> 'GameDTO':
        """Create DTO from domain entity."""
        return cls(
            id=game.id,
            status=game.status,
            current_player_id=game.current_player_id,
            players=[{
                'id': str(p.id),
                'position': p.position.value,
                'score': p.score,
                'is_active': p.is_active
            } for p in game.players],
            created_at=game.created_at,
            updated_at=game.updated_at,
            completed_at=game.completed_at,
            current_round=game.current_round,
            fantasy_land_players=[p.id for p in game.players if p.in_fantasy_land]
        )


@dataclass
class GameDetailDTO(GameDTO):
    """Detailed game information including full history."""
    rounds: List[Dict[str, Any]]
    positions: Dict[str, Dict[str, Any]]
    
    @classmethod
    def from_domain(cls, game: Game, include_history: bool = False) -> 'GameDetailDTO':
        """Create detailed DTO from domain entity."""
        base_dto = GameDTO.from_domain(game)
        
        positions = {}
        for player in game.players:
            positions[str(player.id)] = {
                'front': [str(card) for card in player.position.front_hand.cards],
                'middle': [str(card) for card in player.position.middle_hand.cards],
                'back': [str(card) for card in player.position.back_hand.cards],
                'played_cards': len(player.position.played_cards),
                'remaining_cards': len(player.position.remaining_cards)
            }
        
        rounds = []
        if include_history:
            # Include full round history if requested
            for round_obj in game.rounds:
                rounds.append({
                    'round_number': round_obj.round_number,
                    'completed': round_obj.is_completed,
                    'fantasy_land_players': [str(p) for p in round_obj.fantasy_land_players]
                })
        
        return cls(
            **base_dto.__dict__,
            rounds=rounds,
            positions=positions
        )


@dataclass
class GetGameByIdResult(QueryResult):
    """Result for getting a game by ID."""
    game: Optional[GameDetailDTO]
    

@dataclass
class GetActiveGamesResult(QueryResult):
    """Result for getting active games."""
    games: PaginatedResult[GameDTO]


@dataclass
class GetGameHistoryResult(QueryResult):
    """Result for getting game history."""
    games: PaginatedResult[GameDTO]


@dataclass
class GetPlayerGamesResult(QueryResult):
    """Result for getting player games."""
    games: PaginatedResult[GameDTO]
    player_stats: Dict[str, Any]


@dataclass
class GameStatsDTO:
    """Game statistics DTO."""
    total_games: int
    completed_games: int
    active_games: int
    win_rate: float
    average_score: float
    fantasy_land_rate: float
    games_by_status: Dict[str, int]
    recent_performance: List[Dict[str, Any]]


@dataclass
class GetGameStatsResult(QueryResult):
    """Result for game statistics query."""
    stats: GameStatsDTO


# Query Handlers
class GetGameByIdHandler(QueryHandler[GetGameByIdQuery, GetGameByIdResult]):
    """Handler for getting a game by ID."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def handle(self, query: GetGameByIdQuery) -> GetGameByIdResult:
        """Handle the query."""
        game = await self.game_repository.get_by_id(query.game_id)
        
        if not game:
            return GetGameByIdResult(game=None)
        
        game_dto = GameDetailDTO.from_domain(game, query.include_full_history)
        return GetGameByIdResult(game=game_dto)


class GetActiveGamesHandler(QueryHandler[GetActiveGamesQuery, GetActiveGamesResult]):
    """Handler for getting active games."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def handle(self, query: GetActiveGamesQuery) -> GetActiveGamesResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Get active games from repository
        if query.player_id:
            games = await self.game_repository.find_active_by_player(
                query.player_id,
                offset=pagination.offset,
                limit=pagination.limit
            )
            total = await self.game_repository.count_active_by_player(query.player_id)
        else:
            games = await self.game_repository.find_active(
                offset=pagination.offset,
                limit=pagination.limit
            )
            total = await self.game_repository.count_active()
        
        # Convert to DTOs
        game_dtos = [GameDTO.from_domain(game) for game in games]
        
        paginated_result = PaginatedResult(
            items=game_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return GetActiveGamesResult(games=paginated_result)


class GetGameHistoryHandler(QueryHandler[GetGameHistoryQuery, GetGameHistoryResult]):
    """Handler for getting game history."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def handle(self, query: GetGameHistoryQuery) -> GetGameHistoryResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Build filter criteria
        criteria = {}
        if query.player_id:
            criteria['player_id'] = query.player_id
        if query.status_filter:
            criteria['status_in'] = query.status_filter
        if query.date_filter:
            start_date, end_date = query.date_filter.to_datetime_range()
            if start_date:
                criteria['created_after'] = start_date
            if end_date:
                criteria['created_before'] = end_date
        
        # Get games from repository
        games = await self.game_repository.find_by_criteria(
            criteria,
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=pagination.sort_by or 'created_at',
            sort_order=pagination.sort_order
        )
        
        total = await self.game_repository.count_by_criteria(criteria)
        
        # Convert to DTOs
        game_dtos = [GameDTO.from_domain(game) for game in games]
        
        paginated_result = PaginatedResult(
            items=game_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return GetGameHistoryResult(games=paginated_result)


class GetPlayerGamesHandler(QueryHandler[GetPlayerGamesQuery, GetPlayerGamesResult]):
    """Handler for getting player games."""
    
    def __init__(self, game_repository: GameRepository, player_repository: PlayerRepository):
        self.game_repository = game_repository
        self.player_repository = player_repository
    
    async def handle(self, query: GetPlayerGamesQuery) -> GetPlayerGamesResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Get games for player
        if query.include_active_only:
            games = await self.game_repository.find_active_by_player(
                query.player_id,
                offset=pagination.offset,
                limit=pagination.limit
            )
            total = await self.game_repository.count_active_by_player(query.player_id)
        else:
            games = await self.game_repository.find_by_player(
                query.player_id,
                offset=pagination.offset,
                limit=pagination.limit
            )
            total = await self.game_repository.count_by_player(query.player_id)
        
        # Get player stats
        player_stats = await self._calculate_player_stats(query.player_id)
        
        # Convert to DTOs
        game_dtos = [GameDTO.from_domain(game) for game in games]
        
        paginated_result = PaginatedResult(
            items=game_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return GetPlayerGamesResult(games=paginated_result, player_stats=player_stats)
    
    async def _calculate_player_stats(self, player_id: UUID) -> Dict[str, Any]:
        """Calculate player statistics."""
        # This would be implemented with actual repository methods
        return {
            'total_games': 0,
            'wins': 0,
            'win_rate': 0.0,
            'average_score': 0.0,
            'fantasy_land_count': 0
        }


class GetGameStatsHandler(QueryHandler[GetGameStatsQuery, GetGameStatsResult]):
    """Handler for getting game statistics."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def handle(self, query: GetGameStatsQuery) -> GetGameStatsResult:
        """Handle the query."""
        # Build criteria for filtering
        criteria = {}
        if query.player_id:
            criteria['player_id'] = query.player_id
        if query.date_filter:
            start_date, end_date = query.date_filter.to_datetime_range()
            if start_date:
                criteria['created_after'] = start_date
            if end_date:
                criteria['created_before'] = end_date
        
        # Get statistics from repository
        stats = await self._calculate_game_stats(criteria)
        
        return GetGameStatsResult(stats=stats)
    
    async def _calculate_game_stats(self, criteria: Dict[str, Any]) -> GameStatsDTO:
        """Calculate game statistics based on criteria."""
        # This would be implemented with actual repository methods
        # For now, return placeholder data
        return GameStatsDTO(
            total_games=0,
            completed_games=0,
            active_games=0,
            win_rate=0.0,
            average_score=0.0,
            fantasy_land_rate=0.0,
            games_by_status={},
            recent_performance=[]
        )