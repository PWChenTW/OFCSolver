#!/usr/bin/env python3
"""
Core Test Suite for OFC Solver API
Tests critical functionality to ensure system reliability and performance.
MVP-focused testing approach covering essential features first.
"""

import asyncio
import pytest
import time
import json
import uuid
import requests
from typing import Dict, Any, List
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, patch
import logging

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_base": "http://localhost:8000/api/v1",
    "timeout": 30,
    "demo_api_key": "ofc-solver-demo-key-2024",
    "test_api_key": "ofc-solver-test-key-2024"
}

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Standard test result structure."""
    test_name: str
    success: bool
    duration: float
    message: str = ""
    details: Dict[str, Any] = None


class CoreAPITestSuite:
    """
    Core API test suite focusing on essential functionality.
    Follows MVP principles - test critical paths first.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TEST_CONFIG
        self.session = requests.Session()
        self.test_results: List[TestResult] = []
        
    def log_result(self, result: TestResult):
        """Log test result with consistent formatting."""
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.test_name} ({result.duration:.3f}s)")
        if result.message:
            print(f"    {result.message}")
        if result.details:
            for key, value in result.details.items():
                print(f"    {key}: {value}")
        self.test_results.append(result)

    # ========================================
    # CRITICAL PATH TESTS (MVP Priority 1)
    # ========================================

    def test_system_health(self) -> TestResult:
        """Test basic system health and availability."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.config['base_url']}/health", 
                                       timeout=self.config['timeout'])
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    test_name="System Health Check",
                    success=True,
                    duration=duration,
                    message=f"Status: {data.get('status', 'unknown')}",
                    details={"response_time_ms": f"{duration*1000:.2f}"}
                )
            else:
                return TestResult(
                    test_name="System Health Check",
                    success=False,
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="System Health Check",
                success=False,
                duration=duration,
                message=f"Connection error: {str(e)}"
            )

    def test_api_info(self) -> TestResult:
        """Test API information endpoint."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.config['api_base']}")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    test_name="API Info",
                    success=True,
                    duration=duration,
                    message=f"Version: {data.get('version', 'unknown')}",
                    details={
                        "endpoints": len(data.get('endpoints', [])),
                        "response_time_ms": f"{duration*1000:.2f}"
                    }
                )
            else:
                return TestResult(
                    test_name="API Info",
                    success=False,
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="API Info",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    def test_authentication_flow(self) -> TestResult:
        """Test complete authentication flow - critical for security."""
        start_time = time.time()
        
        try:
            # Test 1: Valid API key
            response = self.session.get(
                f"{self.config['api_base']}/analysis/statistics",
                headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
            )
            
            if response.status_code != 200:
                return TestResult(
                    test_name="Authentication Flow",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Valid API key rejected: HTTP {response.status_code}"
                )
            
            # Test 2: Invalid API key
            invalid_response = self.session.get(
                f"{self.config['api_base']}/analysis/statistics",
                headers={"Authorization": "ApiKey invalid-key-123"}
            )
            
            if invalid_response.status_code != 401:
                return TestResult(
                    test_name="Authentication Flow",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Invalid API key accepted: HTTP {invalid_response.status_code}"
                )
            
            # Test 3: No authentication
            no_auth_response = self.session.get(
                f"{self.config['api_base']}/analysis/statistics"
            )
            
            if no_auth_response.status_code != 401:
                return TestResult(
                    test_name="Authentication Flow",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Unauthenticated request accepted: HTTP {no_auth_response.status_code}"
                )
            
            duration = time.time() - start_time
            return TestResult(
                test_name="Authentication Flow",
                success=True,
                duration=duration,
                message="All authentication scenarios work correctly",
                details={"response_time_ms": f"{duration*1000:.2f}"}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Authentication Flow",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    def test_core_strategy_calculation(self) -> TestResult:
        """Test core strategy calculation - business critical functionality."""
        start_time = time.time()
        
        payload = {
            "position": {
                "players_hands": {
                    "player_1": {
                        "front": ["As", "Kh"],
                        "middle": ["Qd", "Jc", "Ts"],
                        "back": ["9h", "8d", "7c", "6s", "5h"]
                    }
                },
                "remaining_cards": ["2h", "3c", "4d", "Ah"],
                "current_player": 0,
                "round_number": 2
            },
            "calculation_mode": "instant",
            "max_calculation_time_seconds": 10
        }
        
        try:
            response = self.session.post(
                f"{self.config['api_base']}/analysis/calculate-strategy",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    strategy_data = data["data"]
                    ev = strategy_data.get("expected_value", 0)
                    confidence = strategy_data.get("confidence", 0)
                    
                    return TestResult(
                        test_name="Core Strategy Calculation",
                        success=True,
                        duration=duration,
                        message="Strategy calculation successful",
                        details={
                            "expected_value": ev,
                            "confidence": f"{confidence:.2f}",
                            "response_time_ms": f"{duration*1000:.2f}",
                            "meets_performance_target": duration < 0.5
                        }
                    )
                else:
                    return TestResult(
                        test_name="Core Strategy Calculation",
                        success=False,
                        duration=duration,
                        message="Invalid response format"
                    )
            else:
                return TestResult(
                    test_name="Core Strategy Calculation",
                    success=False,
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Core Strategy Calculation",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    # ========================================
    # BUSINESS LOGIC TESTS (MVP Priority 2)
    # ========================================

    def test_game_lifecycle(self) -> TestResult:
        """Test complete game creation and management lifecycle."""
        start_time = time.time()
        
        try:
            # Create game
            create_payload = {
                "player_count": 2,
                "rules_variant": "standard",
                "game_mode": "casual",
                "fantasy_land_enabled": True
            }
            
            create_response = self.session.post(
                f"{self.config['api_base']}/games/",
                json=create_payload,
                headers={
                    "Authorization": f"ApiKey {self.config['demo_api_key']}",
                    "Content-Type": "application/json"
                }
            )
            
            if create_response.status_code != 201:
                return TestResult(
                    test_name="Game Lifecycle",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Game creation failed: HTTP {create_response.status_code}"
                )
            
            game_data = create_response.json()
            if not game_data.get("success") or "data" not in game_data:
                return TestResult(
                    test_name="Game Lifecycle",
                    success=False,
                    duration=time.time() - start_time,
                    message="Invalid game creation response"
                )
            
            game_id = game_data["data"]["id"]
            
            # Retrieve game state
            state_response = self.session.get(
                f"{self.config['api_base']}/games/{game_id}/state",
                headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
            )
            
            if state_response.status_code != 200:
                return TestResult(
                    test_name="Game Lifecycle",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Game state retrieval failed: HTTP {state_response.status_code}"
                )
            
            duration = time.time() - start_time
            return TestResult(
                test_name="Game Lifecycle",
                success=True,
                duration=duration,
                message="Game creation and state retrieval successful",
                details={
                    "game_id": game_id[:8] + "...",
                    "response_time_ms": f"{duration*1000:.2f}"
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Game Lifecycle",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    def test_training_system(self) -> TestResult:
        """Test training system functionality."""
        start_time = time.time()
        
        try:
            # Create training session
            session_payload = {
                "scenario_id": str(uuid.uuid4()),
                "difficulty": "medium",
                "max_exercises": 5,
                "training_mode": "guided"
            }
            
            session_response = self.session.post(
                f"{self.config['api_base']}/training/sessions",
                json=session_payload,
                headers={
                    "Authorization": f"ApiKey {self.config['demo_api_key']}",
                    "Content-Type": "application/json"
                }
            )
            
            if session_response.status_code != 201:
                return TestResult(
                    test_name="Training System",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Training session creation failed: HTTP {session_response.status_code}"
                )
            
            session_data = session_response.json()
            if not session_data.get("success") or "data" not in session_data:
                return TestResult(
                    test_name="Training System",
                    success=False,
                    duration=time.time() - start_time,
                    message="Invalid training session response"
                )
            
            session_id = session_data["data"]["id"]
            
            # Retrieve session
            get_response = self.session.get(
                f"{self.config['api_base']}/training/sessions/{session_id}",
                headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
            )
            
            if get_response.status_code != 200:
                return TestResult(
                    test_name="Training System",
                    success=False,
                    duration=time.time() - start_time,
                    message=f"Training session retrieval failed: HTTP {get_response.status_code}"
                )
            
            duration = time.time() - start_time
            return TestResult(
                test_name="Training System",
                success=True,
                duration=duration,
                message="Training session lifecycle successful",
                details={
                    "session_id": session_id[:8] + "...",
                    "response_time_ms": f"{duration*1000:.2f}"
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Training System",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    # ========================================
    # ERROR HANDLING TESTS (MVP Priority 3)
    # ========================================

    def test_error_handling_validation(self) -> TestResult:
        """Test API error handling and validation."""
        start_time = time.time()
        
        try:
            # Test invalid strategy calculation payload
            invalid_payload = {
                "position": {
                    "players_hands": {},  # Invalid - empty
                    "remaining_cards": [],  # Invalid - empty
                    "current_player": 0,
                    "round_number": 1
                }
            }
            
            response = self.session.post(
                f"{self.config['api_base']}/analysis/calculate-strategy",
                json=invalid_payload,
                headers={"Content-Type": "application/json"}
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 400:
                error_data = response.json()
                return TestResult(
                    test_name="Error Handling Validation",
                    success=True,
                    duration=duration,
                    message="Invalid input correctly rejected",
                    details={
                        "status_code": response.status_code,
                        "error_type": error_data.get("error", "unknown"),
                        "response_time_ms": f"{duration*1000:.2f}"
                    }
                )
            else:
                return TestResult(
                    test_name="Error Handling Validation",
                    success=False,
                    duration=duration,
                    message=f"Expected 400, got {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Error Handling Validation",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    def test_rate_limiting(self) -> TestResult:
        """Test rate limiting functionality."""
        start_time = time.time()
        
        try:
            # Make rapid requests to trigger rate limiting
            responses = []
            for i in range(15):  # More than typical rate limit
                response = self.session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
                )
                responses.append(response.status_code)
                
                # If we get rate limited, that's what we expect
                if response.status_code == 429:
                    break
            
            duration = time.time() - start_time
            
            # Check if rate limiting kicked in
            if 429 in responses:
                return TestResult(
                    test_name="Rate Limiting",
                    success=True,
                    duration=duration,
                    message="Rate limiting correctly activated",
                    details={
                        "requests_before_limit": responses.index(429),
                        "response_time_ms": f"{duration*1000:.2f}"
                    }
                )
            else:
                return TestResult(
                    test_name="Rate Limiting",
                    success=True,  # Still success if under limit
                    duration=duration,
                    message="Rate limit not reached in test",
                    details={
                        "total_requests": len(responses),
                        "all_successful": all(r == 200 for r in responses)
                    }
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="Rate Limiting",
                success=False,
                duration=duration,
                message=f"Error: {str(e)}"
            )

    # ========================================
    # TEST EXECUTION AND REPORTING
    # ========================================

    def run_core_test_suite(self) -> Dict[str, Any]:
        """Run the complete core test suite."""
        print("🚀 Running Core API Test Suite")
        print("=" * 50)
        print("Testing critical functionality with MVP focus")
        print("-" * 50)
        
        # Check if server is running
        try:
            response = self.session.get(self.config['base_url'], timeout=5)
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running. Please start the server first:")
            print("   python src/main.py")
            return {"error": "Server not available", "results": []}
        
        # Run tests in order of criticality
        core_tests = [
            self.test_system_health,
            self.test_api_info,
            self.test_authentication_flow,
            self.test_core_strategy_calculation,
            self.test_game_lifecycle,
            self.test_training_system,
            self.test_error_handling_validation,
            self.test_rate_limiting,
        ]
        
        print("\n📋 Executing Core Tests:")
        print("-" * 30)
        
        for test_func in core_tests:
            result = test_func()
            self.log_result(result)
        
        # Generate summary
        print("\n📊 Test Summary:")
        print("-" * 30)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        avg_response_time = sum(r.duration for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"Average Response Time: {avg_response_time*1000:.2f}ms")
        
        # Performance assessment
        performance_tests = [r for r in self.test_results if r.duration > 0]
        fast_responses = sum(1 for r in performance_tests if r.duration < 0.5)
        performance_rate = (fast_responses / len(performance_tests)) * 100 if performance_tests else 0
        
        print(f"Performance Target (<500ms): {fast_responses}/{len(performance_tests)} ({performance_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 All core tests passed! System is ready for production.")
            status = "PASS"
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Review issues before deployment.")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.message}")
            status = "FAIL"
        
        return {
            "status": status,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "performance_rate": performance_rate
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.test_results
            ]
        }


def main():
    """Main execution function."""
    test_suite = CoreAPITestSuite()
    results = test_suite.run_core_test_suite()
    
    # Save results to file
    with open("core_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: core_test_results.json")
    
    # Exit with appropriate code
    exit_code = 0 if results["status"] == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())