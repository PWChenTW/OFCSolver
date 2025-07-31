# OFC Solver System - Technical Design Document

## Executive Summary

This document presents the technical architecture for the Open Face Chinese (OFC) Poker Solver system, following Domain-Driven Design (DDD) principles. The system is designed to handle complex game theory optimal (GTO) calculations while maintaining clean domain boundaries, high performance, and extensibility.

## System Architecture Overview

### Architectural Principles
- **Domain-Driven Design**: Clear separation of business logic from technical concerns
- **Clean Architecture**: Dependency inversion with domain at the center
- **CQRS**: Command Query Responsibility Segregation for optimal read/write operations
- **Event-Driven**: Domain events for loose coupling between bounded contexts
- **Performance-First**: Optimized for computationally intensive solver calculations

### Technology Stack
- **Language**: Python 3.11+
- **Core Framework**: FastAPI (async/await support for concurrent calculations)
- **Database**: PostgreSQL (primary), Redis (caching), ClickHouse (analytics)
- **Message Queue**: RabbitMQ with Celery for async processing
- **Computing**: NumPy, SciPy for mathematical operations
- **Frontend**: React with TypeScript
- **Containerization**: Docker with Kubernetes orchestration

---

## Domain Model Design

### Core Bounded Contexts

#### 1. Game Management Context
**Purpose**: Manages OFC game rules, state, and validation

**Entities:**
- `Game` (Aggregate Root): Represents a complete OFC game session
- `Player`: Individual player within a game
- `Round`: Single round of card placement
- `Position`: Current game state for analysis

**Value Objects:**
- `Card`: Immutable card representation (suit, rank)
- `Hand`: Collection of cards in a specific arrangement
- `HandRanking`: Poker hand strength evaluation
- `GameRules`: OFC-specific rule configurations

**Domain Services:**
- `GameValidator`: Validates game state transitions
- `HandEvaluator`: Calculates poker hand rankings
- `RoyaltyCalculator`: Computes royalty bonuses
- `FantasyLandManager`: Handles fantasy land mechanics

#### 2. Strategy Analysis Context
**Purpose**: Core solver algorithms and strategy calculations

**Entities:**
- `AnalysisSession` (Aggregate Root): Complete analysis workflow
- `StrategyNode`: Node in the game tree
- `Calculation`: Individual solver computation task

**Value Objects:**
- `Strategy`: Optimal play recommendation
- `ExpectedValue`: EV calculation result
- `Probability`: Outcome probability distribution
- `ConfidenceInterval`: Statistical confidence measure

**Domain Services:**
- `StrategyCalculator`: Main GTO solver engine
- `GameTreeBuilder`: Constructs decision trees
- `MonteCarloSimulator`: Probabilistic analysis
- `OptimalPlayFinder`: Identifies best strategies

#### 3. Training Context
**Purpose**: Learning scenarios and practice environments

**Entities:**
- `TrainingSession` (Aggregate Root): User practice session
- `Scenario`: Specific training situation
- `Exercise`: Individual practice problem

**Value Objects:**
- `Difficulty`: Training difficulty level
- `Performance`: User performance metrics
- `Feedback`: Analysis and recommendations

**Domain Services:**
- `ScenarioGenerator`: Creates training positions
- `PerformanceTracker`: Monitors user progress
- `AdaptiveDifficulty`: Adjusts challenge level

#### 4. Analytics Context
**Purpose**: Performance tracking and historical analysis

**Entities:**
- `AnalyticsProfile` (Aggregate Root): User performance profile
- `HandHistory`: Historical game records
- `PerformanceReport`: Analysis summaries

**Value Objects:**
- `Statistic`: Performance metrics
- `Trend`: Performance over time
- `Benchmark`: Comparative measurements

### Domain Events

```python
# Domain Events for inter-context communication
class GameCompletedEvent:
    game_id: GameId
    final_scores: Dict[PlayerId, Score]
    timestamp: datetime

class AnalysisRequestedEvent:
    session_id: SessionId
    position: Position
    analysis_type: AnalysisType

class StrategyCalculatedEvent:
    session_id: SessionId
    optimal_strategy: Strategy
    calculation_time: float

class TrainingScenarioCompletedEvent:
    user_id: UserId
    scenario_id: ScenarioId
    performance: Performance
```

