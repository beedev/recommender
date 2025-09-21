#!/usr/bin/env python3
"""
Guided Flow Test Script for Welding Equipment Recommendation System

This script specifically tests the guided flow scenarios that were recently fixed
to handle realistic user queries instead of artificial step-based queries.

Features:
- Tests guided flow endpoint (/api/v1/enterprise/guided-flow)
- Realistic user scenarios (package formation, multi-process, beginner requests)
- Product-specific queries leveraging LLM product extraction
- Validates guided flow detection and routing
- Color-coded output for easy result interpretation

Usage:
    python3 scripts/test_guided_flow.py
    python3 scripts/test_guided_flow.py --verbose
    python3 scripts/test_guided_flow.py --scenario package_formation
"""

import requests
import json
import time
import argparse
from typing import Dict, List, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
GUIDED_FLOW_ENDPOINT = f"{BASE_URL}/api/v1/enterprise/recommendations"

# ANSI Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_result(key: str, value: Any):
    """Print formatted result"""
    print(f"{Colors.PURPLE}{key}:{Colors.END} {Colors.WHITE}{value}{Colors.END}")

# Guided Flow Test Scenarios
GUIDED_FLOW_SCENARIOS = {
    "package_formation_aristo": {
        "name": "Package Formation - Aristo 500 ix",
        "query": "I want to form a package with Aristo 500 ix",
        "expected_mode": "GUIDED_FLOW", 
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Package formation request",
        "should_detect_product": "aristo 500 ix",
        "expected_algorithms": ["COMPATIBILITY", "SALES_FREQUENCY"]
    },
    "package_formation_warrior": {
        "name": "Package Formation - Warrior 400i",
        "query": "I want to create a package with Warrior 400i",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW", 
        "expected_reasoning": "Package formation request",
        "should_detect_product": "warrior 400i",
        "expected_algorithms": ["COMPATIBILITY", "SALES_FREQUENCY"]
    },
    "package_formation_renegade": {
        "name": "Package Formation - Renegade 300",
        "query": "I want to build a setup with Renegade 300",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Package formation request", 
        "should_detect_product": "renegade 300",
        "expected_algorithms": ["COMPATIBILITY", "SALES_FREQUENCY"]
    },
    "multi_process_request": {
        "name": "Multi-Process Welding Request",
        "query": "I need a multi process welding machine for versatile welding",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Multi-process query detected",
        "should_detect_product": None,  # General request, no specific product
        "expected_algorithms": ["SALES_FREQUENCY", "COMPATIBILITY"]
    },
    "beginner_package_request": {
        "name": "Beginner Package Request",
        "query": "I need complete welding equipment, looking for welding machine",
        "expected_mode": "GUIDED_FLOW", 
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Beginner package request",
        "should_detect_product": None,  # General beginner request
        "expected_algorithms": ["SALES_FREQUENCY", "COMPATIBILITY"]
    },
    "specific_product_query": {
        "name": "Specific Product Query",
        "query": "I have a Warrior 400i, what goes with it?",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW", 
        "expected_reasoning": "Package formation request",
        "should_detect_product": "warrior 400i",
        "expected_algorithms": ["COMPATIBILITY", "SALES_FREQUENCY"]
    },
    "existing_equipment": {
        "name": "Existing Equipment Query",
        "query": "I already have an Aristo 500 ix, what compatible equipment should I add?",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Package formation request",
        "should_detect_product": "aristo 500 ix", 
        "expected_algorithms": ["COMPATIBILITY", "SALES_FREQUENCY"]
    },
    "welding_starter_kit": {
        "name": "Welding Starter Kit",
        "query": "I'm looking for welding starter kit for my garage",
        "expected_mode": "GUIDED_FLOW",
        "expected_strategy": "GUIDED_FLOW",
        "expected_reasoning": "Beginner package request",
        "should_detect_product": None,
        "expected_algorithms": ["SALES_FREQUENCY", "COMPATIBILITY"]
    }
}

class GuidedFlowTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session_id = f"guided_flow_test_{int(time.time())}"
        self.results = {}

    def check_server_health(self) -> bool:
        """Check if the server is running and healthy"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"Server is running: {health_data.get('status', 'unknown')}")
                
                # Check database connections
                for db_name, db_info in health_data.get('database', {}).items():
                    if db_info.get('status') == 'connected':
                        print_success(f"{db_name.upper()} database connected")
                    else:
                        print_error(f"{db_name.upper()} database not connected: {db_info}")
                        return False
                return True
            else:
                print_error(f"Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print_error(f"Cannot connect to server: {e}")
            return False

    def send_guided_flow_request(self, query: str) -> Dict[str, Any]:
        """Send guided flow request to enterprise endpoint"""
        payload = {
            "query": query,
            "user_context": {
                "user_id": "guided_flow_test_user",
                "experience_level": "beginner",  # Use beginner to trigger guided flow
                "preferences": {
                    "budget_range": "mid_range",
                    "preferred_brands": ["ESAB"],
                    "applications": ["general"]
                }
            },
            "session_id": self.session_id,
            "language": "en"
        }

        try:
            print_info(f"Sending guided flow request: {query[:50]}...")
            
            start_time = time.time()
            response = requests.post(
                GUIDED_FLOW_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = time.time() - start_time

            if self.verbose:
                print_info(f"Response time: {response_time:.2f}s")
                print_info(f"Status code: {response.status_code}")

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time,
                    "status_code": response.status_code
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout (30s)"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {e}"}

    def validate_guided_flow(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, bool]:
        """Validate guided flow response against expected scenario"""
        validation = {
            "has_packages": False,
            "correct_strategy": False,
            "correct_reasoning": False,
            "product_detected": False,
            "correct_algorithms": False,
            "has_search_metadata": False,
            "trinity_compliance": False,
            "guided_flow_activated": False
        }

        if not result.get("success") or not result.get("data"):
            return validation

        data = result["data"]
        packages = data.get("packages", [])

        # Check if packages exist
        if packages:
            validation["has_packages"] = True

        # Check search metadata for guided flow indicators
        search_metadata = data.get("search_metadata")
        if search_metadata:
            validation["has_search_metadata"] = True
            
            # Check strategy
            strategy = search_metadata.get("strategy")
            if strategy == scenario.get("expected_strategy"):
                validation["correct_strategy"] = True
                validation["guided_flow_activated"] = True
            
            # Check reasoning contains expected keywords
            reasoning = search_metadata.get("reasoning", "").lower()
            expected_reasoning = scenario.get("expected_reasoning", "").lower()
            if expected_reasoning in reasoning:
                validation["correct_reasoning"] = True
            
            # Check algorithms used
            algorithms = search_metadata.get("algorithms", [])
            expected_algorithms = scenario.get("expected_algorithms", [])
            if any(alg in algorithms for alg in expected_algorithms):
                validation["correct_algorithms"] = True

        # Check product detection (check original_intent for product detection)
        original_intent = data.get("original_intent", {})
        if original_intent:
            similar_to_customer = original_intent.get("similar_to_customer")
            extracted_entities = original_intent.get("extracted_entities", {})
            mentioned_product = extracted_entities.get("mentioned_product")
            
            expected_product = scenario.get("should_detect_product")
            if expected_product:
                detected_product = similar_to_customer or mentioned_product
                if detected_product and expected_product.lower() in detected_product.lower():
                    validation["product_detected"] = True
            else:
                # If no product expected, validation passes if none detected or general detection
                validation["product_detected"] = True

        # Check Trinity compliance in packages
        if packages:
            for package in packages:
                components = package.get("components", {})
                has_trinity = (
                    "PowerSource" in components and
                    ("Feeder" in components or "Cooler" in components)
                )
                if has_trinity:
                    validation["trinity_compliance"] = True
                    break

        return validation

    def print_guided_flow_details(self, data: Dict[str, Any]):
        """Print detailed guided flow information"""
        print(f"\n{Colors.BOLD}Guided Flow Details:{Colors.END}")
        
        # Search metadata
        search_metadata = data.get("search_metadata", {})
        if search_metadata:
            print_result("Strategy", search_metadata.get("strategy", "N/A"))
            print_result("Reasoning", search_metadata.get("reasoning", "N/A"))
            print_result("Algorithms", ", ".join(search_metadata.get("algorithms", [])))
            print_result("Confidence", f"{search_metadata.get('confidence', 0):.1%}")
        
        # Original intent and product detection
        original_intent = data.get("original_intent", {})
        if original_intent:
            print_result("Detected Language", original_intent.get("detected_language", "N/A"))
            print_result("Expertise Mode", original_intent.get("expertise_mode", "N/A"))
            print_result("Similar to Customer", original_intent.get("similar_to_customer", "None"))
            
            extracted_entities = original_intent.get("extracted_entities", {})
            if extracted_entities:
                mentioned_product = extracted_entities.get("mentioned_product")
                if mentioned_product:
                    print_result("Mentioned Product", mentioned_product)

        # Package summary
        packages = data.get("packages", [])
        if packages:
            print_result("Packages Returned", len(packages))
            if packages:
                package = packages[0]
                components = package.get("components", {})
                print_result("Component Categories", ", ".join(components.keys()))
                print_result("Trinity Compliant", 
                           "Yes" if ("PowerSource" in components and 
                                   ("Feeder" in components or "Cooler" in components)) else "No")

    def run_scenario_test(self, scenario_key: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single guided flow test scenario"""
        print_header(f"Testing: {scenario['name']}")
        
        # Send request
        result = self.send_guided_flow_request(scenario["query"])
        
        if not result["success"]:
            print_error(f"Request failed: {result['error']}")
            return {"scenario": scenario_key, "success": False, "error": result["error"]}

        # Validate response
        validation = self.validate_guided_flow(result, scenario)
        
        # Print results
        data = result["data"]
        packages = data.get("packages", [])
        
        if packages:
            print_success(f"Received {len(packages)} package(s)")
        else:
            print_warning("No packages returned")
            
        # Print validation results
        print(f"\n{Colors.BOLD}Guided Flow Validation:{Colors.END}")
        for check, passed in validation.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
        
        if self.verbose:
            self.print_guided_flow_details(data)

        # Calculate success score
        passed_checks = sum(validation.values())
        total_checks = len(validation)
        success_rate = passed_checks / total_checks if total_checks > 0 else 0

        print_result("Success Rate", f"{success_rate:.1%} ({passed_checks}/{total_checks})")
        print_result("Response Time", f"{result['response_time']:.2f}s")

        return {
            "scenario": scenario_key,
            "success": result["success"],
            "validation": validation,
            "success_rate": success_rate,
            "response_time": result["response_time"],
            "package_count": len(packages),
            "data": data
        }

    def run_all_tests(self, specific_scenario: str = None) -> Dict[str, Any]:
        """Run all guided flow tests or a specific one"""
        print_header("Guided Flow Test Suite")
        print_info(f"Testing against: {BASE_URL}")
        print_info(f"Session ID: {self.session_id}")
        
        # Check server health first
        if not self.check_server_health():
            print_error("Server health check failed. Cannot proceed with tests.")
            return {"success": False, "error": "Server not healthy"}

        # Run tests
        test_results = []
        scenarios_to_test = {specific_scenario: GUIDED_FLOW_SCENARIOS[specific_scenario]} if specific_scenario else GUIDED_FLOW_SCENARIOS

        for scenario_key, scenario in scenarios_to_test.items():
            try:
                result = self.run_scenario_test(scenario_key, scenario)
                test_results.append(result)
                
                # Small delay between tests
                if len(scenarios_to_test) > 1:
                    time.sleep(1)
                    
            except Exception as e:
                print_error(f"Test failed with exception: {e}")
                test_results.append({
                    "scenario": scenario_key,
                    "success": False,
                    "error": str(e)
                })

        # Print summary
        self.print_test_summary(test_results)
        
        return {
            "success": True,
            "test_results": test_results,
            "summary": self.calculate_summary(test_results)
        }

    def calculate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall test summary"""
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get("success", False))
        
        avg_success_rate = 0
        avg_response_time = 0
        total_packages = 0
        guided_flow_activated = 0
        
        valid_results = [r for r in test_results if r.get("success", False)]
        if valid_results:
            avg_success_rate = sum(r.get("success_rate", 0) for r in valid_results) / len(valid_results)
            avg_response_time = sum(r.get("response_time", 0) for r in valid_results) / len(valid_results)
            total_packages = sum(r.get("package_count", 0) for r in valid_results)
            
            # Count how many tests successfully activated guided flow
            for result in valid_results:
                validation = result.get("validation", {})
                if validation.get("guided_flow_activated", False):
                    guided_flow_activated += 1

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_percentage": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_success_rate": avg_success_rate,
            "avg_response_time": avg_response_time,
            "total_packages_generated": total_packages,
            "guided_flow_activation_rate": (guided_flow_activated / total_tests * 100) if total_tests > 0 else 0
        }

    def print_test_summary(self, test_results: List[Dict[str, Any]]):
        """Print comprehensive test summary"""
        print_header("Guided Flow Test Summary")
        
        summary = self.calculate_summary(test_results)
        
        print_result("Total Tests Run", summary["total_tests"])
        print_result("Successful Tests", f"{summary['successful_tests']}/{summary['total_tests']}")
        print_result("Overall Success", f"{summary['success_percentage']:.1f}%")
        print_result("Avg Validation Rate", f"{summary['avg_success_rate']:.1%}")
        print_result("Avg Response Time", f"{summary['avg_response_time']:.2f}s")
        print_result("Total Packages Generated", summary["total_packages_generated"])
        print_result("Guided Flow Activation", f"{summary['guided_flow_activation_rate']:.1f}%")
        
        # Individual test results
        print(f"\n{Colors.BOLD}Individual Test Results:{Colors.END}")
        for result in test_results:
            scenario_name = GUIDED_FLOW_SCENARIOS.get(result["scenario"], {}).get("name", result["scenario"])
            if result.get("success"):
                success_rate = result.get("success_rate", 0)
                response_time = result.get("response_time", 0)
                validation = result.get("validation", {})
                guided_flow = "✅" if validation.get("guided_flow_activated") else "❌"
                print_success(f"{scenario_name}: {success_rate:.1%} validation, {response_time:.2f}s, Guided Flow: {guided_flow}")
            else:
                error = result.get("error", "Unknown error")
                print_error(f"{scenario_name}: {error}")

        # Overall assessment specific to guided flow
        guided_flow_rate = summary["guided_flow_activation_rate"]
        if guided_flow_rate >= 80:
            print_success("\n🎉 Guided flow is working correctly!")
        elif guided_flow_rate >= 60:
            print_warning("\n⚠️  Guided flow has some issues but is partially functional")
        else:
            print_error("\n🚨 Guided flow is not activating properly")

def main():
    parser = argparse.ArgumentParser(description="Test the guided flow functionality")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--scenario", "-s", choices=list(GUIDED_FLOW_SCENARIOS.keys()), 
                       help="Run a specific test scenario")
    parser.add_argument("--export", "-e", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    # Run tests
    tester = GuidedFlowTester(verbose=args.verbose)
    results = tester.run_all_tests(specific_scenario=args.scenario)
    
    # Export results if requested
    if args.export and results.get("success"):
        try:
            with open(args.export, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print_success(f"Results exported to {args.export}")
        except Exception as e:
            print_error(f"Failed to export results: {e}")
    
    # Exit with appropriate code
    if results.get("success"):
        summary = results.get("summary", {})
        if summary.get("guided_flow_activation_rate", 0) >= 80:
            exit(0)  # Success
        else:
            exit(1)  # Partial success
    else:
        exit(2)  # Failure

if __name__ == "__main__":
    main()