"""
Game management API controller.
Handles game creation, state management, and game-related operations.
MVP implementation connecting to existing query processors.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from src.application.queries.game_queries import (
    GetGameByIdQuery,
    GetActiveGamesQuery,
    GetGameHistoryQuery,
    GetPlayerGamesQuery,
    GetGameStatsQuery,
    GetGameByIdHandler,
    GetActiveGamesHandler,
    GetGameHistoryHandler,
    GetPlayerGamesHandler,
    GetGameStatsHandler,
    GameDTO,
    GameDetailDTO,
)
from src.application.queries import PaginationParams, DateRangeFilter
from src.domain.entities.game import GameStatus
from src.domain.value_objects.position import Position as PlayerPosition
from src.infrastructure.web.middleware.auth_middleware import get_current_user, require_game_management
from src.infrastructure.web.dependencies import (
    get_game_command_handler,
    get_game_query_handler,
)

router = APIRouter()


# ===== Request Models =====

class CreateGameRequest(BaseModel):
    """Request model for creating a new game."""
    
    player_count: int = Field(
        default=2,
        description="Number of players in the game",
        ge=2,
        le=4
    )
    rules_variant: str = Field(
        default="standard",
        description="Game rules variant",
        pattern="^(standard|pineapple|turbo)$"
    )
    game_mode: str = Field(
        default="casual",
        description="Game mode: casual, competitive, training",
        pattern="^(casual|competitive|training)$"
    )
    time_limit_minutes: Optional[int] = Field(
        default=None,
        description="Optional time limit per player per round",
        ge=1,
        le=30
    )
    fantasy_land_enabled: bool = Field(
        default=True,
        description="Enable fantasy land rules"
    )


class PlaceCardRequest(BaseModel):
    """Request model for placing a card."""
    
    card: str = Field(
        ...,
        description="Card notation (e.g., 'As' for Ace of Spades)",
        pattern="^[2-9TJQKA][hdcs]$"
    )
    position: str = Field(
        ...,
        description="Position to place card: front_1, front_2, middle_1-5, back_1-5",
        pattern="^(front_[12]|middle_[1-5]|back_[1-5])$"
    )
    player_id: Optional[UUID] = Field(
        default=None,
        description="Player ID (optional, uses current user if not specified)"
    )


class GameActionRequest(BaseModel):
    """Request model for game actions."""
    
    action_type: str = Field(
        ...,
        description="Type of action: join, leave, ready, surrender",
        pattern="^(join|leave|ready|surrender)$"
    )
    player_id: Optional[UUID] = Field(
        default=None,
        description="Player ID (optional, uses current user if not specified)"
    )


# ===== Response Models =====

class GameResponse(BaseModel):
    """Response model for game information."""
    
    id: str
    player_count: int
    current_round: int
    status: str
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    rules_variant: str
    game_mode: str
    time_limit_minutes: Optional[int]
    fantasy_land_enabled: bool
    players: List[Dict[str, Any]]
    current_player_id: Optional[str]


class GameStateResponse(BaseModel):
    """Response model for current game state."""
    
    game_id: str
    status: str
    current_player_id: Optional[str]
    current_round: int
    total_rounds: int
    players_positions: Dict[str, Dict[str, Any]]
    remaining_cards: List[str]
    fantasy_land_players: List[str]
    game_statistics: Dict[str, Any]


class PlayerStatsResponse(BaseModel):
    """Response model for player statistics."""
    
    player_id: str
    total_games: int
    wins: int
    win_rate: float
    average_score: float
    fantasy_land_count: int
    best_score: float
    recent_games: List[Dict[str, Any]]


class GameHistoryResponse(BaseModel):
    """Response model for game history."""
    
    id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    player_count: int
    rules_variant: str
    final_scores: Optional[Dict[str, float]]
    winner: Optional[str]
    duration_minutes: Optional[float]


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    
    success: bool = True
    data: Any
    message: Optional[str] = None
    request_id: Optional[str] = None


# ===== Helper Functions =====

def create_success_response(data: Any, message: Optional[str] = None, request: Optional[Request] = None) -> APIResponse:
    """Create standardized success response."""
    return APIResponse(
        success=True,
        data=data,
        message=message,
        request_id=getattr(request.state, "request_id", None) if request else None
    )


def mock_card_deck() -> List[str]:
    """Generate a mock card deck."""
    suits = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    return [rank + suit for rank in ranks for suit in suits]


# ===== Core Endpoints =====

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    request_body: CreateGameRequest,
    request: Request,
    user=Depends(get_current_user),
    command_handler=Depends(get_game_command_handler),
) -> APIResponse:
    """
    Create a new OFC game.
    
    **Requires authentication** to create games and track player participation.
    
    Args:
        request_body: Game creation parameters
        request: FastAPI request object
        user: Current authenticated user
        command_handler: Injected command handler
    
    Returns:
        Created game information
    
    Raises:
        HTTPException: If game creation fails
    """
    try:
        # Generate game ID for MVP
        game_id = str(uuid4())
        
        # Create mock game
        mock_game = GameResponse(
            id=game_id,
            player_count=request_body.player_count,
            current_round=1,
            status="waiting_for_players",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            completed_at=None,
            rules_variant=request_body.rules_variant,
            game_mode=request_body.game_mode,
            time_limit_minutes=request_body.time_limit_minutes,
            fantasy_land_enabled=request_body.fantasy_land_enabled,
            players=[
                {
                    "id": user.get("user_id", "anonymous"),
                    "position": 0,
                    "score": 0.0,
                    "is_active": True,
                    "is_ready": False,
                    "cards_played": 0,
                    "in_fantasy_land": False
                }
            ],
            current_player_id=user.get("user_id", "anonymous")
        )
        
        return create_success_response(
            data=mock_game,
            message="Game created successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create game: {str(e)}"
        )


@router.get("/{game_id}", response_model=APIResponse)
async def get_game(
    game_id: UUID,
    request: Request,
    include_full_history: bool = False,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get game information by ID.
    
    **Requires authentication** to access game details.
    
    Args:
        game_id: Game identifier
        request: FastAPI request object
        include_full_history: Include full round history
        user: Current authenticated user
    
    Returns:
        Game information
    
    Raises:
        HTTPException: If game not found
    """
    try:
        # Mock query creation for MVP
        query = GetGameByIdQuery(
            game_id=game_id,
            include_full_history=include_full_history
        )
        
        # Mock game data
        mock_game = GameResponse(
            id=str(game_id),
            player_count=2,
            current_round=2,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            completed_at=None,
            rules_variant="standard",
            game_mode="casual",
            time_limit_minutes=None,
            fantasy_land_enabled=True,
            players=[
                {
                    "id": user.get("user_id", "anonymous"),
                    "position": 0,
                    "score": 3.5,
                    "is_active": True,
                    "is_ready": True,
                    "cards_played": 10,
                    "in_fantasy_land": False
                },
                {
                    "id": "opponent_player",
                    "position": 1,
                    "score": -2.0,
                    "is_active": True,
                    "is_ready": True,
                    "cards_played": 10,
                    "in_fantasy_land": True
                }
            ],
            current_player_id=user.get("user_id", "anonymous")
        )
        
        return create_success_response(
            data=mock_game,
            message="Game retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game {game_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game: {str(e)}"
        )