---

## Layered Architecture Design

### 1. Domain Layer
```
src/domain/
├── entities/
│   ├── game/
│   │   ├── game.py
│   │   ├── player.py
│   │   └── position.py
│   ├── strategy/
│   │   ├── analysis_session.py
│   │   └── strategy_node.py
│   └── training/
│       ├── training_session.py
│       └── scenario.py
├── value_objects/
│   ├── card.py
│   ├── hand.py
│   ├── strategy.py
│   └── expected_value.py
├── services/
│   ├── strategy_calculator.py
│   ├── hand_evaluator.py
│   └── game_validator.py
├── repositories/
│   ├── game_repository.py
│   ├── analysis_repository.py
│   └── training_repository.py
└── events/
    ├── game_events.py
    ├── strategy_events.py
    └── training_events.py
```

### 2. Application Layer
```
src/application/
├── commands/
│   ├── game_commands.py
│   ├── analysis_commands.py
│   └── training_commands.py
├── queries/
│   ├── game_queries.py
│   ├── analysis_queries.py
│   └── training_queries.py
├── handlers/
│   ├── command_handlers.py
│   ├── query_handlers.py
│   └── event_handlers.py
├── services/
│   ├── analysis_orchestrator.py
│   ├── training_manager.py
│   └── performance_tracker.py
└── dto/
    ├── analysis_dto.py
    ├── training_dto.py
    └── game_dto.py
```

### 3. Infrastructure Layer
```
src/infrastructure/
├── persistence/
│   ├── postgresql/
│   │   ├── repositories/
│   │   └── migrations/
│   ├── redis/
│   │   ├── cache_service.py
│   │   └── session_store.py
│   └── clickhouse/
│       └── analytics_store.py
├── external/
│   ├── calculation_engine/
│   │   ├── numpy_calculator.py
│   │   └── parallel_processor.py
│   └── messaging/
│       ├── rabbitmq_publisher.py
│       └── celery_tasks.py
├── web/
│   ├── api/
│   │   ├── game_controller.py
│   │   ├── analysis_controller.py
│   │   └── training_controller.py
│   └── middleware/
│       ├── auth_middleware.py
│       └── rate_limiter.py
└── monitoring/
    ├── metrics_collector.py
    └── health_checker.py
```

### 4. Presentation Layer
```
src/presentation/
├── web_ui/
│   ├── components/
│   │   ├── game_board/
│   │   ├── analysis_panel/
│   │   └── training_interface/
│   ├── pages/
│   │   ├── analysis.tsx
│   │   ├── training.tsx
│   │   └── history.tsx
│   └── services/
│       ├── api_client.ts
│       └── websocket_client.ts
└── api/
    ├── rest/
    │   ├── game_endpoints.py
    │   ├── analysis_endpoints.py
    │   └── training_endpoints.py
    └── websocket/
        └── realtime_updates.py
```

---

## Core Domain Model Implementation

### Game Entity (Aggregate Root)

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from .value_objects import Card, Hand, Score, GameRules
from .events import GameCompletedEvent, CardPlacedEvent

@dataclass
class Game:
    """
    Aggregate root for OFC game management.
    Encapsulates all game rules and state transitions.
    """
    id: GameId
    players: List[Player]
    current_round: int
    deck: Deck
    rules: GameRules
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Domain events buffer
    _events: List[DomainEvent] = field(default_factory=list)
    
    def place_card(self, player_id: PlayerId, card: Card, position: CardPosition) -> None:
        """Place a card in player's layout with validation"""
        player = self._find_player(player_id)
        
        # Domain validation
        if not self._can_place_card(player, card, position):
            raise InvalidCardPlacementError(f"Cannot place {card} at {position}")
        
        # Apply placement
        player.place_card(card, position)
        self.deck.remove_card(card)
        
        # Emit domain event
        self._events.append(CardPlacedEvent(
            game_id=self.id,
            player_id=player_id,
            card=card,
            position=position,
            timestamp=datetime.utcnow()
        ))
        
        # Check for game completion
        if self._is_game_complete():
            self._complete_game()
    
    def _complete_game(self) -> None:
        """Complete the game and calculate final scores"""
        self.completed_at = datetime.utcnow()
        final_scores = self._calculate_final_scores()
        
        self._events.append(GameCompletedEvent(
            game_id=self.id,
            final_scores=final_scores,
            timestamp=self.completed_at
        ))
    
    def get_analysis_position(self) -> Position:
        """Create position snapshot for strategy analysis"""
        return Position(
            game_id=self.id,
            players_hands={p.id: p.current_hand for p in self.players},
            remaining_cards=self.deck.remaining_cards(),
            current_player=self._get_current_player().id,
            round_number=self.current_round
        )
