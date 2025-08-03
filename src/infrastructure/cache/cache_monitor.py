"""
Cache Performance Monitoring for OFC Solver System.

Tracks cache performance metrics and provides insights
for optimization.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics
import logging
from collections import deque, defaultdict
import json

from .cache_manager import CacheManager
from .distributed_cache import DistributedCacheManager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of cache metrics."""
    HIT_RATE = "hit_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    KEY_COUNT = "key_count"
    EVICTION_RATE = "eviction_rate"
    ERROR_RATE = "error_rate"


@dataclass
class CacheMetric:
    """A single cache metric measurement."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Alert for cache performance issues."""
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float
    node_id: Optional[str] = None


class CacheMonitor:
    """
    Monitors cache performance and provides analytics.
    
    Features:
    - Real-time metric collection
    - Performance alerting
    - Trend analysis
    - Optimization recommendations
    """
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        distributed_cache: Optional[DistributedCacheManager] = None,
        window_size: int = 300,  # 5 minutes
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """Initialize cache monitor."""
        self.cache_manager = cache_manager
        self.distributed_cache = distributed_cache
        self.window_size = window_size
        
        # Metric storage (using deque for sliding window)
        self.metrics: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=window_size)
            for metric_type in MetricType
        }
        
        # Operation tracking
        self.operation_times: deque = deque(maxlen=1000)
        self.operation_counts = defaultdict(int)
        
        # Alert configuration
        self.alert_thresholds = alert_thresholds or {
            "hit_rate_low": 0.7,
            "latency_high": 100,  # ms
            "error_rate_high": 0.05,
            "memory_usage_high": 0.85
        }
        
        self.alerts: List[PerformanceAlert] = []
        self.last_check_time = datetime.utcnow()
    
    def record_cache_operation(
        self,
        operation: str,
        duration_ms: float,
        hit: bool,
        error: bool = False,
        node_id: Optional[str] = None
    ) -> None:
        """Record a cache operation for monitoring."""
        timestamp = datetime.utcnow()
        
        # Record operation time
        self.operation_times.append((timestamp, duration_ms))
        
        # Update counters
        self.operation_counts["total"] += 1
        self.operation_counts[operation] += 1
        
        if hit:
            self.operation_counts["hits"] += 1
        else:
            self.operation_counts["misses"] += 1
            
        if error:
            self.operation_counts["errors"] += 1
        
        # Record latency metric
        self.metrics[MetricType.LATENCY].append(
            CacheMetric(
                metric_type=MetricType.LATENCY,
                value=duration_ms,
                timestamp=timestamp,
                node_id=node_id,
                metadata={"operation": operation}
            )
        )
        
        # Check if we need to calculate new metrics
        if (timestamp - self.last_check_time).total_seconds() > 10:
            self._calculate_metrics()
            self._check_alerts()
            self.last_check_time = timestamp
    
    def _calculate_metrics(self) -> None:
        """Calculate current cache metrics."""
        timestamp = datetime.utcnow()
        
        # Calculate hit rate
        total = self.operation_counts["total"]
        if total > 0:
            hit_rate = self.operation_counts["hits"] / total
            self.metrics[MetricType.HIT_RATE].append(
                CacheMetric(
                    metric_type=MetricType.HIT_RATE,
                    value=hit_rate,
                    timestamp=timestamp
                )
            )
        
        # Calculate error rate
        if total > 0:
            error_rate = self.operation_counts["errors"] / total
            self.metrics[MetricType.ERROR_RATE].append(
                CacheMetric(
                    metric_type=MetricType.ERROR_RATE,
                    value=error_rate,
                    timestamp=timestamp
                )
            )
        
        # Calculate throughput (ops/sec)
        if self.operation_times:
            recent_ops = [t for t, _ in self.operation_times 
                         if (timestamp - t).total_seconds() < 60]
            throughput = len(recent_ops) / 60.0
            self.metrics[MetricType.THROUGHPUT].append(
                CacheMetric(
                    metric_type=MetricType.THROUGHPUT,
                    value=throughput,
                    timestamp=timestamp
                )
            )
        
        # Get cache stats if available
        if self.cache_manager:
            self._collect_cache_manager_stats(timestamp)
            
        if self.distributed_cache:
            self._collect_distributed_cache_stats(timestamp)
    
    def _collect_cache_manager_stats(self, timestamp: datetime) -> None:
        """Collect stats from cache manager."""
        try:
            # Get Redis info
            info = self.cache_manager.cache.redis_client.info()
            
            # Memory usage
            if "used_memory" in info:
                memory_mb = info["used_memory"] / (1024 * 1024)
                self.metrics[MetricType.MEMORY_USAGE].append(
                    CacheMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=memory_mb,
                        timestamp=timestamp
                    )
                )
            
            # Key count
            if "db0" in info:
                key_count = info["db0"].get("keys", 0)
                self.metrics[MetricType.KEY_COUNT].append(
                    CacheMetric(
                        metric_type=MetricType.KEY_COUNT,
                        value=key_count,
                        timestamp=timestamp
                    )
                )
            
            # Eviction rate
            if "evicted_keys" in info:
                # Calculate rate based on previous value
                # For MVP, just record the total
                self.metrics[MetricType.EVICTION_RATE].append(
                    CacheMetric(
                        metric_type=MetricType.EVICTION_RATE,
                        value=info["evicted_keys"],
                        timestamp=timestamp
                    )
                )
                
        except Exception as e:
            logger.error(f"Failed to collect cache manager stats: {e}")
    
    def _collect_distributed_cache_stats(self, timestamp: datetime) -> None:
        """Collect stats from distributed cache."""
        try:
            stats = self.distributed_cache.get_stats()
            
            # Node-specific metrics
            for node in self.distributed_cache.nodes:
                if node.is_healthy and node.redis_cache:
                    try:
                        info = node.redis_cache.redis_client.info()
                        
                        # Memory per node
                        if "used_memory" in info:
                            memory_mb = info["used_memory"] / (1024 * 1024)
                            self.metrics[MetricType.MEMORY_USAGE].append(
                                CacheMetric(
                                    metric_type=MetricType.MEMORY_USAGE,
                                    value=memory_mb,
                                    timestamp=timestamp,
                                    node_id=node.node_id
                                )
                            )
                    except Exception as e:
                        logger.error(f"Failed to collect stats from node {node.node_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to collect distributed cache stats: {e}")
    
    def _check_alerts(self) -> None:
        """Check metrics against thresholds and generate alerts."""
        timestamp = datetime.utcnow()
        
        # Check hit rate
        if self.metrics[MetricType.HIT_RATE]:
            recent_hit_rates = [m.value for m in self.metrics[MetricType.HIT_RATE]
                               if (timestamp - m.timestamp).total_seconds() < 60]
            if recent_hit_rates:
                avg_hit_rate = statistics.mean(recent_hit_rates)
                if avg_hit_rate < self.alert_thresholds["hit_rate_low"]:
                    self._create_alert(
                        "low_hit_rate",
                        "high",
                        f"Cache hit rate {avg_hit_rate:.2%} below threshold",
                        avg_hit_rate,
                        self.alert_thresholds["hit_rate_low"]
                    )
        
        # Check latency
        if self.metrics[MetricType.LATENCY]:
            recent_latencies = [m.value for m in self.metrics[MetricType.LATENCY]
                               if (timestamp - m.timestamp).total_seconds() < 60]
            if recent_latencies:
                p95_latency = statistics.quantiles(recent_latencies, n=20)[18]  # 95th percentile
                if p95_latency > self.alert_thresholds["latency_high"]:
                    self._create_alert(
                        "high_latency",
                        "medium",
                        f"P95 latency {p95_latency:.1f}ms exceeds threshold",
                        p95_latency,
                        self.alert_thresholds["latency_high"]
                    )
        
        # Check error rate
        if self.metrics[MetricType.ERROR_RATE]:
            recent_errors = [m.value for m in self.metrics[MetricType.ERROR_RATE]
                            if (timestamp - m.timestamp).total_seconds() < 60]
            if recent_errors:
                avg_error_rate = statistics.mean(recent_errors)
                if avg_error_rate > self.alert_thresholds["error_rate_high"]:
                    self._create_alert(
                        "high_error_rate",
                        "critical",
                        f"Error rate {avg_error_rate:.2%} exceeds threshold",
                        avg_error_rate,
                        self.alert_thresholds["error_rate_high"]
                    )
    
    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metric_value: float,
        threshold: float,
        node_id: Optional[str] = None
    ) -> None:
        """Create a performance alert."""
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metric_value=metric_value,
            threshold=threshold,
            node_id=node_id
        )
        
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Log critical alerts
        if severity == "critical":
            logger.critical(f"Cache alert: {message}")
        elif severity == "high":
            logger.warning(f"Cache alert: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current cache performance metrics."""
        timestamp = datetime.utcnow()
        metrics = {}
        
        # Calculate current values for each metric type
        for metric_type in MetricType:
            recent_metrics = [m for m in self.metrics[metric_type]
                             if (timestamp - m.timestamp).total_seconds() < 300]
            
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                metrics[metric_type.value] = {
                    "current": values[-1] if values else 0,
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
                
                # Add percentiles for latency
                if metric_type == MetricType.LATENCY and len(values) > 10:
                    metrics[metric_type.value]["p50"] = statistics.median(values)
                    metrics[metric_type.value]["p95"] = statistics.quantiles(values, n=20)[18]
                    metrics[metric_type.value]["p99"] = statistics.quantiles(values, n=100)[98]
        
        # Add operation counts
        metrics["operations"] = dict(self.operation_counts)
        
        return metrics
    
    def get_trends(self, metric_type: MetricType, duration: timedelta) -> List[Dict[str, Any]]:
        """Get metric trends over specified duration."""
        cutoff_time = datetime.utcnow() - duration
        
        trends = []
        for metric in self.metrics[metric_type]:
            if metric.timestamp > cutoff_time:
                trends.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "node_id": metric.node_id,
                    "metadata": metric.metadata
                })
        
        return trends
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cache optimization recommendations based on metrics."""
        recommendations = []
        current_metrics = self.get_current_metrics()
        
        # Check hit rate
        if MetricType.HIT_RATE.value in current_metrics:
            hit_rate = current_metrics[MetricType.HIT_RATE.value]["avg"]
            if hit_rate < 0.7:
                recommendations.append({
                    "type": "improve_hit_rate",
                    "severity": "high",
                    "recommendation": "Consider increasing cache TTL or implementing cache warming",
                    "current_value": f"{hit_rate:.2%}",
                    "target_value": ">80%"
                })
        
        # Check latency
        if MetricType.LATENCY.value in current_metrics:
            p95_latency = current_metrics[MetricType.LATENCY.value].get("p95", 0)
            if p95_latency > 50:
                recommendations.append({
                    "type": "reduce_latency",
                    "severity": "medium",
                    "recommendation": "Consider adding more cache nodes or optimizing serialization",
                    "current_value": f"{p95_latency:.1f}ms",
                    "target_value": "<50ms"
                })
        
        # Check memory usage
        if MetricType.MEMORY_USAGE.value in current_metrics:
            memory_mb = current_metrics[MetricType.MEMORY_USAGE.value]["current"]
            # Assume 1GB limit for MVP
            if memory_mb > 800:
                recommendations.append({
                    "type": "memory_optimization",
                    "severity": "high",
                    "recommendation": "Implement eviction policies or reduce cache TTL",
                    "current_value": f"{memory_mb:.0f}MB",
                    "target_value": "<800MB"
                })
        
        # Check error rate
        if MetricType.ERROR_RATE.value in current_metrics:
            error_rate = current_metrics[MetricType.ERROR_RATE.value]["avg"]
            if error_rate > 0.01:
                recommendations.append({
                    "type": "reduce_errors",
                    "severity": "critical",
                    "recommendation": "Investigate cache connection issues or timeout settings",
                    "current_value": f"{error_rate:.2%}",
                    "target_value": "<1%"
                })
        
        return recommendations
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent alerts, optionally filtered by severity."""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return [
            {
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "node_id": alert.node_id
            }
            for alert in alerts[-20:]  # Last 20 alerts
        ]
    
    def export_metrics(self, filepath: str) -> None:
        """Export metrics to file for analysis."""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "metrics": {},
            "alerts": self.get_alerts(),
            "recommendations": self.get_optimization_recommendations()
        }
        
        # Export all metrics
        for metric_type in MetricType:
            data["metrics"][metric_type.value] = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "value": m.value,
                    "node_id": m.node_id,
                    "metadata": m.metadata
                }
                for m in self.metrics[metric_type]
            ]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported cache metrics to {filepath}")
    
    def reset_metrics(self) -> None:
        """Reset all metrics and counters."""
        for metric_list in self.metrics.values():
            metric_list.clear()
        
        self.operation_times.clear()
        self.operation_counts.clear()
        self.alerts.clear()
        
        logger.info("Cache metrics reset")