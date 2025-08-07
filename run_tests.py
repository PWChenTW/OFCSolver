#!/usr/bin/env python3
"""
Test Runner Script for OFC Solver API
Provides convenient interface for running different test configurations.
Supports local development, CI/CD integration, and production validation.
"""

import asyncio
import argparse
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from tests.test_pipeline import TestPipeline
from tests.test_suite_core import CoreAPITestSuite
from tests.test_suite_performance import PerformanceTestSuite
from tests.test_suite_security import SecurityTestSuite


class TestRunner:
    """
    Main test runner with multiple execution modes.
    Supports different test configurations for various scenarios.
    """

    def __init__(self):
        self.test_configs = {
            "quick": {
                "description": "Quick smoke tests for development",
                "suites": ["core"],
                "core_only": True,
                "timeout": 300  # 5 minutes
            },
            "standard": {
                "description": "Standard test suite for CI/CD",
                "suites": ["core", "performance", "security"],
                "full_pipeline": True,
                "timeout": 1800  # 30 minutes
            },
            "performance": {
                "description": "Performance and load testing focus",
                "suites": ["core", "performance"],
                "extended_performance": True,
                "timeout": 3600  # 1 hour
            },
            "security": {
                "description": "Security vulnerability testing focus",
                "suites": ["core", "security"],
                "extended_security": True,
                "timeout": 1800  # 30 minutes
            },
            "production": {
                "description": "Production readiness validation",
                "suites": ["core", "performance", "security"],
                "strict_quality_gates": True,
                "timeout": 2400  # 40 minutes
            }
        }

    def print_banner(self):
        """Print test runner banner."""
        print("="*80)
        print("🧪 OFC SOLVER API TEST RUNNER")
        print("="*80)
        print("Comprehensive testing suite for REST API implementation")
        print("MVP-focused approach with quality gate enforcement")
        print("="*80)

    def print_config_info(self, config_name: str):
        """Print configuration information."""
        config = self.test_configs[config_name]
        print(f"\n📋 Test Configuration: {config_name.upper()}")
        print("-"*50)
        print(f"Description: {config['description']}")
        print(f"Test Suites: {', '.join(config['suites'])}")
        print(f"Timeout: {config['timeout']} seconds")
        
        if config.get('strict_quality_gates'):
            print("Quality Gates: STRICT (Production-ready)")
        else:
            print("Quality Gates: STANDARD")

    async def run_quick_tests(self) -> bool:
        """Run quick smoke tests for development."""
        print("\n🚀 Running Quick Tests (Development Mode)")
        print("-"*50)
        
        try:
            core_suite = CoreAPITestSuite()
            results = core_suite.run_core_test_suite()
            
            success = results["status"] == "PASS"
            success_rate = results["summary"]["success_rate"]
            
            print(f"\n📊 Quick Test Results:")
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success:
                print("\n🎉 Quick tests passed! Ready for development.")
            else:
                print("\n⚠️  Quick tests failed. Fix core issues before proceeding.")
                
            return success
            
        except Exception as e:
            print(f"❌ Quick test execution failed: {e}")
            return False

    async def run_standard_tests(self) -> bool:
        """Run standard test suite for CI/CD."""
        print("\n🏗️  Running Standard Tests (CI/CD Mode)")
        print("-"*50)
        
        try:
            pipeline = TestPipeline()
            success = await pipeline.run_full_pipeline()
            
            if success:
                print("\n🎉 Standard tests passed! Ready for deployment.")
            else:
                print("\n⚠️  Standard tests failed. Quality gates not met.")
                
            return success
            
        except Exception as e:
            print(f"❌ Standard test execution failed: {e}")
            return False

    async def run_performance_tests(self) -> bool:
        """Run performance-focused tests."""
        print("\n⚡ Running Performance Tests (Load Testing Mode)")
        print("-"*50)
        
        try:
            # Quick core validation first
            core_suite = CoreAPITestSuite()
            core_results = core_suite.run_core_test_suite()
            
            if core_results["status"] != "PASS":
                print("❌ Core tests failed. Skipping performance tests.")
                return False
            
            # Extended performance testing
            perf_suite = PerformanceTestSuite()
            perf_results = await perf_suite.run_comprehensive_performance_tests()
            
            success = 'error' not in perf_results
            score = perf_results.get('summary', {}).get('performance_score', 0)
            
            print(f"\n📊 Performance Test Results:")
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"Performance Score: {score:.1f}/100")
            
            if success and score >= 75:
                print("\n🎉 Performance tests passed! System is performant.")
                return True
            else:
                print("\n⚠️  Performance tests failed. Optimization needed.")
                return False
                
        except Exception as e:
            print(f"❌ Performance test execution failed: {e}")
            return False

    async def run_security_tests(self) -> bool:
        """Run security-focused tests."""
        print("\n🔒 Running Security Tests (Vulnerability Assessment Mode)")
        print("-"*50)
        
        try:
            # Quick core validation first
            core_suite = CoreAPITestSuite()
            core_results = core_suite.run_core_test_suite()
            
            if core_results["status"] != "PASS":
                print("❌ Core tests failed. Skipping security tests.")
                return False
            
            # Extended security testing
            security_suite = SecurityTestSuite()
            security_results = await security_suite.run_comprehensive_security_tests()
            
            success = 'error' not in security_results
            assessment = security_results.get('assessment', {})
            score = assessment.get('security_score', 0)
            critical_issues = assessment.get('vulnerability_breakdown', {}).get('CRITICAL', 0)
            
            print(f"\n📊 Security Test Results:")
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"Security Score: {score:.1f}/100")
            print(f"Critical Issues: {critical_issues}")
            
            if success and score >= 80 and critical_issues == 0:
                print("\n🎉 Security tests passed! System is secure.")
                return True
            else:
                print("\n⚠️  Security tests failed. Vulnerabilities found.")
                return False
                
        except Exception as e:
            print(f"❌ Security test execution failed: {e}")
            return False

    async def run_production_tests(self) -> bool:
        """Run production readiness validation."""
        print("\n🏭 Running Production Tests (Deployment Validation Mode)")
        print("-"*50)
        
        try:
            # Use strict quality gates for production
            strict_config = {
                "quality_gates": {
                    "core_tests": {
                        "min_success_rate": 100,  # All must pass
                        "max_avg_response_time": 0.2,  # 200ms (stricter)
                        "required": True
                    },
                    "performance_tests": {
                        "min_performance_score": 85,  # Higher threshold
                        "max_p95_response_time": 0.15,  # 150ms (stricter)
                        "min_throughput": 150,  # Higher throughput
                        "required": True
                    },
                    "security_tests": {
                        "min_security_score": 90,  # Higher security score
                        "max_critical_issues": 0,  # No critical issues
                        "max_high_issues": 0,  # No high issues either
                        "required": True
                    }
                }
            }
            
            pipeline = TestPipeline(strict_config)
            success = await pipeline.run_full_pipeline()
            
            if success:
                print("\n🎉 Production tests passed! System is production-ready.")
                print("✅ All strict quality gates met.")
            else:
                print("\n⚠️  Production tests failed. System not ready for deployment.")
                print("❌ Strict quality gates not met.")
                
            return success
            
        except Exception as e:
            print(f"❌ Production test execution failed: {e}")
            return False

    async def run_tests(self, config_name: str) -> bool:
        """Run tests based on configuration."""
        if config_name not in self.test_configs:
            print(f"❌ Unknown test configuration: {config_name}")
            return False
        
        self.print_config_info(config_name)
        
        start_time = time.time()
        
        try:
            if config_name == "quick":
                success = await self.run_quick_tests()
            elif config_name == "standard":
                success = await self.run_standard_tests()
            elif config_name == "performance":
                success = await self.run_performance_tests()
            elif config_name == "security":
                success = await self.run_security_tests()
            elif config_name == "production":
                success = await self.run_production_tests()
            else:
                print(f"❌ Test configuration '{config_name}' not implemented")
                return False
            
            duration = time.time() - start_time
            
            print(f"\n⏱️  Total Execution Time: {duration:.2f} seconds")
            
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️  Test execution interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False

    def list_configurations(self):
        """List available test configurations."""
        print("\n📋 Available Test Configurations:")
        print("-"*50)
        
        for name, config in self.test_configs.items():
            print(f"\n🔧 {name.upper()}")
            print(f"   Description: {config['description']}")
            print(f"   Suites: {', '.join(config['suites'])}")
            print(f"   Timeout: {config['timeout']}s")

    def print_help(self):
        """Print help information."""
        print("\n📚 Test Runner Help")
        print("-"*50)
        print("Usage: python run_tests.py [config] [options]")
        print("\nConfigurations:")
        
        for name, config in self.test_configs.items():
            print(f"  {name:<12} - {config['description']}")
        
        print("\nOptions:")
        print("  --list      - List all available configurations")
        print("  --help      - Show this help message")
        print("  --info      - Show detailed configuration info")
        
        print("\nExamples:")
        print("  python run_tests.py quick        # Quick development tests")
        print("  python run_tests.py standard     # Full CI/CD pipeline")
        print("  python run_tests.py production   # Production validation")
        
        print("\nFor CI/CD Integration:")
        print("  - Use 'standard' for regular CI builds")
        print("  - Use 'production' for release validation")
        print("  - Exit codes: 0=success, 1=failure")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OFC Solver API Test Runner",
        add_help=False
    )
    
    parser.add_argument(
        'config',
        nargs='?',
        default='standard',
        help='Test configuration to run'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available configurations'
    )
    
    parser.add_argument(
        '--help',
        action='store_true',
        help='Show help information'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show configuration details'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    runner.print_banner()
    
    if args.help:
        runner.print_help()
        return 0
    
    if args.list:
        runner.list_configurations()
        return 0
    
    if args.info:
        runner.list_configurations()
        print("\n💡 Use --help for usage information")
        return 0
    
    # Run the specified test configuration
    try:
        success = asyncio.run(runner.run_tests(args.config))
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Runner failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())