```

### Strategy Calculator (Domain Service)

```python
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from .value_objects import Strategy, ExpectedValue, Probability

class StrategyCalculator:
    """
    Core domain service for GTO strategy calculation.
    Implements Monte Carlo and exhaustive analysis approaches.
    """
    
    def __init__(self, 
                 hand_evaluator: HandEvaluator,
                 game_tree_builder: GameTreeBuilder,
                 parallel_executor: ProcessPoolExecutor):
        self._hand_evaluator = hand_evaluator
        self._game_tree_builder = game_tree_builder
        self._executor = parallel_executor
    
    async def calculate_optimal_strategy(self, 
                                       position: Position,
                                       calculation_depth: int = 3) -> Strategy:
        """
        Calculate GTO strategy for given position.
        Uses adaptive approach based on position complexity.
        """
        complexity = self._assess_position_complexity(position)
        
        if complexity.is_end_game():
            return await self._exhaustive_analysis(position)
        elif complexity.is_manageable():
            return await self._monte_carlo_analysis(position, samples=100000)
        else:
            return await self._hybrid_analysis(position, calculation_depth)
    
    async def _exhaustive_analysis(self, position: Position) -> Strategy:
        """Exact calculation for end-game positions"""
        game_tree = self._game_tree_builder.build_complete_tree(position)
        
        # Parallel evaluation of all branches
        futures = []
        for branch in game_tree.get_leaf_branches():
            future = self._executor.submit(self._evaluate_branch, branch)
            futures.append(future)
        
        # Collect results and find optimal path
        branch_values = [f.result() for f in futures]
        optimal_branch = max(branch_values, key=lambda x: x.expected_value)
        
        return Strategy(
            recommended_moves=optimal_branch.move_sequence,
            expected_value=optimal_branch.expected_value,
            confidence=1.0,  # Exact calculation
            calculation_method="exhaustive"
        )
    
    async def _monte_carlo_analysis(self, 
                                  position: Position, 
                                  samples: int) -> Strategy:
        """Probabilistic analysis for complex positions"""
        possible_moves = self._generate_legal_moves(position)
        move_evaluations = []
        
        for move in possible_moves:
            # Run parallel simulations for each move
            simulation_tasks = [
                self._executor.submit(self._simulate_game_outcome, position, move)
                for _ in range(samples // len(possible_moves))
            ]
            
            outcomes = [task.result() for task in simulation_tasks]
            avg_value = np.mean([o.final_score for o in outcomes])
            std_dev = np.std([o.final_score for o in outcomes])
            
            move_evaluations.append(MoveEvaluation(
                move=move,
                expected_value=ExpectedValue(avg_value),
                confidence=self._calculate_confidence(std_dev, len(outcomes))
            ))
        
        optimal_move = max(move_evaluations, key=lambda x: x.expected_value.value)
        
        return Strategy(
            recommended_moves=[optimal_move.move],
            expected_value=optimal_move.expected_value,
            confidence=optimal_move.confidence,
            calculation_method="monte_carlo",
            alternative_moves=[m for m in move_evaluations if m != optimal_move]
        )
```

### Hand Evaluator (Domain Service)

```python
from typing import List, Tuple
from enum import Enum
from .value_objects import Card, Hand, HandRanking

class HandType(Enum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

class HandEvaluator:
    """
    Domain service for poker hand evaluation.
    Optimized for OFC-specific requirements including royalties.
    """
    
    def evaluate_hand(self, cards: List[Card]) -> HandRanking:
        """Evaluate poker hand strength"""
        if len(cards) < 3:
            raise ValueError("Minimum 3 cards required for evaluation")
        
        hand_type = self._determine_hand_type(cards)
        strength_value = self._calculate_hand_strength(cards, hand_type)
        royalty_bonus = self._calculate_royalty_bonus(cards, hand_type)
        
        return HandRanking(
            hand_type=hand_type,
            strength_value=strength_value,
            royalty_bonus=royalty_bonus,
            cards=cards.copy()
        )
    
    def compare_hands(self, hand1: HandRanking, hand2: HandRanking) -> int:
        """Compare two hands (-1: hand1 wins, 0: tie, 1: hand2 wins)"""
        if hand1.hand_type.value != hand2.hand_type.value:
            return hand1.hand_type.value - hand2.hand_type.value
        
        return self._compare_same_type_hands(hand1, hand2)
    
    def validate_ofc_layout(self, 
                           top_hand: List[Card],
                           middle_hand: List[Card], 
                           bottom_hand: List[Card]) -> bool:
        """Validate OFC hand arrangement (bottom > middle > top)"""
        if len(top_hand) != 3 or len(middle_hand) != 5 or len(bottom_hand) != 5:
            return False
        
        top_ranking = self.evaluate_hand(top_hand)
        middle_ranking = self.evaluate_hand(middle_hand)
        bottom_ranking = self.evaluate_hand(bottom_hand)
        
        # Check strength progression
        bottom_beats_middle = self.compare_hands(bottom_ranking, middle_ranking) > 0
        middle_beats_top = self.compare_hands(middle_ranking, top_ranking) > 0
        
        return bottom_beats_middle and middle_beats_top
    
    def _calculate_royalty_bonus(self, cards: List[Card], hand_type: HandType) -> int:
        """Calculate OFC royalty bonuses"""
        row_size = len(cards)
        
        if row_size == 3:  # Top row
            return self._top_row_royalties(cards, hand_type)
        elif row_size == 5:  # Middle/Bottom row
            return self._bottom_middle_royalties(cards, hand_type)
        
        return 0
    
    def _top_row_royalties(self, cards: List[Card], hand_type: HandType) -> int:
        """Calculate top row (3-card) royalty bonuses"""
        if hand_type == HandType.THREE_OF_A_KIND:
            return 10
        elif hand_type == HandType.PAIR:
            pair_rank = self._get_pair_rank(cards)
            if pair_rank >= 6:  # 6s or better
                return pair_rank - 5
        return 0
    
    def _bottom_middle_royalties(self, cards: List[Card], hand_type: HandType) -> int:
        """Calculate middle/bottom row (5-card) royalty bonuses"""
        royalty_table = {
            HandType.STRAIGHT: 2,
            HandType.FLUSH: 4,
            HandType.FULL_HOUSE: 6,
            HandType.FOUR_OF_A_KIND: 10,
            HandType.STRAIGHT_FLUSH: 15,
            HandType.ROYAL_FLUSH: 25
        }
        return royalty_table.get(hand_type, 0)
```

---

## Solver Algorithm Design

### Game Tree Representation

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import threading
from concurrent.futures import ThreadPoolExecutor

@dataclass
class GameNode:
    """Node in the OFC game tree"""
    position: Position
    depth: int
    parent: Optional['GameNode'] = None
    children: List['GameNode'] = field(default_factory=list)
    move_to_reach: Optional[Move] = None
    evaluation: Optional[float] = None
    is_terminal: bool = False
    
    def add_child(self, child: 'GameNode') -> None:
        child.parent = self
        self.children.append(child)
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0 or self.is_terminal

class GameTreeBuilder:
    """
    Builds decision trees for OFC positions.
    Implements pruning strategies for performance.
    """
    
    def __init__(self, max_depth: int = 5, pruning_threshold: float = -10.0):
        self.max_depth = max_depth
        self.pruning_threshold = pruning_threshold
        self._transposition_table: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def build_tree(self, root_position: Position) -> GameNode:
        """Build game tree with alpha-beta pruning"""
        root = GameNode(position=root_position, depth=0)
        self._expand_node(root, float('-inf'), float('inf'))
        return root
    
    def _expand_node(self, node: GameNode, alpha: float, beta: float) -> float:
        """Expand node with alpha-beta pruning"""
        position_hash = self._hash_position(node.position)
        
        # Check transposition table
        with self._lock:
            if position_hash in self._transposition_table:
                return self._transposition_table[position_hash]
        
        # Terminal node evaluation
        if node.depth >= self.max_depth or self._is_terminal_position(node.position):
            evaluation = self._evaluate_position(node.position)
            node.evaluation = evaluation
            node.is_terminal = True
            
            with self._lock:
                self._transposition_table[position_hash] = evaluation
            
            return evaluation
        
        # Generate and evaluate child nodes
        legal_moves = self._generate_legal_moves(node.position)
        best_value = float('-inf')
        
        for move in legal_moves:
            child_position = self._apply_move(node.position, move)
            child_node = GameNode(
                position=child_position,
                depth=node.depth + 1,
                move_to_reach=move
            )
            node.add_child(child_node)
            
            # Recursive evaluation with pruning
            child_value = -self._expand_node(child_node, -beta, -alpha)
            child_node.evaluation = child_value
            
            best_value = max(best_value, child_value)
            alpha = max(alpha, child_value)
            
            # Alpha-beta pruning
            if beta <= alpha:
                break
            
            # Depth pruning for poor positions
            if child_value < self.pruning_threshold:
                break
        
        node.evaluation = best_value
        
        with self._lock:
            self._transposition_table[position_hash] = best_value
        
        return best_value
```

### Parallel Processing Architecture

```python
import asyncio
import concurrent.futures
from typing import List, Callable, Any
from dataclasses import dataclass

@dataclass
class CalculationTask:
    """Individual calculation task for parallel processing"""
    task_id: str
    position: Position
    depth: int
    calculation_type: str
    priority: int = 0

class ParallelCalculationEngine:
    """
    Manages parallel calculation of OFC strategies.
    Optimizes CPU usage across multiple cores.
    """
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or (os.cpu_count() - 1)
        self.process_executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        )
        self.thread_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers * 2
        )
    
    async def calculate_batch_strategies(self, 
                                       tasks: List[CalculationTask]) -> List[Strategy]:
        """Calculate multiple strategies in parallel"""
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        # Create calculation futures
        futures = []
        for task in sorted_tasks:
            if task.calculation_type == "exhaustive":
                future = self.process_executor.submit(
                    self._exhaustive_calculation_worker, task
                )
            else:
                future = self.thread_executor.submit(
                    self._monte_carlo_worker, task
                )
            futures.append((task, future))
        
        # Collect results as they complete
        results = []
        for task, future in futures:
            try:
                strategy = future.result(timeout=300)  # 5 minute timeout
                results.append(strategy)
            except concurrent.futures.TimeoutError:
                # Handle timeout gracefully
                results.append(self._create_fallback_strategy(task))
            except Exception as e:
                # Log error and provide fallback
                logger.error(f"Calculation failed for task {task.task_id}: {e}")
                results.append(self._create_fallback_strategy(task))
        
        return results
    
    def _exhaustive_calculation_worker(self, task: CalculationTask) -> Strategy:
        """Worker function for exhaustive calculations (CPU-bound)"""
        calculator = StrategyCalculator()
        return calculator.calculate_exhaustive_strategy(
            task.position, 
            task.depth
        )
    
    def _monte_carlo_worker(self, task: CalculationTask) -> Strategy:
        """Worker function for Monte Carlo simulations (I/O-bound)"""
        calculator = StrategyCalculator()
        return calculator.calculate_monte_carlo_strategy(
            task.position,
            samples=50000
        )
    
    async def shutdown(self):
        """Clean shutdown of all executors"""
        self.process_executor.shutdown(wait=True)
        self.thread_executor.shutdown(wait=True)
```

---

## Performance Optimization Strategies

### 1. Caching Architecture

```python
from typing import Dict, Any, Optional
import redis
import pickle
import hashlib
from datetime import timedelta

class StrategyCache:
    """
    Multi-level caching for calculated strategies.
    Reduces computation time for similar positions.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.memory_cache: Dict[str, Any] = {}
        self.max_memory_entries = 10000
    
    def get_strategy(self, position: Position) -> Optional[Strategy]:
        """Retrieve cached strategy for position"""
        cache_key = self._generate_cache_key(position)
        
        # Check memory cache first (fastest)
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Check Redis cache (network overhead)
        cached_data = self.redis.get(f"strategy:{cache_key}")
        if cached_data:
            strategy = pickle.loads(cached_data)
            # Promote to memory cache
            self._store_in_memory(cache_key, strategy)
            return strategy
        
        return None
    
    def store_strategy(self, position: Position, strategy: Strategy) -> None:
        """Store calculated strategy in cache"""
        cache_key = self._generate_cache_key(position)
        
        # Store in memory cache
        self._store_in_memory(cache_key, strategy)
        
        # Store in Redis with expiration
        serialized = pickle.dumps(strategy)
        self.redis.setex(
            f"strategy:{cache_key}",
            timedelta(hours=24),
            serialized
        )
    
    def _generate_cache_key(self, position: Position) -> str:
        """Generate deterministic cache key for position"""
        # Create normalized position representation
        position_data = {
            'hands': sorted([
                (pid, sorted(hand.cards)) 
                for pid, hand in position.players_hands.items()
            ]),
            'remaining_cards': sorted(position.remaining_cards),
            'current_player': position.current_player,
            'round': position.round_number
        }
        
        # Hash for consistent key generation
        position_str = str(position_data)
        return hashlib.md5(position_str.encode()).hexdigest()
    
    def _store_in_memory(self, key: str, value: Any) -> None:
        """Store in memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_entries:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = value
```

### 2. Database Schema Design

```sql
-- Core game tables optimized for OFC
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_count INTEGER NOT NULL,
    rules_variant VARCHAR(50) NOT NULL DEFAULT 'standard',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    final_scores JSONB,
    INDEX idx_games_created (created_at),
    INDEX idx_games_completed (completed_at)
);

-- Optimized for position lookups and analysis
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(id),
    round_number INTEGER NOT NULL,
    current_player INTEGER NOT NULL,
    players_hands JSONB NOT NULL,
    remaining_cards INTEGER[] NOT NULL,
    position_hash VARCHAR(32) NOT NULL, -- For caching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_positions_game (game_id, round_number),
    INDEX idx_positions_hash (position_hash),
    INDEX idx_positions_created (created_at)
);

-- Analysis results with performance optimization
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID REFERENCES positions(id),
    optimal_strategy JSONB NOT NULL,
    expected_value DECIMAL(10,6) NOT NULL,
    calculation_method VARCHAR(20) NOT NULL,
    calculation_time_ms INTEGER NOT NULL,
    confidence_level DECIMAL(4,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_analysis_position (position_id),
    INDEX idx_analysis_method (calculation_method),
    INDEX idx_analysis_created (created_at)
);

-- User performance tracking
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_type VARCHAR(20) NOT NULL, -- 'analysis', 'training', 'practice'
    positions_analyzed INTEGER DEFAULT 0,
    avg_decision_time_ms INTEGER,
    accuracy_score DECIMAL(4,3),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_sessions_user (user_id, started_at),
    INDEX idx_sessions_type (session_type, started_at)
);

-- Partitioned table for high-volume analytics
CREATE TABLE position_analytics (
    position_hash VARCHAR(32) NOT NULL,
    calculation_count INTEGER DEFAULT 1,
    avg_calculation_time_ms INTEGER,
    most_common_strategy JSONB,
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (position_hash, DATE(last_calculated))
) PARTITION BY RANGE (DATE(last_calculated));

-- Create monthly partitions
CREATE TABLE position_analytics_2024_01 PARTITION OF position_analytics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 3. API Design for Performance

```python
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import asyncio
from typing import List, Optional

app = FastAPI(title="OFC Solver API", version="1.0.0")

# Performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for services
async def get_strategy_calculator() -> StrategyCalculator:
    return StrategyCalculator()

async def get_cache_service() -> StrategyCache:
    return StrategyCache()

@app.post("/api/v1/analysis/calculate-strategy")
async def calculate_strategy(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    calculator: StrategyCalculator = Depends(get_strategy_calculator),
    cache: StrategyCache = Depends(get_cache_service)
) -> StrategyResponse:
    """
    Calculate optimal strategy for given position.
    Supports both sync and async calculation modes.
    """
    
    # Check cache first
    cached_strategy = await cache.get_strategy(request.position)
    if cached_strategy and not request.force_recalculate:
        return StrategyResponse(
            strategy=cached_strategy,
            cache_hit=True,
            calculation_time_ms=0
        )
    
    # Determine calculation approach
    if request.calculation_mode == "instant":
        # Quick heuristic-based response
        strategy = await calculator.calculate_heuristic_strategy(request.position)
    elif request.calculation_mode == "async":
        # Queue for background processing
        task_id = await queue_calculation_task(request)
        return StrategyResponse(
            task_id=task_id,
            status="queued",
            estimated_completion_time=estimate_calculation_time(request.position)
        )
    else:
        # Full calculation with timeout
        try:
            strategy = await asyncio.wait_for(
                calculator.calculate_optimal_strategy(request.position),
                timeout=request.max_calculation_time_seconds
            )
        except asyncio.TimeoutError:
            # Fallback to heuristic if timeout
            strategy = await calculator.calculate_heuristic_strategy(request.position)
    
    # Cache result for future requests
    background_tasks.add_task(cache.store_strategy, request.position, strategy)
    
    return StrategyResponse(
        strategy=strategy,
        cache_hit=False,
        calculation_time_ms=strategy.calculation_time_ms
    )

@app.get("/api/v1/analysis/task/{task_id}")
async def get_calculation_status(task_id: str) -> TaskStatusResponse:
    """Get status of background calculation task"""
    task_status = await get_task_status(task_id)
    
    if task_status.status == "completed":
        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            result=task_status.result
        )
    elif task_status.status == "failed":
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=task_status.error
        )
    else:
        return TaskStatusResponse(
            task_id=task_id,
            status="processing",
            progress_percentage=task_status.progress,
            estimated_completion_time=task_status.eta
        )

