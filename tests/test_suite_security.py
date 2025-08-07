#!/usr/bin/env python3
"""
Security Testing Suite for OFC Solver API
Validates authentication, authorization, and security vulnerabilities.
Tests for common security threats and attack vectors.
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import hmac
import base64
import jwt
import secrets
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

# Security test configuration
SECURITY_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_base": "http://localhost:8000/api/v1",
    "demo_api_key": "ofc-solver-demo-key-2024",
    "test_timeout": 30,
    "attack_patterns": {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83));--"
        ],
        "command_injection": [
            "; ls -la",
            "| whoami",
            "; cat /etc/passwd",
            "&& echo vulnerable"
        ]
    }
}


@dataclass
class SecurityTestResult:
    """Security test result."""
    test_name: str
    category: str
    success: bool
    vulnerability_found: bool
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str
    recommendation: str = ""
    evidence: Dict[str, Any] = None


class SecurityTestSuite:
    """
    Comprehensive security testing suite.
    Tests for authentication, authorization, and common vulnerabilities.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or SECURITY_CONFIG
        self.results: List[SecurityTestResult] = []
        
    def log_security_result(self, result: SecurityTestResult):
        """Log security test result with appropriate formatting."""
        status = "✅ SECURE" if not result.vulnerability_found else "🚨 VULNERABLE"
        severity_icon = {
            "LOW": "🟡",
            "MEDIUM": "🟠", 
            "HIGH": "🔴",
            "CRITICAL": "💀"
        }.get(result.severity, "❓")
        
        print(f"{status} {result.test_name}")
        if result.vulnerability_found:
            print(f"    {severity_icon} Severity: {result.severity}")
            print(f"    📝 Description: {result.description}")
            if result.recommendation:
                print(f"    💡 Recommendation: {result.recommendation}")
        else:
            print(f"    ✨ {result.description}")
        
        self.results.append(result)

    # ========================================
    # AUTHENTICATION SECURITY TESTS
    # ========================================

    async def test_api_key_security(self) -> List[SecurityTestResult]:
        """Test API key security mechanisms."""
        results = []
        
        print("\n🔐 Testing API Key Security")
        print("-" * 30)
        
        # Test 1: Timing attack resistance
        result = await self._test_timing_attack_resistance()
        results.append(result)
        self.log_security_result(result)
        
        # Test 2: API key brute force protection
        result = await self._test_api_key_brute_force()
        results.append(result)
        self.log_security_result(result)
        
        # Test 3: API key in URL parameters (should be rejected)
        result = await self._test_api_key_in_url()
        results.append(result)
        self.log_security_result(result)
        
        # Test 4: Case sensitivity
        result = await self._test_api_key_case_sensitivity()
        results.append(result)
        self.log_security_result(result)
        
        return results

    async def _test_timing_attack_resistance(self) -> SecurityTestResult:
        """Test resistance to timing attacks on API key validation."""
        
        async with aiohttp.ClientSession() as session:
            # Test with valid API key
            valid_times = []
            for _ in range(10):
                start_time = time.time()
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
                ) as response:
                    await response.text()
                valid_times.append(time.time() - start_time)
            
            # Test with invalid API key of same length
            invalid_key = "x" * len(self.config['demo_api_key'])
            invalid_times = []
            for _ in range(10):
                start_time = time.time()
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"ApiKey {invalid_key}"}
                ) as response:
                    await response.text()
                invalid_times.append(time.time() - start_time)
        
        # Calculate average times
        avg_valid_time = sum(valid_times) / len(valid_times)
        avg_invalid_time = sum(invalid_times) / len(invalid_times)
        time_difference = abs(avg_valid_time - avg_invalid_time)
        
        # Consider vulnerable if timing difference > 10ms
        vulnerable = time_difference > 0.01
        
        return SecurityTestResult(
            test_name="API Key Timing Attack Resistance",
            category="Authentication",
            success=True,
            vulnerability_found=vulnerable,
            severity="MEDIUM" if vulnerable else "LOW",
            description=(
                f"Timing difference: {time_difference*1000:.2f}ms" if vulnerable
                else "Constant-time comparison detected"
            ),
            recommendation="Implement constant-time string comparison" if vulnerable else "",
            evidence={
                "avg_valid_time": avg_valid_time,
                "avg_invalid_time": avg_invalid_time,
                "time_difference_ms": time_difference * 1000
            }
        )

    async def _test_api_key_brute_force(self) -> SecurityTestResult:
        """Test API key brute force protection."""
        
        async with aiohttp.ClientSession() as session:
            # Attempt rapid authentication with different keys
            attempts = 0
            blocked = False
            
            for i in range(50):  # Try 50 invalid keys rapidly
                fake_key = f"fake-key-{i:03d}"
                
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"ApiKey {fake_key}"}
                ) as response:
                    attempts += 1
                    
                    # Check if we get rate limited (429) or blocked
                    if response.status == 429:
                        blocked = True
                        break
        
        # Rate limiting should kick in for brute force attempts
        protected = blocked or attempts < 20  # Should be blocked before 20 attempts
        
        return SecurityTestResult(
            test_name="API Key Brute Force Protection",
            category="Authentication",
            success=True,
            vulnerability_found=not protected,
            severity="HIGH" if not protected else "LOW",
            description=(
                f"No rate limiting detected after {attempts} attempts" if not protected
                else f"Rate limiting activated after {attempts} attempts"
            ),
            recommendation="Implement progressive rate limiting for failed authentication" if not protected else "",
            evidence={"attempts_before_block": attempts, "blocked": blocked}
        )

    async def _test_api_key_in_url(self) -> SecurityTestResult:
        """Test if API key in URL parameters is rejected."""
        
        async with aiohttp.ClientSession() as session:
            # Try API key as URL parameter (insecure)
            url = f"{self.config['api_base']}/analysis/statistics?api_key={self.config['demo_api_key']}"
            
            async with session.get(url) as response:
                accepted = response.status == 200
        
        return SecurityTestResult(
            test_name="API Key URL Parameter Rejection",
            category="Authentication",
            success=True,
            vulnerability_found=accepted,
            severity="HIGH" if accepted else "LOW",
            description=(
                "API key accepted in URL parameters (insecure)" if accepted
                else "API key in URL parameters correctly rejected"
            ),
            recommendation="Only accept API keys in Authorization header" if accepted else "",
            evidence={"url_parameter_accepted": accepted}
        )

    async def _test_api_key_case_sensitivity(self) -> SecurityTestResult:
        """Test API key case sensitivity."""
        
        async with aiohttp.ClientSession() as session:
            # Test with lowercase version of API key
            lowercase_key = self.config['demo_api_key'].lower()
            
            async with session.get(
                f"{self.config['api_base']}/analysis/statistics",
                headers={"Authorization": f"ApiKey {lowercase_key}"}
            ) as response:
                lowercase_accepted = response.status == 200
            
            # Test with uppercase version
            uppercase_key = self.config['demo_api_key'].upper()
            
            async with session.get(
                f"{self.config['api_base']}/analysis/statistics",
                headers={"Authorization": f"ApiKey {uppercase_key}"}
            ) as response:
                uppercase_accepted = response.status == 200
        
        case_insensitive = lowercase_accepted or uppercase_accepted
        
        return SecurityTestResult(
            test_name="API Key Case Sensitivity",
            category="Authentication",
            success=True,
            vulnerability_found=case_insensitive,
            severity="MEDIUM" if case_insensitive else "LOW",
            description=(
                "API keys are case-insensitive (reduces entropy)" if case_insensitive
                else "API keys are case-sensitive"
            ),
            recommendation="Ensure API keys are case-sensitive for maximum entropy" if case_insensitive else "",
            evidence={
                "lowercase_accepted": lowercase_accepted,
                "uppercase_accepted": uppercase_accepted
            }
        )

    # ========================================
    # JWT SECURITY TESTS
    # ========================================

    async def test_jwt_security(self) -> List[SecurityTestResult]:
        """Test JWT token security."""
        results = []
        
        print("\n🎫 Testing JWT Security")
        print("-" * 30)
        
        # Test 1: JWT algorithm confusion
        result = await self._test_jwt_algorithm_confusion()
        results.append(result)
        self.log_security_result(result)
        
        # Test 2: JWT signature verification
        result = await self._test_jwt_signature_verification()
        results.append(result)
        self.log_security_result(result)
        
        # Test 3: JWT expiration enforcement
        result = await self._test_jwt_expiration()
        results.append(result)
        self.log_security_result(result)
        
        return results

    async def _test_jwt_algorithm_confusion(self) -> SecurityTestResult:
        """Test JWT algorithm confusion attack."""
        
        try:
            # Create a malicious JWT with 'none' algorithm
            header = {"alg": "none", "typ": "JWT"}
            payload = {
                "user_id": "test_user",
                "user_type": "admin",
                "features": ["all"],
                "exp": int(time.time()) + 3600
            }
            
            # Encode without signature (algorithm: none)
            encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            malicious_token = f"{encoded_header}.{encoded_payload}."
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"Bearer {malicious_token}"}
                ) as response:
                    accepted = response.status == 200
            
            return SecurityTestResult(
                test_name="JWT Algorithm Confusion Attack",
                category="Authentication",
                success=True,
                vulnerability_found=accepted,
                severity="CRITICAL" if accepted else "LOW",
                description=(
                    "JWT with 'none' algorithm accepted" if accepted
                    else "JWT algorithm properly validated"
                ),
                recommendation="Explicitly whitelist allowed JWT algorithms and reject 'none'" if accepted else "",
                evidence={"none_algorithm_accepted": accepted}
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="JWT Algorithm Confusion Attack",
                category="Authentication",
                success=False,
                vulnerability_found=False,
                severity="LOW",
                description=f"Test error: {str(e)}",
                evidence={"error": str(e)}
            )

    async def _test_jwt_signature_verification(self) -> SecurityTestResult:
        """Test JWT signature verification."""
        
        try:
            # Create a JWT with invalid signature
            header = {"alg": "RS256", "typ": "JWT"}
            payload = {
                "user_id": "malicious_user",
                "user_type": "admin",
                "features": ["all"],
                "exp": int(time.time()) + 3600
            }
            
            encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            fake_signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip('=')
            
            malicious_token = f"{encoded_header}.{encoded_payload}.{fake_signature}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"Bearer {malicious_token}"}
                ) as response:
                    accepted = response.status == 200
            
            return SecurityTestResult(
                test_name="JWT Signature Verification",
                category="Authentication",
                success=True,
                vulnerability_found=accepted,
                severity="CRITICAL" if accepted else "LOW",
                description=(
                    "JWT with invalid signature accepted" if accepted
                    else "JWT signature properly verified"
                ),
                recommendation="Always verify JWT signatures against trusted keys" if accepted else "",
                evidence={"invalid_signature_accepted": accepted}
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="JWT Signature Verification",
                category="Authentication",
                success=False,
                vulnerability_found=False,
                severity="LOW",
                description=f"Test error: {str(e)}",
                evidence={"error": str(e)}
            )

    async def _test_jwt_expiration(self) -> SecurityTestResult:
        """Test JWT expiration enforcement."""
        
        try:
            # Create an expired JWT
            header = {"alg": "RS256", "typ": "JWT"}
            payload = {
                "user_id": "test_user",
                "user_type": "demo",
                "features": ["basic"],
                "exp": int(time.time()) - 3600  # Expired 1 hour ago
            }
            
            encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            fake_signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip('=')
            
            expired_token = f"{encoded_header}.{encoded_payload}.{fake_signature}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['api_base']}/analysis/statistics",
                    headers={"Authorization": f"Bearer {expired_token}"}
                ) as response:
                    accepted = response.status == 200
            
            return SecurityTestResult(
                test_name="JWT Expiration Enforcement",
                category="Authentication",
                success=True,
                vulnerability_found=accepted,
                severity="HIGH" if accepted else "LOW",
                description=(
                    "Expired JWT token accepted" if accepted
                    else "JWT expiration properly enforced"
                ),
                recommendation="Always check JWT expiration timestamp" if accepted else "",
                evidence={"expired_token_accepted": accepted}
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="JWT Expiration Enforcement",
                category="Authentication",
                success=False,
                vulnerability_found=False,
                severity="LOW",
                description=f"Test error: {str(e)}",
                evidence={"error": str(e)}
            )

    # ========================================
    # INJECTION ATTACK TESTS
    # ========================================

    async def test_injection_attacks(self) -> List[SecurityTestResult]:
        """Test for various injection vulnerabilities."""
        results = []
        
        print("\n💉 Testing Injection Attacks")
        print("-" * 30)
        
        # Test SQL injection
        result = await self._test_sql_injection()
        results.append(result)
        self.log_security_result(result)
        
        # Test XSS
        result = await self._test_xss_injection()
        results.append(result)
        self.log_security_result(result)
        
        # Test command injection
        result = await self._test_command_injection()
        results.append(result)
        self.log_security_result(result)
        
        return results

    async def _test_sql_injection(self) -> SecurityTestResult:
        """Test for SQL injection vulnerabilities."""
        
        vulnerable_responses = []
        
        async with aiohttp.ClientSession() as session:
            for payload in self.config['attack_patterns']['sql_injection']:
                # Test in game creation endpoint
                game_data = {
                    "player_count": 2,
                    "rules_variant": payload,  # Inject here
                    "game_mode": "casual"
                }
                
                try:
                    async with session.post(
                        f"{self.config['api_base']}/games/",
                        json=game_data,
                        headers={
                            "Authorization": f"ApiKey {self.config['demo_api_key']}",
                            "Content-Type": "application/json"
                        }
                    ) as response:
                        response_text = await response.text()
                        
                        # Look for SQL error messages or unexpected behavior
                        sql_errors = [
                            "syntax error", "sql", "database", "mysql", "postgresql",
                            "sqlite", "table", "column", "constraint"
                        ]
                        
                        response_lower = response_text.lower()
                        if any(error in response_lower for error in sql_errors):
                            vulnerable_responses.append({
                                "payload": payload,
                                "response": response_text[:200],
                                "status": response.status
                            })
                            
                except Exception:
                    pass  # Connection errors are expected
        
        vulnerable = len(vulnerable_responses) > 0
        
        return SecurityTestResult(
            test_name="SQL Injection Protection",
            category="Injection",
            success=True,
            vulnerability_found=vulnerable,
            severity="CRITICAL" if vulnerable else "LOW",
            description=(
                f"SQL injection possible in {len(vulnerable_responses)} cases" if vulnerable
                else "No SQL injection vulnerabilities detected"
            ),
            recommendation="Use parameterized queries and input validation" if vulnerable else "",
            evidence={"vulnerable_responses": vulnerable_responses}
        )

    async def _test_xss_injection(self) -> SecurityTestResult:
        """Test for XSS vulnerabilities."""
        
        reflected_payloads = []
        
        async with aiohttp.ClientSession() as session:
            for payload in self.config['attack_patterns']['xss']:
                # Test in training session creation
                session_data = {
                    "scenario_id": payload,  # Inject here
                    "difficulty": "medium",
                    "max_exercises": 5
                }
                
                try:
                    async with session.post(
                        f"{self.config['api_base']}/training/sessions",
                        json=session_data,
                        headers={
                            "Authorization": f"ApiKey {self.config['demo_api_key']}",
                            "Content-Type": "application/json"
                        }
                    ) as response:
                        response_text = await response.text()
                        
                        # Check if payload is reflected in response
                        if payload in response_text:
                            reflected_payloads.append({
                                "payload": payload,
                                "reflected": True
                            })
                            
                except Exception:
                    pass
        
        vulnerable = len(reflected_payloads) > 0
        
        return SecurityTestResult(
            test_name="XSS Protection",
            category="Injection",
            success=True,
            vulnerability_found=vulnerable,
            severity="HIGH" if vulnerable else "LOW",
            description=(
                f"XSS payloads reflected in {len(reflected_payloads)} cases" if vulnerable
                else "No XSS vulnerabilities detected"
            ),
            recommendation="Implement proper input validation and output encoding" if vulnerable else "",
            evidence={"reflected_payloads": reflected_payloads}
        )

    async def _test_command_injection(self) -> SecurityTestResult:
        """Test for command injection vulnerabilities."""
        
        vulnerable_responses = []
        
        async with aiohttp.ClientSession() as session:
            for payload in self.config['attack_patterns']['command_injection']:
                # Test in strategy calculation
                calc_data = {
                    "position": {
                        "players_hands": {
                            "player_1": {
                                "front": ["As", "Kh"],
                                "middle": ["Qd", payload, "Ts"],  # Inject here
                                "back": ["9h", "8d", "7c", "6s", "5h"]
                            }
                        },
                        "remaining_cards": ["2h", "3c"],
                        "current_player": 0,
                        "round_number": 1
                    }
                }
                
                try:
                    async with session.post(
                        f"{self.config['api_base']}/analysis/calculate-strategy",
                        json=calc_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        response_text = await response.text()
                        
                        # Look for command execution indicators
                        cmd_indicators = ["root", "bin", "etc", "whoami", "ls"]
                        
                        if any(indicator in response_text.lower() for indicator in cmd_indicators):
                            vulnerable_responses.append({
                                "payload": payload,
                                "response": response_text[:200]
                            })
                            
                except Exception:
                    pass
        
        vulnerable = len(vulnerable_responses) > 0
        
        return SecurityTestResult(
            test_name="Command Injection Protection",
            category="Injection",
            success=True,
            vulnerability_found=vulnerable,
            severity="CRITICAL" if vulnerable else "LOW",
            description=(
                f"Command injection possible in {len(vulnerable_responses)} cases" if vulnerable
                else "No command injection vulnerabilities detected"
            ),
            recommendation="Validate all inputs and avoid system calls with user data" if vulnerable else "",
            evidence={"vulnerable_responses": vulnerable_responses}
        )

    # ========================================
    # AUTHORIZATION TESTS
    # ========================================

    async def test_authorization(self) -> List[SecurityTestResult]:
        """Test authorization and access control."""
        results = []
        
        print("\n🛡️  Testing Authorization")
        print("-" * 30)
        
        # Test privilege escalation
        result = await self._test_privilege_escalation()
        results.append(result)
        self.log_security_result(result)
        
        # Test resource access control
        result = await self._test_resource_access_control()
        results.append(result)
        self.log_security_result(result)
        
        return results

    async def _test_privilege_escalation(self) -> SecurityTestResult:
        """Test for privilege escalation vulnerabilities."""
        
        # This would require creating different user types and testing access
        # For now, test if admin endpoints are properly protected
        
        async with aiohttp.ClientSession() as session:
            admin_endpoints = [
                "/admin/users",
                "/admin/system",
                "/admin/config"
            ]
            
            accessible_endpoints = []
            
            for endpoint in admin_endpoints:
                try:
                    async with session.get(
                        f"{self.config['api_base']}{endpoint}",
                        headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
                    ) as response:
                        if response.status == 200:
                            accessible_endpoints.append(endpoint)
                except Exception:
                    pass
        
        vulnerable = len(accessible_endpoints) > 0
        
        return SecurityTestResult(
            test_name="Privilege Escalation Protection",
            category="Authorization",
            success=True,
            vulnerability_found=vulnerable,
            severity="HIGH" if vulnerable else "LOW",
            description=(
                f"Admin endpoints accessible: {accessible_endpoints}" if vulnerable
                else "Admin endpoints properly protected"
            ),
            recommendation="Implement proper role-based access control" if vulnerable else "",
            evidence={"accessible_admin_endpoints": accessible_endpoints}
        )

    async def _test_resource_access_control(self) -> SecurityTestResult:
        """Test resource-level access control."""
        
        # Test if users can access other users' resources
        # This is a simplified test
        
        async with aiohttp.ClientSession() as session:
            # Try to access resources with different user IDs
            unauthorized_access = []
            
            test_endpoints = [
                "/games/user_123/history",
                "/training/user_456/sessions",
                "/analysis/user_789/statistics"
            ]
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(
                        f"{self.config['api_base']}{endpoint}",
                        headers={"Authorization": f"ApiKey {self.config['demo_api_key']}"}
                    ) as response:
                        if response.status == 200:
                            unauthorized_access.append(endpoint)
                except Exception:
                    pass
        
        vulnerable = len(unauthorized_access) > 0
        
        return SecurityTestResult(
            test_name="Resource Access Control",
            category="Authorization",
            success=True,
            vulnerability_found=vulnerable,
            severity="MEDIUM" if vulnerable else "LOW",
            description=(
                f"Unauthorized resource access: {unauthorized_access}" if vulnerable
                else "Resource access properly controlled"
            ),
            recommendation="Implement user-specific resource access validation" if vulnerable else "",
            evidence={"unauthorized_endpoints": unauthorized_access}
        )

    # ========================================
    # COMPREHENSIVE SECURITY ASSESSMENT
    # ========================================

    async def run_comprehensive_security_tests(self) -> Dict[str, Any]:
        """Run comprehensive security testing suite."""
        
        print("🔒 Running Comprehensive Security Test Suite")
        print("=" * 60)
        
        test_start_time = time.time()
        all_results = []
        
        try:
            # 1. Authentication security tests
            auth_results = await self.test_api_key_security()
            all_results.extend(auth_results)
            
            # 2. JWT security tests
            jwt_results = await self.test_jwt_security()
            all_results.extend(jwt_results)
            
            # 3. Injection attack tests
            injection_results = await self.test_injection_attacks()
            all_results.extend(injection_results)
            
            # 4. Authorization tests
            authz_results = await self.test_authorization()
            all_results.extend(authz_results)
            
            # Generate security assessment
            assessment = self._generate_security_assessment(all_results)
            
            total_duration = time.time() - test_start_time
            
            return {
                "test_suite": "comprehensive_security",
                "timestamp": datetime.now().isoformat(),
                "duration": total_duration,
                "results": [
                    {
                        "test_name": r.test_name,
                        "category": r.category,
                        "success": r.success,
                        "vulnerability_found": r.vulnerability_found,
                        "severity": r.severity,
                        "description": r.description,
                        "recommendation": r.recommendation,
                        "evidence": r.evidence
                    }
                    for r in all_results
                ],
                "assessment": assessment
            }
            
        except Exception as e:
            logger.error(f"Security test suite error: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "partial_results": [
                    {
                        "test_name": r.test_name,
                        "vulnerability_found": r.vulnerability_found,
                        "severity": r.severity
                    }
                    for r in all_results
                ]
            }

    def _generate_security_assessment(self, results: List[SecurityTestResult]) -> Dict[str, Any]:
        """Generate comprehensive security assessment."""
        
        # Count vulnerabilities by severity
        vulnerability_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        category_counts = {}
        
        for result in results:
            if result.vulnerability_found:
                vulnerability_counts[result.severity] += 1
                
                if result.category not in category_counts:
                    category_counts[result.category] = 0
                category_counts[result.category] += 1
        
        # Calculate security score
        total_vulnerabilities = sum(vulnerability_counts.values())
        critical_weight = vulnerability_counts["CRITICAL"] * 25
        high_weight = vulnerability_counts["HIGH"] * 15
        medium_weight = vulnerability_counts["MEDIUM"] * 8
        low_weight = vulnerability_counts["LOW"] * 3
        
        penalty = critical_weight + high_weight + medium_weight + low_weight
        security_score = max(0, 100 - penalty)
        
        # Determine security level
        if security_score >= 90:
            security_level = "EXCELLENT"
        elif security_score >= 75:
            security_level = "GOOD"
        elif security_score >= 60:
            security_level = "MODERATE"
        elif security_score >= 40:
            security_level = "POOR"
        else:
            security_level = "CRITICAL"
        
        # Generate recommendations
        recommendations = []
        
        if vulnerability_counts["CRITICAL"] > 0:
            recommendations.append("🚨 URGENT: Fix critical vulnerabilities immediately")
        
        if vulnerability_counts["HIGH"] > 0:
            recommendations.append("🔴 HIGH PRIORITY: Address high-severity vulnerabilities")
        
        if vulnerability_counts["MEDIUM"] > 0:
            recommendations.append("🟠 MEDIUM PRIORITY: Fix medium-severity issues")
        
        if total_vulnerabilities == 0:
            recommendations.append("✅ Security testing shows no major vulnerabilities")
        
        recommendations.extend([
            "🔍 Conduct regular security audits",
            "📚 Train development team on secure coding practices",
            "🛡️  Implement automated security scanning in CI/CD"
        ])
        
        return {
            "security_score": security_score,
            "security_level": security_level,
            "total_tests": len(results),
            "total_vulnerabilities": total_vulnerabilities,
            "vulnerability_breakdown": vulnerability_counts,
            "category_breakdown": category_counts,
            "critical_issues": [
                r.test_name for r in results 
                if r.vulnerability_found and r.severity == "CRITICAL"
            ],
            "recommendations": recommendations
        }

    def generate_security_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable security report."""
        
        assessment = results.get('assessment', {})
        
        report = f"""
