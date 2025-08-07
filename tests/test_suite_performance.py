#!/usr/bin/env python3
"""
Performance and Load Testing Suite for OFC Solver API
Validates system performance under various load conditions.
Tests response times, throughput, concurrency, and system stability.
"""

import asyncio
import aiohttp
import time
import statistics
import concurrent.futures
import json
import psutil
import gc
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

# Performance test configuration
PERFORMANCE_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_base": "http://localhost:8000/api/v1",
    "demo_api_key": "ofc-solver-demo-key-2024",
    "test_timeout": 60,
    "max_concurrent_users": 100,
    "performance_targets": {
        "max_response_time": 0.2,  # 200ms (better than 500ms requirement)
        "min_throughput": 100,     # 100 requests/second
        "max_error_rate": 0.05,    # 5% error rate
        "min_success_rate": 0.95   # 95% success rate
    }
}


@dataclass
class PerformanceMetrics:
    """Performance test metrics."""
    test_name: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float


@dataclass
class LoadTestResult:
    """Load test result."""
    concurrent_users: int
    metrics: PerformanceMetrics
    system_stable: bool
    meets_targets: bool


class PerformanceTestSuite:
    """
    Comprehensive performance testing suite.
    Tests system under various load conditions.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or PERFORMANCE_CONFIG
        self.results: List[PerformanceMetrics] = []
        
    def measure_system_resources(self) -> Tuple[float, float]:
        """Measure current system resource usage."""
        try:
            memory_mb = psutil.virtual_memory().used / (1024 * 1024)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return memory_mb, cpu_percent
        except Exception:
            return 0.0, 0.0

    async def single_api_request(self, session: aiohttp.ClientSession, endpoint: str, 
                                method: str = "GET", payload: Dict = None) -> Tuple[float, bool]:
        """Make a single API request and measure response time."""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"ApiKey {self.config['demo_api_key']}",
                "Content-Type": "application/json"
            }
            
            if method.upper() == "GET":
                async with session.get(endpoint, headers=headers) as response:
                    await response.text()
                    success = 200 <= response.status < 300
            else:
                async with session.post(endpoint, json=payload, headers=headers) as response:
                    await response.text()
                    success = 200 <= response.status < 300
                    
            duration = time.time() - start_time
            return duration, success
            
        except Exception as e:
            duration = time.time() - start_time
            logger.debug(f"Request failed: {e}")
            return duration, False

    async def run_concurrent_load_test(self, concurrent_users: int, 
                                     duration_seconds: int = 30,
                                     endpoint: str = None) -> PerformanceMetrics:
        """Run concurrent load test with specified number of users."""
        
        if endpoint is None:
            endpoint = f"{self.config['api_base']}/analysis/statistics"
        
        print(f"🔥 Load Test: {concurrent_users} concurrent users for {duration_seconds}s")
        
        # Track metrics
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Initial system resources
        initial_memory, initial_cpu = self.measure_system_resources()
        
        # Create session with connection pool
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=self.config['test_timeout'])
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            async def user_session():
                """Simulate a single user's request pattern."""
                nonlocal success_count, failure_count
                
                while time.time() < end_time:
                    duration, success = await self.single_api_request(session, endpoint)
                    response_times.append(duration)
                    
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    # Small delay between requests (realistic user behavior)
                    await asyncio.sleep(0.1)
            
            # Launch concurrent user sessions
            tasks = [user_session() for _ in range(concurrent_users)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate final metrics
        test_duration = time.time() - start_time
        total_requests = success_count + failure_count
        
        # Final system resources
        final_memory, final_cpu = self.measure_system_resources()
        
        if response_times:
            response_times.sort()
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Percentiles
            p50_idx = int(0.50 * len(response_times))
            p95_idx = int(0.95 * len(response_times))
            p99_idx = int(0.99 * len(response_times))
            
            p50_response_time = response_times[p50_idx]
            p95_response_time = response_times[p95_idx]
            p99_response_time = response_times[p99_idx]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p95_response_time = p99_response_time = 0
        
        throughput = total_requests / test_duration if test_duration > 0 else 0
        error_rate = failure_count / total_requests if total_requests > 0 else 0
        
        return PerformanceMetrics(
            test_name=f"Load Test - {concurrent_users} users",
            duration=test_duration,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage_mb=final_memory,
            cpu_usage_percent=final_cpu
        )

    async def test_strategy_calculation_performance(self) -> PerformanceMetrics:
        """Test performance of strategy calculation under load."""
        
        print("🧠 Testing Strategy Calculation Performance")
        
        endpoint = f"{self.config['api_base']}/analysis/calculate-strategy"
        payload = {
            "position": {
                "players_hands": {
                    "player_1": {
                        "front": ["As", "Kh"],
                        "middle": ["Qd", "Jc", "Ts"],
                        "back": ["9h", "8d", "7c", "6s", "5h"]
                    }
                },
                "remaining_cards": ["2h", "3c", "4d"],
                "current_player": 0,
                "round_number": 2
            },
            "calculation_mode": "instant",
            "max_calculation_time_seconds": 5
        }
        
        # Test with moderate concurrency for CPU-intensive operations
        concurrent_users = 10
        duration_seconds = 20
        
        response_times = []
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            async def calculate_strategy():
                nonlocal success_count, failure_count
                duration, success = await self.single_api_request(
                    session, endpoint, "POST", payload
                )
                response_times.append(duration)
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            
            # Run concurrent strategy calculations
            tasks = [calculate_strategy() for _ in range(concurrent_users * 5)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        total_requests = success_count + failure_count
        
        if response_times:
            response_times.sort()
            avg_response_time = statistics.mean(response_times)
            p95_response_time = response_times[int(0.95 * len(response_times))]
            p99_response_time = response_times[int(0.99 * len(response_times))]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        throughput = total_requests / test_duration if test_duration > 0 else 0
        error_rate = failure_count / total_requests if total_requests > 0 else 0
        memory_mb, cpu_percent = self.measure_system_resources()
        
        return PerformanceMetrics(
            test_name="Strategy Calculation Performance",
            duration=test_duration,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            avg_response_time=avg_response_time,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p50_response_time=response_times[int(0.50 * len(response_times))] if response_times else 0,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent
        )

    async def run_stress_test(self) -> List[LoadTestResult]:
        """Run progressive stress test to find system limits."""
        
        print("💪 Running Progressive Stress Test")
        print("-" * 40)
        
        stress_results = []
        user_counts = [1, 5, 10, 20, 50, 75, 100]
        
        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")
            
            # Run load test
            metrics = await self.run_concurrent_load_test(
                concurrent_users=user_count,
                duration_seconds=15  # Shorter duration for stress test
            )
            
            # Check if system is stable
            targets = self.config['performance_targets']
            system_stable = (
                metrics.error_rate < 0.1 and  # Less than 10% errors
                metrics.p95_response_time < 2.0  # Less than 2 seconds P95
            )
            
            meets_targets = (
                metrics.p95_response_time <= targets['max_response_time'] and
                metrics.throughput >= targets['min_throughput'] and
                metrics.error_rate <= targets['max_error_rate']
            )
            
            result = LoadTestResult(
                concurrent_users=user_count,
                metrics=metrics,
                system_stable=system_stable,
                meets_targets=meets_targets
            )
            
            stress_results.append(result)
            
            print(f"  📊 Throughput: {metrics.throughput:.1f} req/s")
            print(f"  ⏱️  P95 Response: {metrics.p95_response_time*1000:.0f}ms")
            print(f"  ❌ Error Rate: {metrics.error_rate:.2%}")
            print(f"  🎯 Meets Targets: {'✅' if meets_targets else '❌'}")
            print(f"  🔧 System Stable: {'✅' if system_stable else '❌'}")
            
            # Stop if system becomes unstable
            if not system_stable:
                print(f"  ⚠️  System unstable at {user_count} users, stopping stress test")
                break
            
            # Cleanup between tests
            gc.collect()
            await asyncio.sleep(2)
        
        return stress_results

    def analyze_performance_results(self, results: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance test results and generate insights."""
        
        if not results:
            return {"error": "No results to analyze"}
        
        targets = self.config['performance_targets']
        
        analysis = {
            "summary": {
                "total_tests": len(results),
                "avg_response_time": statistics.mean([r.avg_response_time for r in results]),
                "max_throughput": max([r.throughput for r in results]),
                "avg_error_rate": statistics.mean([r.error_rate for r in results]),
                "total_requests": sum([r.total_requests for r in results])
            },
            "performance_assessment": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        # Performance target assessment
        for result in results:
            meets_response_time = result.p95_response_time <= targets['max_response_time']
            meets_throughput = result.throughput >= targets['min_throughput']
            meets_error_rate = result.error_rate <= targets['max_error_rate']
            
            analysis["performance_assessment"][result.test_name] = {
                "meets_response_time_target": meets_response_time,
                "meets_throughput_target": meets_throughput,
                "meets_error_rate_target": meets_error_rate,
                "overall_score": self._calculate_performance_score(result, targets)
            }
            
            # Identify bottlenecks
            if not meets_response_time:
                analysis["bottlenecks"].append(
                    f"{result.test_name}: High response time (P95: {result.p95_response_time*1000:.0f}ms)"
                )
            
            if not meets_throughput:
                analysis["bottlenecks"].append(
                    f"{result.test_name}: Low throughput ({result.throughput:.1f} req/s)"
                )
            
            if not meets_error_rate:
                analysis["bottlenecks"].append(
                    f"{result.test_name}: High error rate ({result.error_rate:.2%})"
                )
        
        # Generate recommendations
        avg_response_time = analysis["summary"]["avg_response_time"]
        max_throughput = analysis["summary"]["max_throughput"]
        avg_error_rate = analysis["summary"]["avg_error_rate"]
        
        if avg_response_time > targets['max_response_time']:
            analysis["recommendations"].append(
                "Consider optimizing slow endpoints or adding caching"
            )
        
        if max_throughput < targets['min_throughput']:
            analysis["recommendations"].append(
                "Consider horizontal scaling or connection pool optimization"
            )
        
        if avg_error_rate > targets['max_error_rate']:
            analysis["recommendations"].append(
                "Investigate error causes and improve error handling"
            )
        
        if not analysis["recommendations"]:
            analysis["recommendations"].append(
                "Performance meets all targets - system is well optimized"
            )
        
        return analysis

    def _calculate_performance_score(self, metrics: PerformanceMetrics, 
                                   targets: Dict[str, float]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100
        
        # Response time score (40% weight)
        if metrics.p95_response_time > targets['max_response_time']:
            penalty = min(40, (metrics.p95_response_time / targets['max_response_time'] - 1) * 40)
            score -= penalty
        
        # Throughput score (30% weight)
        if metrics.throughput < targets['min_throughput']:
            penalty = min(30, (1 - metrics.throughput / targets['min_throughput']) * 30)
            score -= penalty
        
        # Error rate score (30% weight)
        if metrics.error_rate > targets['max_error_rate']:
            penalty = min(30, (metrics.error_rate / targets['max_error_rate'] - 1) * 30)
            score -= penalty
        
        return max(0, score)

    async def run_comprehensive_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance testing suite."""
        
        print("🚀 Running Comprehensive Performance Test Suite")
        print("=" * 60)
        
        test_start_time = time.time()
        
        try:
            # 1. Strategy calculation performance test
            strategy_metrics = await self.test_strategy_calculation_performance()
            self.results.append(strategy_metrics)
            
            # 2. Progressive load testing
            print(f"\n📈 Progressive Load Testing")
            print("-" * 30)
            
            load_tests = [5, 10, 25, 50]  # Reasonable progression
            for user_count in load_tests:
                metrics = await self.run_concurrent_load_test(
                    concurrent_users=user_count,
                    duration_seconds=20
                )
                self.results.append(metrics)
            
            # 3. Stress testing
            print(f"\n💪 Stress Testing")
            print("-" * 30)
            stress_results = await self.run_stress_test()
            
            # 4. Performance analysis
            print(f"\n📊 Performance Analysis")
            print("-" * 30)
            analysis = self.analyze_performance_results(self.results)
            
            total_duration = time.time() - test_start_time
            
            # Generate comprehensive report
            report = {
                "test_suite": "comprehensive_performance",
                "timestamp": datetime.now().isoformat(),
                "duration": total_duration,
                "metrics": [asdict(metric) for metric in self.results],
                "stress_test_results": [asdict(result) for result in stress_results],
                "analysis": analysis,
                "performance_targets": self.config['performance_targets'],
                "summary": {
                    "total_tests": len(self.results),
                    "total_requests": sum(r.total_requests for r in self.results),
                    "max_concurrent_users_stable": self._find_max_stable_users(stress_results),
                    "performance_score": self._calculate_overall_score(analysis)
                }
            }
            
            print(f"\n✅ Performance testing completed in {total_duration:.2f}s")
            return report
            
        except Exception as e:
            logger.error(f"Performance test suite error: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "partial_results": [asdict(metric) for metric in self.results]
            }

    def _find_max_stable_users(self, stress_results: List[LoadTestResult]) -> int:
        """Find maximum number of stable concurrent users."""
        stable_results = [r for r in stress_results if r.system_stable]
        return max(r.concurrent_users for r in stable_results) if stable_results else 0

    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        assessments = analysis.get("performance_assessment", {})
        if not assessments:
            return 0
        
        scores = [data.get("overall_score", 0) for data in assessments.values()]
        return statistics.mean(scores) if scores else 0

    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable performance report."""
        
        report = f"""
# Performance Test Report

Generated: {results.get('timestamp', 'Unknown')}
Duration: {results.get('duration', 0):.2f} seconds

## Summary
- Total Tests: {results['summary']['total_tests']}
- Total Requests: {results['summary']['total_requests']:,}
- Max Stable Users: {results['summary']['max_concurrent_users_stable']}
- Performance Score: {results['summary']['performance_score']:.1f}/100

## Key Findings
"""
        
        analysis = results.get('analysis', {})
        summary = analysis.get('summary', {})
        
        report += f"""
- Average Response Time: {summary.get('avg_response_time', 0)*1000:.2f}ms
- Maximum Throughput: {summary.get('max_throughput', 0):.1f} req/s
- Average Error Rate: {summary.get('avg_error_rate', 0):.2%}
"""
        
        # Performance targets assessment
        targets = results.get('performance_targets', {})
        meets_response_target = summary.get('avg_response_time', 1) <= targets.get('max_response_time', 0.2)
        meets_throughput_target = summary.get('max_throughput', 0) >= targets.get('min_throughput', 100)
        meets_error_target = summary.get('avg_error_rate', 1) <= targets.get('max_error_rate', 0.05)
        
        report += f"""
## Performance Targets
- Response Time (<{targets.get('max_response_time', 0.2)*1000:.0f}ms): {'✅ PASS' if meets_response_target else '❌ FAIL'}
- Throughput (>{targets.get('min_throughput', 100)} req/s): {'✅ PASS' if meets_throughput_target else '❌ FAIL'}
- Error Rate (<{targets.get('max_error_rate', 0.05):.1%}): {'✅ PASS' if meets_error_target else '❌ FAIL'}
"""
        
        # Bottlenecks
        bottlenecks = analysis.get('bottlenecks', [])
        if bottlenecks:
            report += "\n## Identified Bottlenecks\n"
            for bottleneck in bottlenecks:
                report += f"- {bottleneck}\n"
        
        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            report += "\n## Recommendations\n"
            for rec in recommendations:
                report += f"- {rec}\n"
        
        return report


async def main():
    """Main execution function."""
    test_suite = PerformanceTestSuite()
    
    # Run comprehensive performance tests
    results = await test_suite.run_comprehensive_performance_tests()
    
    # Generate and display report
    report_text = test_suite.generate_performance_report(results)
    print(report_text)
    
    # Save results
    with open("performance_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    with open("performance_test_report.md", "w") as f:
        f.write(report_text)
    
    print(f"\n📄 Results saved to:")
    print(f"  - performance_test_results.json")
    print(f"  - performance_test_report.md")
    
    # Determine success
    overall_score = results.get('summary', {}).get('performance_score', 0)
    success = overall_score >= 75  # 75% threshold for success
    
    if success:
        print("\n🎉 Performance tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  Performance tests need attention (Score: {overall_score:.1f}/100)")
        return 1


if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)