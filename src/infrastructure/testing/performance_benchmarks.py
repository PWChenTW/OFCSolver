"""
Comprehensive performance benchmarking system for API optimizations.
Validates authentication algorithms, rate limiting, and error recovery performance.
"""

import asyncio
import time
import statistics
import concurrent.futures
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging
import json
from datetime import datetime

from src.infrastructure.security.auth_algorithms import get_auth_service
from src.infrastructure.algorithms.rate_limiting import get_rate_limit_manager
from src.infrastructure.reliability.error_recovery import get_fault_tolerance
from src.infrastructure.monitoring.performance_analytics import get_performance_analyzer

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""
    test_name: str
    duration_seconds: float
    operations_count: int
    success_count: int
    failure_count: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput_ops_per_second: float
    error_rate: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    additional_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    duration_seconds: int = 60
    concurrent_users: int = 10
    operations_per_user: int = 100
    warmup_seconds: int = 10
    cooldown_seconds: int = 5
    target_throughput: Optional[int] = None  # ops/second


class AuthenticationBenchmark:
    """Benchmark authentication system performance."""

    def __init__(self):
        self.auth_service = get_auth_service()
        self.test_api_keys = [
            "ofc-solver-demo-key-2024",
            "ofc-solver-test-key-2024"
        ]

    async def benchmark_api_key_validation(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Benchmark API key validation performance."""
        
        logger.info(f"Starting API key validation benchmark: {config.concurrent_users} users, {config.duration_seconds}s")
        
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        async def _single_auth_test():
            """Single authentication test."""
            nonlocal success_count, failure_count
            
            api_key = self.test_api_keys[0]  # Use demo key
            test_start = time.time()
            
            try:
                result = await self.auth_service.authenticate(api_key=api_key)
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                failure_count += 1
                logger.debug(f"Auth test failed: {e}")

        # Warmup
        logger.info("Warming up authentication system...")
        for _ in range(10):
            await _single_auth_test()
        
        response_times.clear()  # Clear warmup data
        success_count = 0
        failure_count = 0
        
        # Main benchmark
        tasks = []
        end_time = start_time + config.duration_seconds
        
        while time.time() < end_time:
            # Create batch of concurrent tasks
            batch_size = min(config.concurrent_users, 50)  # Limit batch size
            batch_tasks = [_single_auth_test() for _ in range(batch_size)]
            
            await asyncio.gather(*batch_tasks)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        # Calculate results
        total_duration = time.time() - start_time
        total_operations = success_count + failure_count
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
            p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        return BenchmarkResult(
            test_name="api_key_validation",
            duration_seconds=total_duration,
            operations_count=total_operations,
            success_count=success_count,
            failure_count=failure_count,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_ops_per_second=total_operations / total_duration if total_duration > 0 else 0,
            error_rate=failure_count / total_operations if total_operations > 0 else 0,
            additional_metrics={
                "auth_method": "api_key",
                "concurrent_users": config.concurrent_users
            }
        )

    async def benchmark_jwt_validation(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Benchmark JWT validation performance."""
        
        logger.info(f"Starting JWT validation benchmark: {config.concurrent_users} users, {config.duration_seconds}s")
        
        # Generate test JWT token
        jwt_manager = self.auth_service.jwt_manager
        test_token = jwt_manager.create_access_token("test_user", "test", ["all"])
        
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        async def _single_jwt_test():
            """Single JWT validation test."""
            nonlocal success_count, failure_count
            
            test_start = time.time()
            
            try:
                result = await self.auth_service.authenticate(jwt_token=test_token)
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                failure_count += 1

        # Warmup
        for _ in range(10):
            await _single_jwt_test()
        
        response_times.clear()
        success_count = 0
        failure_count = 0
        
        # Main benchmark
        end_time = start_time + config.duration_seconds
        
        while time.time() < end_time:
            batch_tasks = [_single_jwt_test() for _ in range(config.concurrent_users)]
            await asyncio.gather(*batch_tasks)
            await asyncio.sleep(0.01)
        
        # Calculate results
        total_duration = time.time() - start_time
        total_operations = success_count + failure_count
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
            p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        return BenchmarkResult(
            test_name="jwt_validation",
            duration_seconds=total_duration,
            operations_count=total_operations,
            success_count=success_count,
            failure_count=failure_count,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_ops_per_second=total_operations / total_duration if total_duration > 0 else 0,
            error_rate=failure_count / total_operations if total_operations > 0 else 0,
            additional_metrics={
                "auth_method": "jwt",
                "concurrent_users": config.concurrent_users
            }
        )


class RateLimitingBenchmark:
    """Benchmark rate limiting system performance."""

    def __init__(self):
        self.rate_manager = get_rate_limit_manager()

    async def benchmark_token_bucket(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Benchmark token bucket rate limiting performance."""
        
        logger.info(f"Starting token bucket benchmark: {config.concurrent_users} users, {config.duration_seconds}s")
        
        # Setup test user
        test_user_id = "benchmark_user_token_bucket"
        self.rate_manager.setup_user_limits(test_user_id, "test")
        
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        async def _single_rate_limit_test():
            """Single rate limit test."""
            nonlocal success_count, failure_count
            
            test_start = time.time()
            
            try:
                result = self.rate_manager.check_rate_limit(
                    user_id=test_user_id,
                    endpoint="test_endpoint"
                )
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                
                if result.allowed:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                failure_count += 1

        # Warmup
        for _ in range(10):
            await _single_rate_limit_test()
        
        response_times.clear()
        success_count = 0
        failure_count = 0
        
        # Main benchmark - controlled rate to test algorithm performance
        end_time = start_time + config.duration_seconds
        
        while time.time() < end_time:
            # Simulate realistic request patterns
            batch_tasks = [_single_rate_limit_test() for _ in range(min(config.concurrent_users, 20))]
            await asyncio.gather(*batch_tasks)
            
            # Add realistic delay between batches
            await asyncio.sleep(0.1)  # 100ms between batches
        
        # Calculate results
        total_duration = time.time() - start_time
        total_operations = success_count + failure_count
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
            p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        return BenchmarkResult(
            test_name="token_bucket_rate_limiting",
            duration_seconds=total_duration,
            operations_count=total_operations,
            success_count=success_count,
            failure_count=failure_count,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_ops_per_second=total_operations / total_duration if total_duration > 0 else 0,
            error_rate=failure_count / total_operations if total_operations > 0 else 0,
            additional_metrics={
                "algorithm": "token_bucket",
                "concurrent_users": config.concurrent_users,
                "allowed_rate": success_count / total_operations if total_operations > 0 else 0
            }
        )


class ErrorRecoveryBenchmark:
    """Benchmark error recovery and fault tolerance performance."""

    def __init__(self):
        self.fault_tolerance = get_fault_tolerance()

    async def benchmark_retry_mechanism(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Benchmark retry mechanism performance."""
        
        logger.info(f"Starting retry mechanism benchmark: {config.concurrent_users} users, {config.duration_seconds}s")
        
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        # Simulate a flaky service that fails 30% of the time
        failure_rate = 0.3
        call_count = 0
        
        async def _flaky_service():
            """Simulate a flaky service."""
            nonlocal call_count
            call_count += 1
            
            # Simulate service delay
            await asyncio.sleep(0.01)
            
            if (call_count % 10) < (failure_rate * 10):
                raise Exception("Simulated service failure")
            
            return "success"

        async def _single_retry_test():
            """Single retry test."""
            nonlocal success_count, failure_count
            
            test_start = time.time()
            
            try:
                result = await self.fault_tolerance.execute_with_protection(
                    "test_service",
                    _flaky_service
                )
                test_duration = time.time() - test_start
                response_times.append(test_duration)
                success_count += 1
                
            except Exception as e:
                test_duration = time.time() - test_start
                response_times.append(test_duration) 
                failure_count += 1

        # Main benchmark
        end_time = start_time + config.duration_seconds
        
        while time.time() < end_time:
            batch_tasks = [_single_retry_test() for _ in range(config.concurrent_users)]
            await asyncio.gather(*batch_tasks)
            await asyncio.sleep(0.05)  # 50ms between batches
        
        # Calculate results
        total_duration = time.time() - start_time
        total_operations = success_count + failure_count
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
            p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        return BenchmarkResult(
            test_name="retry_mechanism",
            duration_seconds=total_duration,
            operations_count=total_operations,
            success_count=success_count,
            failure_count=failure_count,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_ops_per_second=total_operations / total_duration if total_duration > 0 else 0,
            error_rate=failure_count / total_operations if total_operations > 0 else 0,
            additional_metrics={
                "simulated_failure_rate": failure_rate,
                "recovery_success_rate": success_count / total_operations if total_operations > 0 else 0
            }
        )


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite."""

    def __init__(self):
        self.auth_benchmark = AuthenticationBenchmark()
        self.rate_limit_benchmark = RateLimitingBenchmark()
        self.error_recovery_benchmark = ErrorRecoveryBenchmark()
        self.performance_analyzer = get_performance_analyzer()

    async def run_comprehensive_benchmark(
        self, 
        config: Optional[BenchmarkConfig] = None
    ) -> Dict[str, Any]:
        """Run comprehensive performance benchmark suite."""
        
        if config is None:
            config = BenchmarkConfig(
                duration_seconds=30,  # Shorter for comprehensive test
                concurrent_users=10,
                warmup_seconds=5
            )
        
        logger.info("Starting comprehensive performance benchmark suite")
        start_time = time.time()
        
        results = {}
        
        try:
            # Authentication benchmarks
            logger.info("Running authentication benchmarks...")
            results["auth_api_key"] = await self.auth_benchmark.benchmark_api_key_validation(config)
            results["auth_jwt"] = await self.auth_benchmark.benchmark_jwt_validation(config)
            
            # Rate limiting benchmarks
            logger.info("Running rate limiting benchmarks...")
            results["rate_limit_token_bucket"] = await self.rate_limit_benchmark.benchmark_token_bucket(config)
            
            # Error recovery benchmarks  
            logger.info("Running error recovery benchmarks...")
            results["error_recovery_retry"] = await self.error_recovery_benchmark.benchmark_retry_mechanism(config)
            
            # Generate performance analysis
            analysis = self._analyze_benchmark_results(results)
            
            total_duration = time.time() - start_time
            
            return {
                "benchmark_suite": "comprehensive_performance",
                "timestamp": datetime.now().isoformat(),
                "total_duration_seconds": total_duration,
                "config": {
                    "duration_seconds": config.duration_seconds,
                    "concurrent_users": config.concurrent_users,
                    "warmup_seconds": config.warmup_seconds
                },
                "results": {name: self._serialize_result(result) for name, result in results.items()},
                "analysis": analysis,
                "recommendations": self._generate_recommendations(results, analysis)
            }
            
        except Exception as e:
            logger.error(f"Benchmark suite error: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "partial_results": {name: self._serialize_result(result) for name, result in results.items()}
            }

    def _serialize_result(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Convert BenchmarkResult to serializable dictionary."""
        return {
            "test_name": result.test_name,
            "duration_seconds": result.duration_seconds,
            "operations_count": result.operations_count,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "avg_response_time": result.avg_response_time,
            "p95_response_time": result.p95_response_time,
            "p99_response_time": result.p99_response_time,
            "throughput_ops_per_second": result.throughput_ops_per_second,
            "error_rate": result.error_rate,
            "memory_usage_mb": result.memory_usage_mb,
            "cpu_usage_percent": result.cpu_usage_percent,
            "additional_metrics": result.additional_metrics
        }

    def _analyze_benchmark_results(self, results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
        """Analyze benchmark results and provide insights."""
        
        analysis = {
            "performance_summary": {},
            "bottlenecks": [],
            "strengths": [],
            "comparisons": {}
        }
        
        # Performance targets (from requirements)
        targets = {
            "max_response_time": 0.5,  # 500ms for immediate calculations
            "min_throughput": 100,     # 100 ops/second minimum
            "max_error_rate": 0.05,    # 5% error rate maximum
            "min_success_rate": 0.95   # 95% success rate minimum
        }
        
        for name, result in results.items():
            # Check against targets
            meets_response_time = result.p95_response_time <= targets["max_response_time"]
            meets_throughput = result.throughput_ops_per_second >= targets["min_throughput"]
            meets_error_rate = result.error_rate <= targets["max_error_rate"]
            
            analysis["performance_summary"][name] = {
                "meets_response_time_target": meets_response_time,
                "meets_throughput_target": meets_throughput, 
                "meets_error_rate_target": meets_error_rate,
                "overall_score": self._calculate_performance_score(result, targets)
            }
            
            # Identify bottlenecks
            if not meets_response_time:
                analysis["bottlenecks"].append(f"{name}: High response time ({result.p95_response_time:.3f}s)")
            
            if not meets_throughput:
                analysis["bottlenecks"].append(f"{name}: Low throughput ({result.throughput_ops_per_second:.1f} ops/s)")
            
            if not meets_error_rate:
                analysis["bottlenecks"].append(f"{name}: High error rate ({result.error_rate:.2%})")
            
            # Identify strengths
            if meets_response_time and meets_throughput and meets_error_rate:
                analysis["strengths"].append(f"{name}: Meets all performance targets")
        
        # Compare authentication methods
        if "auth_api_key" in results and "auth_jwt" in results:
            api_key_result = results["auth_api_key"]
            jwt_result = results["auth_jwt"]
            
            analysis["comparisons"]["auth_methods"] = {
                "api_key_faster": api_key_result.avg_response_time < jwt_result.avg_response_time,
                "api_key_throughput": api_key_result.throughput_ops_per_second,
                "jwt_throughput": jwt_result.throughput_ops_per_second,
                "performance_difference_percent": (
                    (jwt_result.avg_response_time - api_key_result.avg_response_time) / 
                    api_key_result.avg_response_time * 100
                ) if api_key_result.avg_response_time > 0 else 0
            }
        
        return analysis

    def _calculate_performance_score(self, result: BenchmarkResult, targets: Dict[str, float]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100
        
        # Response time score (30% weight)
        if result.p95_response_time > targets["max_response_time"]:
            response_penalty = min(30, (result.p95_response_time / targets["max_response_time"] - 1) * 30)
            score -= response_penalty
        
        # Throughput score (30% weight)
        if result.throughput_ops_per_second < targets["min_throughput"]:
            throughput_penalty = min(30, (1 - result.throughput_ops_per_second / targets["min_throughput"]) * 30)
            score -= throughput_penalty
        
        # Error rate score (40% weight)
        if result.error_rate > targets["max_error_rate"]:
            error_penalty = min(40, (result.error_rate / targets["max_error_rate"] - 1) * 40)
            score -= error_penalty
        
        return max(0, score)

    def _generate_recommendations(
        self, 
        results: Dict[str, BenchmarkResult], 
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        
        recommendations = []
        
        # Check bottlenecks
        bottlenecks = analysis.get("bottlenecks", [])
        if bottlenecks:
            recommendations.append("Performance bottlenecks detected:")
            recommendations.extend([f"  - {bottleneck}" for bottleneck in bottlenecks])
        
        # Authentication recommendations
        if "auth_api_key" in results:
            auth_result = results["auth_api_key"]
            if auth_result.p95_response_time > 0.1:  # 100ms
                recommendations.append(
                    "API key authentication P95 response time > 100ms. "
                    "Consider caching validated keys or optimizing hash functions."
                )
        
        if "auth_jwt" in results:
            jwt_result = results["auth_jwt"]
            if jwt_result.p95_response_time > 0.2:  # 200ms
                recommendations.append(
                    "JWT validation P95 response time > 200ms. "
                    "Consider caching public keys or using faster signature algorithms."
                )
        
        # Rate limiting recommendations
        if "rate_limit_token_bucket" in results:
            rate_result = results["rate_limit_token_bucket"]
            if rate_result.p95_response_time > 0.01:  # 10ms
                recommendations.append(
                    "Rate limiting P95 response time > 10ms. "
                    "Consider optimizing data structures or reducing lock contention."
                )
        
        # Error recovery recommendations
        if "error_recovery_retry" in results:
            retry_result = results["error_recovery_retry"]
            recovery_rate = retry_result.additional_metrics.get("recovery_success_rate", 0)
            if recovery_rate < 0.8:  # 80%
                recommendations.append(
                    f"Error recovery success rate is {recovery_rate:.2%}. "
                    "Consider adjusting retry strategies or circuit breaker thresholds."
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append("All performance metrics meet targets. System is optimized.")
        else:
            recommendations.append(
                "Consider implementing performance monitoring dashboards to track these metrics continuously."
            )
        
        return recommendations

    async def run_stress_test(self, max_concurrent_users: int = 100) -> Dict[str, Any]:
        """Run stress test to find system limits."""
        
        logger.info(f"Starting stress test with up to {max_concurrent_users} concurrent users")
        
        stress_results = []
        
        # Test with increasing concurrent users
        user_counts = [1, 5, 10, 20, 50, 100]
        user_counts = [u for u in user_counts if u <= max_concurrent_users]
        
        for user_count in user_counts:
            logger.info(f"Testing with {user_count} concurrent users")
            
            config = BenchmarkConfig(
                duration_seconds=20,
                concurrent_users=user_count,
                warmup_seconds=2
            )
            
            # Test authentication performance under load
            result = await self.auth_benchmark.benchmark_api_key_validation(config)
            
            stress_results.append({
                "concurrent_users": user_count,
                "throughput": result.throughput_ops_per_second,
                "avg_response_time": result.avg_response_time,
                "p95_response_time": result.p95_response_time,
                "error_rate": result.error_rate
            })
            
            # Stop if error rate becomes too high
            if result.error_rate > 0.1:  # 10% error rate
                logger.warning(f"High error rate at {user_count} users, stopping stress test")
                break
        
        # Find optimal concurrency
        optimal_users = self._find_optimal_concurrency(stress_results)
        
        return {
            "stress_test_results": stress_results,
            "optimal_concurrent_users": optimal_users,
            "max_throughput": max(r["throughput"] for r in stress_results) if stress_results else 0,
            "recommendations": self._generate_stress_test_recommendations(stress_results)
        }

    def _find_optimal_concurrency(self, stress_results: List[Dict[str, Any]]) -> int:
        """Find optimal concurrency level based on throughput and response time."""
        
        if not stress_results:
            return 1
        
        # Find the point where throughput is maximized while keeping response time reasonable
        best_score = 0
        optimal_users = 1
        
        for result in stress_results:
            # Score based on throughput and response time
            throughput_score = result["throughput"] / 1000  # Normalize
            response_time_penalty = result["p95_response_time"] * 10  # Penalize high response times
            error_penalty = result["error_rate"] * 100  # Heavily penalize errors
            
            score = throughput_score - response_time_penalty - error_penalty
            
            if score > best_score:
                best_score = score
                optimal_users = result["concurrent_users"]
        
        return optimal_users

    def _generate_stress_test_recommendations(self, stress_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on stress test results."""
        
        recommendations = []
        
        if not stress_results:
            return ["Unable to generate recommendations - no stress test data"]
        
        max_throughput = max(r["throughput"] for r in stress_results)
        optimal_users = self._find_optimal_concurrency(stress_results)
        
        recommendations.append(f"Optimal concurrency level: {optimal_users} users")
        recommendations.append(f"Maximum throughput achieved: {max_throughput:.1f} ops/second")
        
        # Check for performance degradation
        first_result = stress_results[0]
        last_result = stress_results[-1]
        
        if last_result["p95_response_time"] > first_result["p95_response_time"] * 2:
            recommendations.append(
                "Response time degrades significantly under load. "
                "Consider implementing connection pooling or load balancing."
            )
        
        if last_result["error_rate"] > 0.05:
            recommendations.append(
                "Error rate increases under load. "
                "Consider implementing backpressure or graceful degradation."
            )
        
        return recommendations


# Global benchmark suite instance
benchmark_suite = PerformanceBenchmarkSuite()


def get_benchmark_suite() -> PerformanceBenchmarkSuite:
    """Get the performance benchmark suite instance."""
    return benchmark_suite