# Security Assessment Report

Generated: {results.get('timestamp', 'Unknown')}
Duration: {results.get('duration', 0):.2f} seconds

## Executive Summary
- **Security Score**: {assessment.get('security_score', 0):.1f}/100
- **Security Level**: {assessment.get('security_level', 'UNKNOWN')}
- **Total Tests**: {assessment.get('total_tests', 0)}
- **Vulnerabilities Found**: {assessment.get('total_vulnerabilities', 0)}

## Vulnerability Breakdown
"""
        
        vuln_breakdown = assessment.get('vulnerability_breakdown', {})
        for severity, count in vuln_breakdown.items():
            if count > 0:
                icon = {"CRITICAL": "💀", "HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(severity, "❓")
                report += f"- {icon} {severity}: {count}\n"
        
        # Critical issues
        critical_issues = assessment.get('critical_issues', [])
        if critical_issues:
            report += f"\n## 🚨 Critical Issues Requiring Immediate Attention\n"
            for issue in critical_issues:
                report += f"- {issue}\n"
        
        # Category breakdown
        category_breakdown = assessment.get('category_breakdown', {})
        if category_breakdown:
            report += f"\n## Vulnerabilities by Category\n"
            for category, count in category_breakdown.items():
                report += f"- {category}: {count}\n"
        
        # Recommendations
        recommendations = assessment.get('recommendations', [])
        if recommendations:
            report += f"\n## Recommendations\n"
            for rec in recommendations:
                report += f"- {rec}\n"
        
        return report


async def main():
    """Main execution function."""
    test_suite = SecurityTestSuite()
    
    # Run comprehensive security tests
    results = await test_suite.run_comprehensive_security_tests()
    
    # Generate and display report
    report_text = test_suite.generate_security_report(results)
    print(report_text)
    
    # Save results
    with open("security_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    with open("security_test_report.md", "w") as f:
        f.write(report_text)
    
    print(f"\n📄 Results saved to:")
    print(f"  - security_test_results.json")
    print(f"  - security_test_report.md")
    
    # Determine success
    assessment = results.get('assessment', {})
    security_score = assessment.get('security_score', 0)
    critical_issues = len(assessment.get('critical_issues', []))
    
    if critical_issues == 0 and security_score >= 75:
        print("\n🎉 Security tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  Security issues found (Score: {security_score:.1f}/100)")
        return 1


if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)