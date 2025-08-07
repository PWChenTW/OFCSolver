#!/usr/bin/env python3
"""
Basic API Testing Script for OFC Solver
Tests core functionality to ensure API endpoints are working correctly.
"""

import requests
import json
import time
import sys
from uuid import uuid4
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test API Keys
DEMO_API_KEY = "ofc-solver-demo-key-2024"
TEST_API_KEY = "ofc-solver-test-key-2024"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", response_time: float = 0):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        time_str = f"({response_time:.2f}s)" if response_time > 0 else ""
        print(f"{status} {test_name} {time_str}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_time": response_time
        })
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}", response_time)
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Health Check", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_api_info(self):
        """Test API info endpoint."""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.api_base}")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Info", True, f"Version: {data.get('version', 'unknown')}", response_time)
                return True
            else:
                self.log_test("API Info", False, f"Status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("API Info", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_strategy_calculation(self):
        """Test core strategy calculation (public endpoint)."""
        start_time = time.time()
        try:
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
            
            response = self.session.post(
                f"{self.api_base}/analysis/calculate-strategy",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    strategy_data = data["data"]
                    ev = strategy_data.get("expected_value", 0)
                    confidence = strategy_data.get("confidence", 0)
                    self.log_test(
                        "Strategy Calculation", 
                        True, 
                        f"EV: {ev}, Confidence: {confidence:.2f}", 
                        response_time
                    )
                    return True
                else:
                    self.log_test("Strategy Calculation", False, "Invalid response format", response_time)
                    return False
            else:
                self.log_test("Strategy Calculation", False, f"Status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Strategy Calculation", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_authentication(self):
        """Test API key authentication."""
        start_time = time.time()
        try:
            # Test with valid API key
            response = self.session.get(
                f"{self.api_base}/analysis/statistics",
                headers={"Authorization": f"ApiKey {DEMO_API_KEY}"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Authentication (Valid Key)", True, "Demo API key accepted", response_time)
                auth_success = True
            else:
                self.log_test("Authentication (Valid Key)", False, f"Status code: {response.status_code}", response_time)
                auth_success = False
            
            # Test without API key (should fail)
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/analysis/statistics")
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Authentication (No Key)", True, "Correctly rejected unauthenticated request", response_time)
                return auth_success
            else:
                self.log_test("Authentication (No Key)", False, f"Should return 401, got {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Authentication", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_training_session(self):
        """Test training session creation and retrieval."""
        start_time = time.time()
        try:
            # Create training session
            payload = {
                "scenario_id": str(uuid4()),
                "difficulty": "medium",
                "max_exercises": 5,
                "training_mode": "guided"
            }
            
            response = self.session.post(
                f"{self.api_base}/training/sessions",
                json=payload,
                headers={
                    "Authorization": f"ApiKey {DEMO_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                if data.get("success") and "data" in data:
                    session_id = data["data"]["id"]
                    self.log_test("Training Session Creation", True, f"Session ID: {session_id[:8]}...", response_time)
                    
                    # Test session retrieval
                    start_time = time.time()
                    response = self.session.get(
                        f"{self.api_base}/training/sessions/{session_id}",
                        headers={"Authorization": f"ApiKey {DEMO_API_KEY}"}
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.log_test("Training Session Retrieval", True, "Session retrieved successfully", response_time)
                        return True
                    else:
                        self.log_test("Training Session Retrieval", False, f"Status code: {response.status_code}", response_time)
                        return False
                else:
                    self.log_test("Training Session Creation", False, "Invalid response format", response_time)
                    return False
            else:
                self.log_test("Training Session Creation", False, f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Training Session", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_game_creation(self):
        """Test game creation and state retrieval."""
        start_time = time.time()
        try:
            # Create game
            payload = {
                "player_count": 2,
                "rules_variant": "standard",
                "game_mode": "casual",
                "fantasy_land_enabled": True
            }
            
            response = self.session.post(
                f"{self.api_base}/games/",
                json=payload,
                headers={
                    "Authorization": f"ApiKey {DEMO_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                if data.get("success") and "data" in data:
                    game_id = data["data"]["id"]
                    self.log_test("Game Creation", True, f"Game ID: {game_id[:8]}...", response_time)
                    
                    # Test game state retrieval
                    start_time = time.time()
                    response = self.session.get(
                        f"{self.api_base}/games/{game_id}/state",
                        headers={"Authorization": f"ApiKey {DEMO_API_KEY}"}
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.log_test("Game State Retrieval", True, "Game state retrieved successfully", response_time)
                        return True
                    else:
                        self.log_test("Game State Retrieval", False, f"Status code: {response.status_code}", response_time)
                        return False
                else:
                    self.log_test("Game Creation", False, "Invalid response format", response_time)
                    return False
            else:
                self.log_test("Game Creation", False, f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Game Creation", False, f"Error: {str(e)}", response_time)
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        start_time = time.time()
        try:
            # Test invalid strategy calculation
            payload = {
                "position": {
                    "players_hands": {},  # Empty hands - should be invalid
                    "remaining_cards": [],  # Empty cards - should be invalid
                    "current_player": 0,
                    "round_number": 1
                }
            }
            
            response = self.session.post(
                f"{self.api_base}/analysis/calculate-strategy",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test("Error Handling (Validation)", True, "Correctly rejected invalid input", response_time)
                return True
            else:
                self.log_test("Error Handling (Validation)", False, f"Expected 400, got {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling", False, f"Error: {str(e)}", response_time)
            return False
    
    def run_all_tests(self):
        """Run all tests and provide summary."""
        print("🚀 OFC Solver API Basic Testing")
        print("=" * 50)
        
        # Check if server is running
        try:
            response = self.session.get(self.base_url, timeout=5)
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running. Please start the server first:")
            print("   python src/main.py")
            return False
        
        tests = [
            self.test_health_check,
            self.test_api_info,
            self.test_strategy_calculation,
            self.test_authentication,
            self.test_training_session,
            self.test_game_creation,
            self.test_error_handling,
        ]
        
        print("\n📋 Running Tests:")
        print("-" * 30)
        
        for test in tests:
            test()
        
        # Summary
        print("\n📊 Test Summary:")
        print("-" * 30)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            failed_tests = [r for r in self.test_results if not r["success"]]
            print("\nFailed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
            return False


def main():
    """Main test execution."""
    if len(sys.argv) > 1 and sys.argv[1] == "--url":
        base_url = sys.argv[2] if len(sys.argv) > 2 else BASE_URL
    else:
        base_url = BASE_URL
    
    tester = APITester(base_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🔗 Next Steps:")
        print("  - View API docs: http://localhost:8000/api/docs")
        print("  - Check health: http://localhost:8000/health")
        print("  - Read usage guide: API_USAGE_GUIDE.md")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()