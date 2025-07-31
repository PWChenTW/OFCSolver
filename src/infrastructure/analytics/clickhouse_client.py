from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
import asyncio
import logging
from contextlib import asynccontextmanager

from clickhouse_driver import Client
from clickhouse_driver.errors import Error as ClickHouseError

from src.config import settings

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Async ClickHouse client for analytics data."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "ofc_analytics",
        user: str = "default",
        password: str = "",
        **kwargs
    ):
        """Initialize ClickHouse client.
        
        Args:
            host: ClickHouse server host
            port: ClickHouse native port (9000)
            database: Database name
            user: Username
            password: Password
            **kwargs: Additional client parameters
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.client_params = kwargs
        self._client = None
        
    def _get_client(self) -> Client:
        """Get or create ClickHouse client."""
        if self._client is None:
            self._client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                **self.client_params
            )
        return self._client
        
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        with_column_types: bool = False
    ) -> Union[List[tuple], tuple]:
        """Execute a query asynchronously.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            with_column_types: Include column types in response
            
        Returns:
            Query results
        """
        loop = asyncio.get_event_loop()
        client = self._get_client()
        
        try:
            result = await loop.run_in_executor(
                None,
                lambda: client.execute(query, params, with_column_types=with_column_types)
            )
            return result
        except ClickHouseError as e:
            logger.error(f"ClickHouse query error: {e}")
            raise
            
    async def insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        column_names: Optional[List[str]] = None
    ) -> int:
        """Insert data into a table.
        
        Args:
            table: Table name
            data: List of dictionaries to insert
            column_names: Column names (if not provided, uses keys from first dict)
            
        Returns:
            Number of rows inserted
        """
        if not data:
            return 0
            
        loop = asyncio.get_event_loop()
        client = self._get_client()
        
        # Get column names from first record if not provided
        if column_names is None:
            column_names = list(data[0].keys())
            
        # Convert data to list of tuples
        values = [tuple(row.get(col) for col in column_names) for row in data]
        
        # Build insert query
        columns_str = ", ".join(column_names)
        placeholders = ", ".join(["%s"] * len(column_names))
        query = f"INSERT INTO {table} ({columns_str}) VALUES"
        
        try:
            await loop.run_in_executor(
                None,
                lambda: client.execute(query, values)
            )
            return len(data)
        except ClickHouseError as e:
            logger.error(f"ClickHouse insert error: {e}")
            raise
            
    async def query_dataframe(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute query and return results as pandas DataFrame.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            pandas DataFrame with results
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for query_dataframe")
            
        loop = asyncio.get_event_loop()
        client = self._get_client()
        
        try:
            df = await loop.run_in_executor(
                None,
                lambda: client.query_dataframe(query, params)
            )
            return df
        except ClickHouseError as e:
            logger.error(f"ClickHouse query error: {e}")
            raise
            
    # Analytics-specific methods
    
    async def log_game_event(
        self,
        game_id: str,
        event_type: str,
        player_id: int,
        round_number: int,
        event_data: Dict[str, Any]
    ) -> bool:
        """Log a game event.
        
        Args:
            game_id: Game identifier
            event_type: Type of event
            player_id: Player identifier
            round_number: Current round
            event_data: Additional event data
            
        Returns:
            True if logged successfully
        """
        try:
            await self.insert(
                "game_events",
                [{
                    "game_id": game_id,
                    "event_type": event_type,
                    "player_id": player_id,
                    "round_number": round_number,
                    "event_data": str(event_data),
                    "timestamp": datetime.now()
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log game event: {e}")
            return False
            
    async def log_calculation_metric(
        self,
        position_hash: str,
        calculation_method: str,
        calculation_time_ms: int,
        tree_nodes_explored: int,
        memory_used_mb: int,
        confidence_level: float,
        cache_hit: bool = False
    ) -> bool:
        """Log calculation performance metrics.
        
        Args:
            position_hash: Position identifier
            calculation_method: Method used
            calculation_time_ms: Calculation time
            tree_nodes_explored: Number of nodes explored
            memory_used_mb: Memory usage
            confidence_level: Confidence in result
            cache_hit: Whether cache was hit
            
        Returns:
            True if logged successfully
        """
        try:
            await self.insert(
                "calculation_metrics",
                [{
                    "position_hash": position_hash,
                    "calculation_method": calculation_method,
                    "calculation_time_ms": calculation_time_ms,
                    "tree_nodes_explored": tree_nodes_explored,
                    "memory_used_mb": memory_used_mb,
                    "cpu_cores_used": 1,  # TODO: Get actual CPU cores used
                    "confidence_level": confidence_level,
                    "cache_hit": cache_hit,
                    "timestamp": datetime.now()
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log calculation metric: {e}")
            return False
            
    async def log_player_performance(
        self,
        session_id: str,
        user_id: Optional[str],
        scenario_id: str,
        decision_time_seconds: int,
        is_correct: bool,
        ev_difference: float,
        difficulty_level: str
    ) -> bool:
        """Log player performance metrics.
        
        Args:
            session_id: Training session ID
            user_id: User ID (optional)
            scenario_id: Scenario identifier
            decision_time_seconds: Time to make decision
            is_correct: Whether answer was correct
            ev_difference: EV difference from optimal
            difficulty_level: Difficulty level
            
        Returns:
            True if logged successfully
        """
        try:
            await self.insert(
                "player_performance",
                [{
                    "session_id": session_id,
                    "user_id": user_id,
                    "scenario_id": scenario_id,
                    "decision_time_seconds": decision_time_seconds,
                    "is_correct": is_correct,
                    "ev_difference": ev_difference,
                    "difficulty_level": difficulty_level,
                    "timestamp": datetime.now()
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log player performance: {e}")
            return False
            
    async def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        user_agent: str,
        ip_address: str,
        request_size: int = 0,
        response_size: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Log API request metrics.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time
            user_agent: User agent string
            ip_address: Client IP address
            request_size: Request size in bytes
            response_size: Response size in bytes
            error_message: Error message if any
            
        Returns:
            True if logged successfully
        """
        try:
            await self.insert(
                "api_requests",
                [{
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                    "user_agent": user_agent,
                    "ip_address": ip_address,
                    "request_size_bytes": request_size,
                    "response_size_bytes": response_size,
                    "error_message": error_message,
                    "timestamp": datetime.now()
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            return False
            
    # Query methods for analytics
    
    async def get_game_statistics(
        self,
        start_date: date,
        end_date: date,
        rules_variant: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get game statistics for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            rules_variant: Filter by rules variant
            
        Returns:
            List of statistics
        """
        query = """
        SELECT
            hour_date,
            hour,
            rules_variant,
            total_games,
            completed_games,
            abandoned_games,
            avg_game_duration
        FROM game_stats_hourly
        WHERE hour_date >= %(start_date)s
        AND hour_date <= %(end_date)s
        """
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        if rules_variant:
            query += " AND rules_variant = %(rules_variant)s"
            params["rules_variant"] = rules_variant
            
        query += " ORDER BY hour_date, hour"
        
        results = await self.execute(query, params)
        
        return [
            {
                "date": row[0],
                "hour": row[1],
                "rules_variant": row[2],
                "total_games": row[3],
                "completed_games": row[4],
                "abandoned_games": row[5],
                "avg_duration_minutes": row[6]
            }
            for row in results
        ]
        
    async def get_solver_performance(
        self,
        start_date: date,
        end_date: date,
        calculation_method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get solver performance statistics.
        
        Args:
            start_date: Start date
            end_date: End date
            calculation_method: Filter by method
            
        Returns:
            List of performance metrics
        """
        query = """
        SELECT
            day_date,
            calculation_method,
            total_calculations,
            avg_calculation_time,
            median_calculation_time,
            p95_calculation_time,
            avg_confidence,
            cache_hits
        FROM solver_stats_daily
        WHERE day_date >= %(start_date)s
        AND day_date <= %(end_date)s
        """
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        if calculation_method:
            query += " AND calculation_method = %(method)s"
            params["method"] = calculation_method
            
        query += " ORDER BY day_date, calculation_method"
        
        results = await self.execute(query, params)
        
        return [
            {
                "date": row[0],
                "method": row[1],
                "total_calculations": row[2],
                "avg_time_ms": row[3],
                "median_time_ms": row[4],
                "p95_time_ms": row[5],
                "avg_confidence": row[6],
                "cache_hits": row[7]
            }
            for row in results
        ]
        
    async def close(self):
        """Close ClickHouse connection."""
        if self._client:
            self._client.disconnect()
            self._client = None
            
    async def ping(self) -> bool:
        """Check if ClickHouse is accessible.
        
        Returns:
            True if accessible
        """
        try:
            await self.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"ClickHouse ping failed: {e}")
            return False


# Global ClickHouse client instance
clickhouse_client = ClickHouseClient(
    host=settings.environment == "development" and "clickhouse" or "localhost",
    database="ofc_analytics"
)


@asynccontextmanager
async def get_clickhouse():
    """Get ClickHouse client for dependency injection."""
    yield clickhouse_client