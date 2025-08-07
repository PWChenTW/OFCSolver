"""
Advanced performance monitoring and analytics system.
Real-time metrics collection, anomaly detection, and performance optimization insights.
"""

import time
import asyncio
import statistics
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    description: str
    triggered_at: Optional[float] = None
    resolved_at: Optional[float] = None
    is_active: bool = False


class PerformanceMetrics:
    """
    High-performance metrics collection and analysis.
    Thread-safe implementation with minimal overhead.
    """

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance tracking
        self.start_time = time.time()
        self.last_cleanup = time.time()

    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._generate_key(name, tags)
            self.counters[key] += value
            self._record_metric(name, self.counters[key], MetricType.COUNTER, tags)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self._lock:
            key = self._generate_key(name, tags)
            self.gauges[key] = value
            self._record_metric(name, value, MetricType.GAUGE, tags)

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        with self._lock:
            key = self._generate_key(name, tags)
            self.histograms[key].append(value)
            
            # Keep only recent values for performance
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            
            self._record_metric(name, value, MetricType.HISTOGRAM, tags)

    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric."""
        with self._lock:
            key = self._generate_key(name, tags)
            self.timers[key].append(duration)
            self._record_metric(name, duration, MetricType.TIMER, tags)

    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, tags)

    def _record_metric(self, name: str, value: float, metric_type: MetricType, tags: Optional[Dict[str, str]]):
        """Internal method to record metric points."""
        metric_point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {}
        )
        
        key = self._generate_key(name, tags)
        self.metrics[key].append(metric_point)

    def _generate_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Generate unique key for metric with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_metric_summary(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get comprehensive summary of a metric."""
        with self._lock:
            key = self._generate_key(name, tags)
            
            if key not in self.metrics:
                return {"error": "Metric not found"}
            
            points = list(self.metrics[key])
            if not points:
                return {"error": "No data points"}
            
            values = [p.value for p in points]
            recent_values = values[-100:]  # Last 100 points
            
            summary = {
                "name": name,
                "tags": tags or {},
                "total_points": len(values),
                "current_value": values[-1] if values else 0,
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": statistics.mean(values),
                "recent_avg": statistics.mean(recent_values) if recent_values else 0,
                "trend": self._calculate_trend(values),
                "last_updated": points[-1].timestamp if points else 0
            }
            
            # Add percentiles for histograms and timers
            if len(values) > 1:
                sorted_values = sorted(values)
                summary.update({
                    "p50": statistics.median(sorted_values),
                    "p95": sorted_values[int(0.95 * len(sorted_values))],
                    "p99": sorted_values[int(0.99 * len(sorted_values))],
                    "stddev": statistics.stdev(values) if len(values) > 1 else 0
                })
            
            return summary

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for metric values."""
        if len(values) < 10:
            return "insufficient_data"
        
        recent = values[-10:]
        older = values[-20:-10] if len(values) >= 20 else values[:-10]
        
        if not older:
            return "no_baseline"
        
        recent_avg = statistics.mean(recent)
        older_avg = statistics.mean(older)
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"

    def cleanup_old_data(self, max_age_seconds: float = 3600):
        """Clean up old metric data to prevent memory leaks."""
        current_time = time.time()
        
        if current_time - self.last_cleanup < 300:  # Cleanup every 5 minutes
            return
        
        with self._lock:
            cutoff_time = current_time - max_age_seconds
            
            for key, points in self.metrics.items():
                # Remove old points
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()
            
            # Clean up histogram data
            for key, values in self.histograms.items():
                if len(values) > 500:
                    self.histograms[key] = values[-500:]
        
        self.last_cleanup = current_time


class TimerContext:
    """Context manager for timing operations."""

    def __init__(self, metrics: PerformanceMetrics, name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_timer(self.name, duration, self.tags)


class AnomalyDetector:
    """
    Statistical anomaly detection for performance metrics.
    Uses multiple algorithms for robust detection.
    """

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Standard deviations for anomaly threshold
        self.baseline_window = 100      # Number of points for baseline
        self.detection_methods = [
            self._z_score_detection,
            self._iqr_detection,
            self._moving_average_detection
        ]

    def detect_anomalies(self, values: List[float]) -> Dict[str, Any]:
        """
        Detect anomalies in metric values using multiple methods.
        Returns comprehensive anomaly analysis.
        """
        if len(values) < self.baseline_window:
            return {
                "anomalies_detected": False,
                "reason": "insufficient_data",
                "required_points": self.baseline_window,
                "current_points": len(values)
            }

        results = {}
        anomalies_found = False

        for method in self.detection_methods:
            method_result = method(values)
            method_name = method.__name__.replace('_detection', '')
            results[method_name] = method_result
            
            if method_result.get("anomaly_detected", False):
                anomalies_found = True

        # Consensus scoring
        consensus_score = sum(
            1 for result in results.values() 
            if result.get("anomaly_detected", False)
        ) / len(self.detection_methods)

        return {
            "anomalies_detected": anomalies_found,
            "consensus_score": consensus_score,
            "detection_methods": results,
            "severity": self._classify_severity(consensus_score, values),
            "recommendation": self._generate_recommendation(consensus_score, results)
        }

    def _z_score_detection(self, values: List[float]) -> Dict[str, Any]:
        """Z-score based anomaly detection."""
        baseline = values[:-10]  # All but last 10 points
        recent = values[-10:]    # Last 10 points
        
        if len(baseline) < 10:
            return {"anomaly_detected": False, "reason": "insufficient_baseline"}
        
        baseline_mean = statistics.mean(baseline)
        baseline_std = statistics.stdev(baseline) if len(baseline) > 1 else 0
        
        if baseline_std == 0:
            return {"anomaly_detected": False, "reason": "zero_variance"}
        
        recent_mean = statistics.mean(recent)
        z_score = abs(recent_mean - baseline_mean) / baseline_std
        
        return {
            "anomaly_detected": z_score > self.sensitivity,
            "z_score": z_score,
            "threshold": self.sensitivity,
            "baseline_mean": baseline_mean,
            "recent_mean": recent_mean,
            "deviation": abs(recent_mean - baseline_mean)
        }

    def _iqr_detection(self, values: List[float]) -> Dict[str, Any]:
        """Interquartile Range based anomaly detection."""
        baseline = values[:-10]
        recent = values[-10:]
        
        if len(baseline) < 20:
            return {"anomaly_detected": False, "reason": "insufficient_baseline"}
        
        sorted_baseline = sorted(baseline)
        q1 = sorted_baseline[len(sorted_baseline) // 4]
        q3 = sorted_baseline[3 * len(sorted_baseline) // 4]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        recent_mean = statistics.mean(recent)
        anomaly_detected = recent_mean < lower_bound or recent_mean > upper_bound
        
        return {
            "anomaly_detected": anomaly_detected,
            "recent_mean": recent_mean,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "iqr": iqr
        }

    def _moving_average_detection(self, values: List[float]) -> Dict[str, Any]:
        """Moving average based trend anomaly detection."""
        if len(values) < 50:
            return {"anomaly_detected": False, "reason": "insufficient_data"}
        
        window_size = 20
        recent_window = values[-window_size:]
        previous_window = values[-2*window_size:-window_size]
        
        recent_avg = statistics.mean(recent_window)
        previous_avg = statistics.mean(previous_window)
        
        if previous_avg == 0:
            return {"anomaly_detected": False, "reason": "zero_baseline"}
        
        change_percent = abs((recent_avg - previous_avg) / previous_avg) * 100
        threshold_percent = 30  # 30% change threshold
        
        return {
            "anomaly_detected": change_percent > threshold_percent,
            "change_percent": change_percent,
            "threshold_percent": threshold_percent,
            "recent_avg": recent_avg,
            "previous_avg": previous_avg
        }

    def _classify_severity(self, consensus_score: float, values: List[float]) -> AlertSeverity:
        """Classify anomaly severity based on consensus and magnitude."""
        if consensus_score >= 0.75:
            return AlertSeverity.CRITICAL
        elif consensus_score >= 0.5:
            return AlertSeverity.ERROR
        elif consensus_score >= 0.25:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    def _generate_recommendation(self, consensus_score: float, results: Dict[str, Any]) -> str:
        """Generate actionable recommendations based on anomaly analysis."""
        if consensus_score >= 0.75:
            return "Immediate investigation required. Multiple detection methods confirm anomaly."
        elif consensus_score >= 0.5:
            return "Monitor closely. Anomaly detected by multiple methods."
        elif consensus_score >= 0.25:
            return "Potential issue detected. Consider investigating if pattern continues."
        else:
            return "No significant anomaly detected. Continue monitoring."


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis and reporting system.
    Provides insights and optimization recommendations.
    """

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.anomaly_detector = AnomalyDetector()
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.analysis_cache = {}
        self.last_analysis = time.time()

    # Core API performance metrics
    def record_api_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record API request metrics."""
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status": str(status_code)
        }
        
        self.metrics.increment_counter("api_requests_total", 1.0, tags)
        self.metrics.record_timer("api_request_duration", duration, tags)
        
        if status_code >= 400:
            self.metrics.increment_counter("api_errors_total", 1.0, tags)

    def record_database_query(self, query_type: str, duration: float, success: bool):
        """Record database query metrics."""
        tags = {
            "query_type": query_type,
            "success": str(success)
        }
        
        self.metrics.increment_counter("db_queries_total", 1.0, tags)
        self.metrics.record_timer("db_query_duration", duration, tags)

    def record_cache_operation(self, operation: str, hit: bool, duration: float):
        """Record cache operation metrics."""
        tags = {
            "operation": operation,
            "result": "hit" if hit else "miss"
        }
        
        self.metrics.increment_counter("cache_operations_total", 1.0, tags)
        self.metrics.record_timer("cache_operation_duration", duration, tags)

    def record_authentication(self, method: str, success: bool, duration: float):
        """Record authentication metrics."""
        tags = {
            "method": method,
            "success": str(success)
        }
        
        self.metrics.increment_counter("auth_attempts_total", 1.0, tags)
        self.metrics.record_timer("auth_duration", duration, tags)

    def analyze_performance(self) -> Dict[str, Any]:
        """
        Comprehensive performance analysis.
        Returns insights and recommendations.
        """
        current_time = time.time()
        
        # Check if we need fresh analysis
        if current_time - self.last_analysis < 60:  # Cache for 1 minute
            return self.analysis_cache
        
        analysis = {
            "timestamp": current_time,
            "api_performance": self._analyze_api_performance(),
            "database_performance": self._analyze_database_performance(),
            "cache_performance": self._analyze_cache_performance(),
            "authentication_performance": self._analyze_auth_performance(),
            "system_health": self._analyze_system_health(),
            "anomalies": self._detect_performance_anomalies(),
            "recommendations": []
        }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        self.analysis_cache = analysis
        self.last_analysis = current_time
        
        return analysis

    def _analyze_api_performance(self) -> Dict[str, Any]:
        """Analyze API performance metrics."""
        api_summary = self.metrics.get_metric_summary("api_request_duration")
        error_summary = self.metrics.get_metric_summary("api_errors_total")
        
        return {
            "avg_response_time": api_summary.get("avg_value", 0),
            "p95_response_time": api_summary.get("p95", 0),
            "p99_response_time": api_summary.get("p99", 0),
            "error_rate": self._calculate_error_rate(),
            "requests_per_minute": self._calculate_request_rate(),
            "trend": api_summary.get("trend", "unknown"),
            "status": self._classify_api_health(api_summary)
        }

    def _analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database performance metrics."""
        db_summary = self.metrics.get_metric_summary("db_query_duration")
        
        return {
            "avg_query_time": db_summary.get("avg_value", 0),
            "p95_query_time": db_summary.get("p95", 0),
            "slow_queries": self._count_slow_queries(),
            "query_rate": self._calculate_query_rate(),
            "trend": db_summary.get("trend", "unknown"),
            "status": self._classify_db_health(db_summary)
        }

    def _analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyze cache performance metrics."""
        cache_summary = self.metrics.get_metric_summary("cache_operations_total")
        
        return {
            "hit_rate": self._calculate_cache_hit_rate(),
            "avg_operation_time": cache_summary.get("avg_value", 0),
            "operations_per_minute": self._calculate_cache_rate(),
            "trend": cache_summary.get("trend", "unknown"),
            "status": self._classify_cache_health()
        }

    def _analyze_auth_performance(self) -> Dict[str, Any]:
        """Analyze authentication performance metrics."""
        auth_summary = self.metrics.get_metric_summary("auth_duration")
        
        return {
            "avg_auth_time": auth_summary.get("avg_value", 0),
            "success_rate": self._calculate_auth_success_rate(),
            "auth_rate": self._calculate_auth_rate(),
            "trend": auth_summary.get("trend", "unknown"),
            "status": self._classify_auth_health(auth_summary)
        }

    def _analyze_system_health(self) -> Dict[str, Any]:
        """Analyze overall system health."""
        uptime = time.time() - self.metrics.start_time
        
        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "memory_usage": self._estimate_memory_usage(),
            "metrics_collected": len(self.metrics.metrics),
            "health_score": self._calculate_health_score()
        }

    def _detect_performance_anomalies(self) -> Dict[str, Any]:
        """Detect performance anomalies across all metrics."""
        anomalies = {}
        
        key_metrics = [
            "api_request_duration",
            "db_query_duration", 
            "auth_duration"
        ]
        
        for metric_name in key_metrics:
            summary = self.metrics.get_metric_summary(metric_name)
            if "error" not in summary:
                # Get recent values for anomaly detection
                with self.metrics._lock:
                    key = metric_name
                    if key in self.metrics.metrics:
                        values = [p.value for p in self.metrics.metrics[key]]
                        anomaly_result = self.anomaly_detector.detect_anomalies(values)
                        
                        if anomaly_result["anomalies_detected"]:
                            anomalies[metric_name] = anomaly_result
        
        return anomalies

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # API performance recommendations
        api_perf = analysis["api_performance"]
        if api_perf["p95_response_time"] > 5.0:
            recommendations.append("API P95 response time exceeds 5s. Consider implementing caching or optimizing slow endpoints.")
        
        if api_perf["error_rate"] > 0.05:
            recommendations.append(f"API error rate is {api_perf['error_rate']:.2%}. Investigate and fix common errors.")
        
        # Database recommendations
        db_perf = analysis["database_performance"]
        if db_perf["p95_query_time"] > 1.0:
            recommendations.append("Database P95 query time exceeds 1s. Consider adding indexes or query optimization.")
        
        # Cache recommendations
        cache_perf = analysis["cache_performance"]
        if cache_perf["hit_rate"] < 0.8:
            recommendations.append(f"Cache hit rate is {cache_perf['hit_rate']:.2%}. Review caching strategy and TTL settings.")
        
        # Anomaly recommendations
        if analysis["anomalies"]:
            recommendations.append(f"Performance anomalies detected in {len(analysis['anomalies'])} metrics. Investigate immediately.")
        
        return recommendations

    # Helper methods for calculations
    def _calculate_error_rate(self) -> float:
        """Calculate API error rate."""
        # Implementation would calculate based on error vs total requests
        return 0.02  # Placeholder

    def _calculate_request_rate(self) -> float:
        """Calculate requests per minute."""
        # Implementation would calculate based on request timestamps
        return 100.0  # Placeholder

    def _calculate_query_rate(self) -> float:
        """Calculate database queries per minute."""
        return 50.0  # Placeholder

    def _count_slow_queries(self) -> int:
        """Count slow database queries."""
        return 5  # Placeholder

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return 0.85  # Placeholder

    def _calculate_cache_rate(self) -> float:
        """Calculate cache operations per minute."""
        return 200.0  # Placeholder

    def _calculate_auth_success_rate(self) -> float:
        """Calculate authentication success rate."""
        return 0.98  # Placeholder

    def _calculate_auth_rate(self) -> float:
        """Calculate authentication attempts per minute."""
        return 20.0  # Placeholder

    def _classify_api_health(self, summary: Dict[str, Any]) -> str:
        """Classify API health status."""
        avg_time = summary.get("avg_value", 0)
        if avg_time < 0.5:
            return "excellent"
        elif avg_time < 2.0:
            return "good"
        elif avg_time < 5.0:
            return "fair"
        else:
            return "poor"

    def _classify_db_health(self, summary: Dict[str, Any]) -> str:
        """Classify database health status."""
        avg_time = summary.get("avg_value", 0)
        if avg_time < 0.1:
            return "excellent"
        elif avg_time < 0.5:
            return "good"
        elif avg_time < 1.0:
            return "fair"
        else:
            return "poor"

    def _classify_cache_health(self) -> str:
        """Classify cache health status."""
        hit_rate = self._calculate_cache_hit_rate()
        if hit_rate > 0.9:
            return "excellent"
        elif hit_rate > 0.8:
            return "good"
        elif hit_rate > 0.6:
            return "fair"
        else:
            return "poor"

    def _classify_auth_health(self, summary: Dict[str, Any]) -> str:
        """Classify authentication health status."""
        avg_time = summary.get("avg_value", 0)
        if avg_time < 0.1:
            return "excellent"
        elif avg_time < 0.5:
            return "good"
        elif avg_time < 1.0:
            return "fair"
        else:
            return "poor"

    def _estimate_memory_usage(self) -> Dict[str, Any]:
        """Estimate memory usage of monitoring system."""
        # Rough estimation based on stored metrics
        total_points = sum(len(points) for points in self.metrics.metrics.values())
        estimated_mb = (total_points * 100) / (1024 * 1024)  # Rough estimate
        
        return {
            "estimated_mb": estimated_mb,
            "total_metric_points": total_points,
            "metric_types": len(self.metrics.metrics)
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        # Simplified health score calculation
        score = 100
        
        # Deduct points for high response times, errors, etc.
        api_summary = self.metrics.get_metric_summary("api_request_duration")
        if api_summary.get("avg_value", 0) > 2.0:
            score -= 20
        
        return max(0, score)


# Global performance analyzer instance
performance_analyzer = PerformanceAnalyzer()


def get_performance_analyzer() -> PerformanceAnalyzer:
    """Get the performance analyzer instance."""
    return performance_analyzer