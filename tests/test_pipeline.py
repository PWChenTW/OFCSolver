#!/usr/bin/env python3
"""
Automated Testing Pipeline for OFC Solver API
Orchestrates all test suites and implements quality gates.
Designed for CI/CD integration with comprehensive reporting.
"""

import asyncio
import subprocess
import sys
import time
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# Import test suites
from test_suite_core import CoreAPITestSuite
from test_suite_performance import PerformanceTestSuite
from test_suite_security import SecurityTestSuite

logger = logging.getLogger(__name__)

# Pipeline configuration
PIPELINE_CONFIG = {
    "quality_gates": {
        "core_tests": {
            "min_success_rate": 100,  # All core tests must pass
            "max_avg_response_time": 0.5,  # 500ms
            "required": True
        },
        "performance_tests": {
            "min_performance_score": 75,  # 75/100
            "max_p95_response_time": 0.2,  # 200ms
            "min_throughput": 100,  # req/s
            "required": True
        },
        "security_tests": {
            "min_security_score": 80,  # 80/100
            "max_critical_issues": 0,  # No critical vulnerabilities
            "max_high_issues": 2,  # Max 2 high-severity issues
            "required": True
        }
    },
    "timeout_seconds": 1800,  # 30 minutes total
    "retry_attempts": 2,
    "server_startup_wait": 30,
    "output_dir": "test_results"
}


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    success: bool
    duration: float
    score: float
    details: Dict[str, Any]
    error_message: str = ""


@dataclass
class QualityGateResult:
    """Quality gate evaluation result."""
    gate_name: str
    passed: bool
    requirements: Dict[str, Any]
    actual_values: Dict[str, Any]
    failure_reasons: List[str]