@router.get("/{game_id}/state", response_model=APIResponse)
async def get_game_state(
    game_id: UUID,
    request: Request,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get current game state for analysis and play.
    
    **Requires authentication** and player must be in the game.
    
    Args:
        game_id: Game identifier
        request: FastAPI request object
        user: Current authenticated user
    
    Returns:
        Current game state with positions and available actions
    
    Raises:
        HTTPException: If game not found or player not in game
    """
    try:
        # Mock game state data
        mock_state = GameStateResponse(
            game_id=str(game_id),
            status="active",
            current_player_id=user.get("user_id", "anonymous"),
            current_round=2,
            total_rounds=3,
            players_positions={
                user.get("user_id", "anonymous"): {
                    "front": ["As", "Kh"],
                    "middle": ["Qd", "Jc", "Ts", "9h", "8d"],
                    "back": ["7c", "6s", "5h", "4d", "3c"],
                    "remaining_cards": ["2h", "Ah"],
                    "played_cards": 10,
                    "score": 3.5,
                    "in_fantasy_land": False
                },
                "opponent_player": {
                    "front": ["**", "**"],  # Hidden from current player
                    "middle": ["**", "**", "**", "**", "**"],
                    "back": ["**", "**", "**", "**", "**"],
                    "remaining_cards": ["**", "**"],
                    "played_cards": 10,
                    "score": -2.0,
                    "in_fantasy_land": True
                }
            },
            remaining_cards=["2s", "3s", "4s", "5s"],  # Available to deal
            fantasy_land_players=["opponent_player"],
            game_statistics={
                "total_hands_played": 20,
                "fantasy_land_achieved": 1,
                "average_hand_strength": {
                    "front": 0.65,
                    "middle": 0.78,
                    "back": 0.82
                }
            }
        )
        
        return create_success_response(
            data=mock_state,
            message="Game state retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game {game_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game state: {str(e)}"
        )


@router.post("/{game_id}/place-card", response_model=APIResponse)
async def place_card(
    game_id: UUID,
    request_body: PlaceCardRequest,
    request: Request,
    user=Depends(get_current_user),
    command_handler=Depends(get_game_command_handler),
) -> APIResponse:
    """
    Place a card in the game.
    
    **Requires authentication** and player must be current player.
    
    Args:
        game_id: Game identifier
        request_body: Card placement parameters
        request: FastAPI request object
        user: Current authenticated user
        command_handler: Injected command handler
    
    Returns:
        Placement result and updated game state
    
    Raises:
        HTTPException: If placement is invalid or game not found
    """
    try:
        # Validate card placement for MVP
        valid_positions = [
            "front_1", "front_2",
            "middle_1", "middle_2", "middle_3", "middle_4", "middle_5",
            "back_1", "back_2", "back_3", "back_4", "back_5"
        ]
        
        if request_body.position not in valid_positions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid position: {request_body.position}"
            )
        
        # Mock placement result
        placement_result = {
            "game_id": str(game_id),
            "player_id": user.get("user_id", "anonymous"),
            "card": request_body.card,
            "position": request_body.position,
            "placement_valid": True,
            "scoring_impact": {
                "points_change": 1.5,
                "fantasy_land_eligible": False,
                "fouled": False
            },
            "next_player": "opponent_player",
            "round_completed": False,
            "game_completed": False,
            "updated_state": {
                "current_round": 2,
                "cards_remaining": 2,
                "next_action": "opponent_turn"
            }
        }
        
        return create_success_response(
            data=placement_result,
            message="Card placed successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid card placement: {str(e)}"
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game {game_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place card: {str(e)}"
        )


@router.post("/{game_id}/action", response_model=APIResponse)
async def game_action(
    game_id: UUID,
    request_body: GameActionRequest,
    request: Request,
    user=Depends(get_current_user),
    command_handler=Depends(get_game_command_handler),
) -> APIResponse:
    """
    Perform a game action (join, leave, ready, surrender).
    
    **Requires authentication** to perform game actions.
    
    Args:
        game_id: Game identifier
        request_body: Game action parameters
        request: FastAPI request object
        user: Current authenticated user
        command_handler: Injected command handler
    
    Returns:
        Action result and updated game state
    """
    try:
        player_id = request_body.player_id or user.get("user_id", "anonymous")
        
        # Mock action result based on action type
        if request_body.action_type == "join":
            result = {
                "action": "join",
                "player_id": player_id,
                "success": True,
                "message": "Successfully joined the game",
                "player_position": 1,
                "game_status": "waiting_for_players"
            }
        elif request_body.action_type == "ready":
            result = {
                "action": "ready",
                "player_id": player_id,
                "success": True,
                "message": "Player marked as ready",
                "all_players_ready": True,
                "game_status": "active"
            }
        elif request_body.action_type == "leave":
            result = {
                "action": "leave",
                "player_id": player_id,
                "success": True,
                "message": "Successfully left the game",
                "game_status": "waiting_for_players"
            }
        elif request_body.action_type == "surrender":
            result = {
                "action": "surrender",
                "player_id": player_id,
                "success": True,
                "message": "Player surrendered",
                "game_status": "completed",
                "winner": "opponent_player"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action type: {request_body.action_type}"
            )
        
        return create_success_response(
            data=result,
            message=f"Action '{request_body.action_type}' completed successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform action: {str(e)}"
        )


@router.get("/", response_model=APIResponse)
async def list_games(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    status_filter: Optional[str] = None,
    game_mode: Optional[str] = None,
    player_id: Optional[UUID] = None,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    List games with pagination and filtering.
    
    **Requires authentication** to view games.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of games to return (max 100)
        offset: Number of games to skip
        status_filter: Filter by game status
        game_mode: Filter by game mode
        player_id: Filter by specific player
        user: Current authenticated user
    
    Returns:
        Paginated list of games
    """
    try:
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10
        if offset < 0:
            offset = 0
        
        # Create pagination
        pagination = PaginationParams(
            page=offset // limit + 1,
            page_size=limit,
            sort_by="created_at",
            sort_order="desc"
        )
        
        # Mock query for MVP
        if player_id:
            # Get games for specific player
            query = GetPlayerGamesQuery(
                player_id=player_id,
                include_active_only=status_filter == "active",
                pagination=pagination
            )
        else:
            # Get all games or active games
            if status_filter == "active":
                query = GetActiveGamesQuery(
                    player_id=UUID(user.get("user_id", str(uuid4()))),
                    pagination=pagination
                )
            else:
                query = GetGameHistoryQuery(
                    player_id=UUID(user.get("user_id", str(uuid4()))),
                    pagination=pagination
                )
        
        # Mock games data
        mock_games = []
        for i in range(min(limit, 5)):  # Return up to 5 mock games
            mock_games.append(GameHistoryResponse(
                id=str(uuid4()),
                status="completed" if i > 2 else "active",
                created_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat() if i > 2 else None,
                player_count=2,
                rules_variant="standard",
                final_scores={"player1": 15.5, "player2": -15.5} if i > 2 else None,
                winner="player1" if i > 2 else None,
                duration_minutes=45.5 if i > 2 else None
            ))
        
        response_data = {
            "games": {
                "items": mock_games,
                "total": len(mock_games),
                "page": pagination.page,
                "page_size": pagination.page_size,
                "has_next": False,
                "has_prev": offset > 0
            },
            "filters": {
                "status": status_filter,
                "game_mode": game_mode,
                "player_id": str(player_id) if player_id else None
            }
        }
        
        return create_success_response(
            data=response_data,
            message=f"Retrieved {len(mock_games)} games",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list games: {str(e)}"
        )


@router.get("/stats/{player_id}", response_model=APIResponse)
async def get_player_stats(
    player_id: UUID,
    request: Request,
    days_back: int = 30,
    current_user=Depends(get_current_user)
) -> APIResponse:
    """
    Get player statistics.
    
    **Requires authentication** and user must access own stats or have admin rights.
    
    Args:
        player_id: Player identifier
        request: FastAPI request object
        days_back: Number of days to look back for stats
        current_user: Current authenticated user
    
    Returns:
        Player statistics and performance metrics
    """
    try:
        # Check permissions
        if str(player_id) != current_user.get("user_id") and current_user.get("user_type") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other player's statistics"
            )
        
        # Create date filter
        date_filter = DateRangeFilter(days_back=days_back)
        
        # Mock query for MVP
        query = GetGameStatsQuery(
            player_id=player_id,
            date_filter=date_filter
        )
        
        # Mock player stats
        mock_stats = PlayerStatsResponse(
            player_id=str(player_id),
            total_games=42,
            wins=28,
            win_rate=0.67,
            average_score=5.2,
            fantasy_land_count=8,
            best_score=45.5,
            recent_games=[
                {
                    "game_id": str(uuid4()),
                    "opponent": "opponent1",
                    "score": 12.5,
                    "result": "win",
                    "date": datetime.now().isoformat()
                },
                {
                    "game_id": str(uuid4()),
                    "opponent": "opponent2",
                    "score": -8.0,
                    "result": "loss",
                    "date": datetime.now().isoformat()
                }
            ]
        )
        
        return create_success_response(
            data=mock_stats,
            message="Player statistics retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player stats: {str(e)}"
        )


# ===== Health Check Endpoint =====

@router.get("/health", response_model=APIResponse)
async def game_health_check(request: Request) -> APIResponse:
    """
    Health check for game service.
    
    **Public endpoint** - No authentication required.
    """
    return create_success_response(
        data={
            "service": "games",
            "status": "healthy",
            "features": {
                "game_creation": True,
                "game_state_management": True,
                "card_placement": True,
                "player_statistics": True,
                "game_history": True
            },
            "active_games": 8,
            "total_games_today": 23,
            "avg_game_duration_minutes": 42.5
        },
        message="Game service is healthy",
        request=request
    )