@app.websocket("/api/v1/analysis/realtime")
async def realtime_analysis(websocket: WebSocket):
    """WebSocket endpoint for real-time strategy updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive position update from client
            data = await websocket.receive_json()
            position = Position.from_dict(data['position'])
            
            # Calculate strategy asynchronously
            strategy = await calculate_strategy_streaming(position)
            
            # Send incremental results
            await websocket.send_json({
                "type": "strategy_update",
                "strategy": strategy.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
```

---

## Implementation Priorities

### Phase 1: Core Domain (Weeks 1-4)
**Priority: Critical**
- [ ] Card and Hand value objects
- [ ] Game entity with basic rules enforcement
- [ ] HandEvaluator domain service
- [ ] Basic position representation
- [ ] Simple strategy calculation (heuristic-based)

**Deliverables:**
- Working OFC game validation
- Basic hand evaluation engine
- Simple API for game state management

### Phase 2: Strategy Engine (Weeks 5-8)
**Priority: High**
- [ ] GameTreeBuilder implementation
- [ ] Monte Carlo simulation engine
- [ ] Basic caching layer
- [ ] Parallel calculation infrastructure
- [ ] Strategy comparison and ranking

**Deliverables:**
- Working GTO solver for simple positions
- Performance benchmarks and optimization
- Caching system with Redis integration

### Phase 3: Advanced Analysis (Weeks 9-12)
**Priority: High**
- [ ] Complex position analysis
- [ ] Exhaustive end-game solver
- [ ] Advanced pruning algorithms
- [ ] Multi-player position handling
- [ ] Confidence interval calculations

**Deliverables:**
- Production-ready solver engine
- Comprehensive test suite
- Performance monitoring system

### Phase 4: User Interface (Weeks 13-16)
**Priority: Medium**
- [ ] React-based game board component
- [ ] Analysis results visualization
- [ ] Real-time strategy updates
- [ ] Mobile-responsive design
- [ ] User session management

**Deliverables:**
- Complete web application
- User authentication system
- Responsive UI/UX

### Phase 5: Training System (Weeks 17-20)
**Priority: Medium**
- [ ] Training scenario generator
- [ ] Adaptive difficulty system
- [ ] Performance tracking
- [ ] Progress visualization
- [ ] Social features (leaderboards, sharing)

**Deliverables:**
- Complete training platform
- User analytics dashboard
- Community features

### Phase 6: Advanced Features (Weeks 21-24)
**Priority: Low**
- [ ] Advanced analytics and reporting
- [ ] Opponent modeling
- [ ] Tournament analysis tools
- [ ] API integrations with poker platforms
- [ ] Mobile application

**Deliverables:**
- Advanced analytics platform
- Mobile app (iOS/Android)
- Third-party integrations

---

## Monitoring and Observability

### Application Metrics
```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
calculation_requests = Counter('ofc_calculations_total', 'Total calculation requests', ['method', 'status'])
calculation_duration = Histogram('ofc_calculation_duration_seconds', 'Calculation duration', ['method'])
active_calculations = Gauge('ofc_active_calculations', 'Currently active calculations')
cache_hits = Counter('ofc_cache_hits_total', 'Cache hits', ['cache_type'])

def monitor_calculation(calculation_method: str):
    """Decorator to monitor calculation performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            active_calculations.inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                calculation_requests.labels(method=calculation_method, status='success').inc()
                return result
            except Exception as e:
                calculation_requests.labels(method=calculation_method, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                calculation_duration.labels(method=calculation_method).observe(duration)
                active_calculations.dec()
        
        return wrapper
    return decorator

@monitor_calculation('monte_carlo')
async def calculate_monte_carlo_strategy(position: Position) -> Strategy:
    # Implementation here
    pass
```

### Health Checks
```python
from fastapi import FastAPI
from typing import Dict, Any

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        await database.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Redis connectivity
    try:
        await redis_client.ping()
        health_status["checks"]["cache"] = "healthy"
    except Exception as e:
        health_status["checks"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Calculation engine
    try:
        test_calculation = await quick_health_calculation()
        if test_calculation.execution_time_ms < 1000:
            health_status["checks"]["solver"] = "healthy"
        else:
            health_status["checks"]["solver"] = "slow"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["solver"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

---

## Security Considerations

### Input Validation
```python
from pydantic import BaseModel, validator
from typing import List

class PositionRequest(BaseModel):
    """Validated position input"""
    players_hands: Dict[str, List[str]]  # player_id -> card strings
    remaining_cards: List[str]
    current_player: str
    round_number: int
    
    @validator('players_hands')
    def validate_hands(cls, v):
        for player_id, cards in v.items():
            if len(cards) > 13:  # Max cards in OFC
                raise ValueError(f"Too many cards for player {player_id}")
            for card in cards:
                if not cls._is_valid_card(card):
                    raise ValueError(f"Invalid card format: {card}")
        return v
    
    @validator('remaining_cards')
    def validate_remaining_cards(cls, v):
        if len(v) > 52:
            raise ValueError("Too many remaining cards")
        return v
    
    @staticmethod
    def _is_valid_card(card: str) -> bool:
        """Validate card string format (e.g., 'As', 'Kh', '2c')"""
        if len(card) != 2:
            return False
        rank, suit = card[0], card[1]
        return rank in '23456789TJQKA' and suit in 'shdc'
```

### Rate Limiting
```python
from fastapi import HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/analysis/calculate-strategy")
@limiter.limit("10/minute")  # Allow 10 calculations per minute per IP
async def calculate_strategy(request: Request, analysis_request: AnalysisRequest):
    # Implementation
    pass
```

---

## Conclusion

This technical design provides a robust foundation for the OFC Solver system, emphasizing:

1. **Clean Domain Model**: Clear separation of business logic using DDD principles
2. **Performance Optimization**: Multi-level caching, parallel processing, and efficient algorithms
3. **Scalability**: Designed to handle concurrent users and computationally intensive calculations
4. **Maintainability**: Well-structured code with clear boundaries and responsibilities
5. **Extensibility**: Architecture supports future enhancements and feature additions

The implementation plan provides a practical roadmap for development, prioritizing core functionality while maintaining quality and performance standards throughout the development process.

Key architectural decisions:
- **Python-based** for rapid development and rich ecosystem
- **Event-driven architecture** for loose coupling
- **CQRS pattern** for optimal read/write performance  
- **Multi-level caching** for computation efficiency
- **Parallel processing** for handling complex calculations
- **Clean API design** for frontend integration

This design successfully addresses all requirements from the BDD scenarios while providing a solid technical foundation for building a world-class OFC poker solver.