class TestPipeline:
    """
    Comprehensive testing pipeline orchestrator.
    Manages test execution, quality gates, and reporting.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or PIPELINE_CONFIG
        self.results: List[TestSuiteResult] = []
        self.quality_gates: List[QualityGateResult] = []
        self.start_time = None
        self.end_time = None
        
        # Ensure output directory exists
        os.makedirs(self.config['output_dir'], exist_ok=True)

    def check_server_health(self) -> bool:
        """Check if the API server is running and healthy."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def wait_for_server(self, max_wait: int = None) -> bool:
        """Wait for server to be ready."""
        max_wait = max_wait or self.config['server_startup_wait']
        print(f"⏳ Waiting for server to be ready (max {max_wait}s)...")
        
        for i in range(max_wait):
            if self.check_server_health():
                print(f"✅ Server is ready after {i+1}s")
                return True
            time.sleep(1)
            
        print(f"❌ Server not ready after {max_wait}s")
        return False

    def start_server_if_needed(self) -> bool:
        """Start the API server if it's not running."""
        if self.check_server_health():
            print("✅ Server is already running")
            return True
        
        print("🚀 Starting API server...")
        try:
            # Try to start the server in background
            subprocess.Popen([
                sys.executable, "src/main.py"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return self.wait_for_server()
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    async def run_core_test_suite(self) -> TestSuiteResult:
        """Execute core functionality tests."""
        print("\n" + "="*60)
        print("🎯 RUNNING CORE TEST SUITE")
        print("="*60)
        
        start_time = time.time()
        
        try:
            core_suite = CoreAPITestSuite()
            results = core_suite.run_core_test_suite()
            
            duration = time.time() - start_time
            
            # Calculate score based on success rate and performance
            success_rate = results['summary']['success_rate']
            performance_rate = results['summary']['performance_rate']
            score = (success_rate * 0.7) + (performance_rate * 0.3)  # Weighted score
            
            return TestSuiteResult(
                suite_name="Core API Tests",
                success=results['status'] == "PASS",
                duration=duration,
                score=score,
                details=results
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Core test suite error: {e}", exc_info=True)
            
            return TestSuiteResult(
                suite_name="Core API Tests",
                success=False,
                duration=duration,
                score=0,
                details={},
                error_message=str(e)
            )

    async def run_performance_test_suite(self) -> TestSuiteResult:
        """Execute performance and load tests."""
        print("\n" + "="*60)
        print("⚡ RUNNING PERFORMANCE TEST SUITE")
        print("="*60)
        
        start_time = time.time()
        
        try:
            perf_suite = PerformanceTestSuite()
            results = await perf_suite.run_comprehensive_performance_tests()
            
            duration = time.time() - start_time
            
            # Get performance score
            score = results.get('summary', {}).get('performance_score', 0)
            
            return TestSuiteResult(
                suite_name="Performance Tests",
                success='error' not in results,
                duration=duration,
                score=score,
                details=results
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Performance test suite error: {e}", exc_info=True)
            
            return TestSuiteResult(
                suite_name="Performance Tests",
                success=False,
                duration=duration,
                score=0,
                details={},
                error_message=str(e)
            )

    async def run_security_test_suite(self) -> TestSuiteResult:
        """Execute security tests."""
        print("\n" + "="*60)
        print("🔒 RUNNING SECURITY TEST SUITE")
        print("="*60)
        
        start_time = time.time()
        
        try:
            security_suite = SecurityTestSuite()
            results = await security_suite.run_comprehensive_security_tests()
            
            duration = time.time() - start_time
            
            # Get security score
            score = results.get('assessment', {}).get('security_score', 0)
            
            return TestSuiteResult(
                suite_name="Security Tests",
                success='error' not in results,
                duration=duration,
                score=score,
                details=results
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Security test suite error: {e}", exc_info=True)
            
            return TestSuiteResult(
                suite_name="Security Tests",
                success=False,
                duration=duration,
                score=0,
                details={},
                error_message=str(e)
            )

    def evaluate_quality_gates(self) -> List[QualityGateResult]:
        """Evaluate all quality gates based on test results."""
        gate_results = []
        
        # Find results by suite name
        core_result = next((r for r in self.results if "Core" in r.suite_name), None)
        perf_result = next((r for r in self.results if "Performance" in r.suite_name), None)
        security_result = next((r for r in self.results if "Security" in r.suite_name), None)
        
        # Evaluate core tests gate
        if core_result:
            gate_results.append(self._evaluate_core_gate(core_result))
        
        # Evaluate performance gate
        if perf_result:
            gate_results.append(self._evaluate_performance_gate(perf_result))
        
        # Evaluate security gate
        if security_result:
            gate_results.append(self._evaluate_security_gate(security_result))
        
        return gate_results

    def _evaluate_core_gate(self, result: TestSuiteResult) -> QualityGateResult:
        """Evaluate core tests quality gate."""
        gate_config = self.config['quality_gates']['core_tests']
        requirements = {
            "min_success_rate": gate_config['min_success_rate'],
            "max_avg_response_time": gate_config['max_avg_response_time']
        }
        
        if not result.success:
            return QualityGateResult(
                gate_name="Core Tests",
                passed=False,
                requirements=requirements,
                actual_values={},
                failure_reasons=["Core test suite failed to execute"]
            )
        
        summary = result.details.get('summary', {})
        actual_values = {
            "success_rate": summary.get('success_rate', 0),
            "avg_response_time": summary.get('avg_response_time', 999)
        }
        
        failure_reasons = []
        
        if actual_values['success_rate'] < requirements['min_success_rate']:
            failure_reasons.append(
                f"Success rate {actual_values['success_rate']:.1f}% < {requirements['min_success_rate']}%"
            )
        
        if actual_values['avg_response_time'] > requirements['max_avg_response_time']:
            failure_reasons.append(
                f"Avg response time {actual_values['avg_response_time']*1000:.0f}ms > {requirements['max_avg_response_time']*1000:.0f}ms"
            )
        
        return QualityGateResult(
            gate_name="Core Tests",
            passed=len(failure_reasons) == 0,
            requirements=requirements,
            actual_values=actual_values,
            failure_reasons=failure_reasons
        )

    def _evaluate_performance_gate(self, result: TestSuiteResult) -> QualityGateResult:
        """Evaluate performance tests quality gate."""
        gate_config = self.config['quality_gates']['performance_tests']
        requirements = {
            "min_performance_score": gate_config['min_performance_score'],
            "max_p95_response_time": gate_config['max_p95_response_time'],
            "min_throughput": gate_config['min_throughput']
        }
        
        if not result.success:
            return QualityGateResult(
                gate_name="Performance Tests",
                passed=False,
                requirements=requirements,
                actual_values={},
                failure_reasons=["Performance test suite failed to execute"]
            )
        
        summary = result.details.get('summary', {})
        analysis = result.details.get('analysis', {}).get('summary', {})
        
        actual_values = {
            "performance_score": result.score,
            "max_throughput": analysis.get('max_throughput', 0),
            "avg_response_time": analysis.get('avg_response_time', 999)
        }
        
        failure_reasons = []
        
        if actual_values['performance_score'] < requirements['min_performance_score']:
            failure_reasons.append(
                f"Performance score {actual_values['performance_score']:.1f} < {requirements['min_performance_score']}"
            )
        
        if actual_values['avg_response_time'] > requirements['max_p95_response_time']:
            failure_reasons.append(
                f"Avg response time {actual_values['avg_response_time']*1000:.0f}ms > {requirements['max_p95_response_time']*1000:.0f}ms"
            )
        
        if actual_values['max_throughput'] < requirements['min_throughput']:
            failure_reasons.append(
                f"Max throughput {actual_values['max_throughput']:.1f} req/s < {requirements['min_throughput']} req/s"
            )
        
        return QualityGateResult(
            gate_name="Performance Tests",
            passed=len(failure_reasons) == 0,
            requirements=requirements,
            actual_values=actual_values,
            failure_reasons=failure_reasons
        )

    def _evaluate_security_gate(self, result: TestSuiteResult) -> QualityGateResult:
        """Evaluate security tests quality gate."""
        gate_config = self.config['quality_gates']['security_tests']
        requirements = {
            "min_security_score": gate_config['min_security_score'],
            "max_critical_issues": gate_config['max_critical_issues'],
            "max_high_issues": gate_config['max_high_issues']
        }
        
        if not result.success:
            return QualityGateResult(
                gate_name="Security Tests",
                passed=False,
                requirements=requirements,
                actual_values={},
                failure_reasons=["Security test suite failed to execute"]
            )
        
        assessment = result.details.get('assessment', {})
        vuln_breakdown = assessment.get('vulnerability_breakdown', {})
        
        actual_values = {
            "security_score": result.score,
            "critical_issues": vuln_breakdown.get('CRITICAL', 0),
            "high_issues": vuln_breakdown.get('HIGH', 0)
        }
        
        failure_reasons = []
        
        if actual_values['security_score'] < requirements['min_security_score']:
            failure_reasons.append(
                f"Security score {actual_values['security_score']:.1f} < {requirements['min_security_score']}"
            )
        
        if actual_values['critical_issues'] > requirements['max_critical_issues']:
            failure_reasons.append(
                f"Critical issues {actual_values['critical_issues']} > {requirements['max_critical_issues']}"
            )
        
        if actual_values['high_issues'] > requirements['max_high_issues']:
            failure_reasons.append(
                f"High severity issues {actual_values['high_issues']} > {requirements['max_high_issues']}"
            )
        
        return QualityGateResult(
            gate_name="Security Tests",
            passed=len(failure_reasons) == 0,
            requirements=requirements,
            actual_values=actual_values,
            failure_reasons=failure_reasons
        )

    def save_results(self):
        """Save all test results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual suite results
        for result in self.results:
            suite_filename = f"{result.suite_name.lower().replace(' ', '_')}_{timestamp}.json"
            filepath = Path(self.config['output_dir']) / suite_filename
            
            with open(filepath, 'w') as f:
                json.dump(result.details, f, indent=2, default=str)
        
        # Save overall pipeline results
        pipeline_result = {
            "pipeline_execution": {
                "timestamp": datetime.now().isoformat(),
                "duration": self.end_time - self.start_time if self.end_time and self.start_time else 0,
                "success": all(gate.passed for gate in self.quality_gates)
            },
            "test_suites": [asdict(result) for result in self.results],
            "quality_gates": [asdict(gate) for gate in self.quality_gates],
            "configuration": self.config
        }
        
        pipeline_filepath = Path(self.config['output_dir']) / f"pipeline_results_{timestamp}.json"
        with open(pipeline_filepath, 'w') as f:
            json.dump(pipeline_result, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {self.config['output_dir']}/")

    def generate_summary_report(self) -> str:
        """Generate executive summary report."""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        passed_gates = sum(1 for gate in self.quality_gates if gate.passed)
        total_gates = len(self.quality_gates)
        
        report = f"""
# Test Pipeline Execution Report

**Execution Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Duration**: {total_duration:.2f} seconds
**Quality Gates**: {passed_gates}/{total_gates} passed

## Test Suite Results
"""
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report += f"- **{result.suite_name}**: {status} (Score: {result.score:.1f}/100, Duration: {result.duration:.2f}s)\n"
            if result.error_message:
                report += f"  - Error: {result.error_message}\n"
        
        report += "\n## Quality Gate Evaluation\n"
        
        for gate in self.quality_gates:
            status = "✅ PASSED" if gate.passed else "❌ FAILED"
            report += f"- **{gate.gate_name}**: {status}\n"
            
            if gate.failure_reasons:
                report += "  - Failures:\n"
                for reason in gate.failure_reasons:
                    report += f"    - {reason}\n"
        
        # Overall assessment
        all_passed = all(gate.passed for gate in self.quality_gates)
        
        report += f"\n## Overall Assessment\n"
        
        if all_passed:
            report += "🎉 **ALL QUALITY GATES PASSED** - System is ready for deployment!\n"
        else:
            report += "⚠️ **QUALITY GATES FAILED** - Issues must be resolved before deployment.\n"
            
            # Critical issues summary
            critical_issues = []
            for gate in self.quality_gates:
                if not gate.passed:
                    critical_issues.extend(gate.failure_reasons)
            
            if critical_issues:
                report += "\n### Critical Issues to Address:\n"
                for issue in critical_issues:
                    report += f"- {issue}\n"
        
        return report

    async def run_full_pipeline(self) -> bool:
        """Execute the complete testing pipeline."""
        print("🚀 STARTING COMPREHENSIVE TEST PIPELINE")
        print("=" * 80)
        
        self.start_time = time.time()
        
        try:
            # Step 1: Ensure server is running
            if not self.start_server_if_needed():
                print("❌ Cannot start API server. Pipeline aborted.")
                return False
            
            # Step 2: Run all test suites
            print("\n📋 Executing Test Suites...")
            
            # Core tests (critical path)
            core_result = await self.run_core_test_suite()
            self.results.append(core_result)
            
            # If core tests fail completely, consider stopping
            if not core_result.success and core_result.score < 50:
                print("⚠️ Core tests failed badly. Consider fixing before continuing.")
            
            # Performance tests
            perf_result = await self.run_performance_test_suite()
            self.results.append(perf_result)
            
            # Security tests
            security_result = await self.run_security_test_suite()
            self.results.append(security_result)
            
            # Step 3: Evaluate quality gates
            print("\n🚪 Evaluating Quality Gates...")
            self.quality_gates = self.evaluate_quality_gates()
            
            # Step 4: Display results
            self.end_time = time.time()
            self.display_pipeline_summary()
            
            # Step 5: Save results
            self.save_results()
            
            # Step 6: Generate and save report
            report = self.generate_summary_report()
            
            report_file = Path(self.config['output_dir']) / "pipeline_summary_report.md"
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"\n📄 Summary report saved to: {report_file}")
            
            # Return overall success
            return all(gate.passed for gate in self.quality_gates)
            
        except Exception as e:
            self.end_time = time.time()
            logger.error(f"Pipeline execution error: {e}", exc_info=True)
            print(f"❌ Pipeline failed with error: {e}")
            return False

    def display_pipeline_summary(self):
        """Display pipeline execution summary."""
        total_duration = self.end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"🧪 Test Suites: {len(self.results)}")
        print(f"🚪 Quality Gates: {len(self.quality_gates)}")
        
        print("\n📈 Test Suite Performance:")
        print("-" * 40)
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.suite_name}")
            print(f"   Score: {result.score:.1f}/100")
            print(f"   Duration: {result.duration:.2f}s")
            if result.error_message:
                print(f"   Error: {result.error_message}")
        
        print("\n🚪 Quality Gate Results:")
        print("-" * 40)
        for gate in self.quality_gates:
            status = "✅ PASSED" if gate.passed else "❌ FAILED"
            print(f"{status} {gate.gate_name}")
            
            if gate.failure_reasons:
                print("   Issues:")
                for reason in gate.failure_reasons:
                    print(f"   - {reason}")
        
        # Overall result
        all_passed = all(gate.passed for gate in self.quality_gates)
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 PIPELINE SUCCESS - ALL QUALITY GATES PASSED!")
            print("✅ System is ready for production deployment.")
        else:
            print("⚠️  PIPELINE FAILED - QUALITY GATES NOT MET")
            print("❌ Issues must be resolved before deployment.")
        print("=" * 80)


async def main():
    """Main pipeline execution."""
    pipeline = TestPipeline()
    success = await pipeline.run_full_pipeline()
    
    # Exit with appropriate code for CI/CD
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)