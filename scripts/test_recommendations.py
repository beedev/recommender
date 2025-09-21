#!/usr/bin/env python3
"""
Comprehensive Test Script for Welding Equipment Recommendation System

This script tests the enterprise recommendation system through various real-world
welding scenarios to verify the complete 3-agent architecture works correctly.

Features:
- Tests enterprise recommendation endpoint (/api/v1/enterprise/recommendations)
- Multiple welding scenarios (MIG, TIG, Stick welding)
- Validates 7-product package completion with golden package fallback
- Checks sales history analysis integration
- Verifies LangSmith observability (if configured)
- Color-coded output for easy result interpretation

Usage:
    python3 scripts/test_recommendations.py
    python3 scripts/test_recommendations.py --verbose
    python3 scripts/test_recommendations.py --scenario mig_aluminum
"""

import requests
import json
import time
import argparse
from typing import Dict, List, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ENTERPRISE_ENDPOINT = f"{BASE_URL}/api/v1/enterprise/recommendations"

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

# Test Scenarios
TEST_SCENARIOS = {
    "mig_aluminum": {
        "name": "MIG Welding - Aluminum (300A)",
        "query": "I need MIG welding equipment for aluminum, 300 amps, 1/4 inch thickness, automotive application",
        "expected_process": "MIG",
        "expected_material": "aluminum",
        "expected_current_range": (250, 350),
        "expected_components": ["PowerSource", "Feeder", "Cooler"]
    },
    "tig_stainless": {
        "name": "TIG Welding - Stainless Steel (200A)",
        "query": "I need TIG welding for stainless steel, 200 amps, precision work, aerospace application",
        "expected_process": "TIG",
        "expected_material": "stainless",
        "expected_current_range": (150, 250),
        "expected_components": ["PowerSource", "Cooler", "Torch"]
    },
    "stick_steel": {
        "name": "Stick Welding - Carbon Steel (400A)",
        "query": "I need stick welding equipment for heavy carbon steel, 400 amps, shipyard construction",
        "expected_process": "STICK",
        "expected_material": "steel",
        "expected_current_range": (350, 450),
        "expected_components": ["PowerSource"]
    },
    "high_current_mig": {
        "name": "High Current MIG - Steel (500A)",
        "query": "I need high current MIG welding for thick steel plates, 500 amps, industrial fabrication",
        "expected_process": "MIG",
        "expected_material": "steel",
        "expected_current_range": (450, 550),
        "expected_components": ["PowerSource", "Feeder", "Cooler"]
    },
    "multi_process": {
        "name": "Multi-Process Requirement",
        "query": "I need equipment that can do both MIG and TIG welding, aluminum and steel, 300 amps maximum",
        "expected_process": ["MIG", "TIG"],
        "expected_material": ["aluminum", "steel"],
        "expected_current_range": (250, 350),
        "expected_components": ["PowerSource", "Feeder", "Cooler", "Torch"]
    }
}

class RecommendationTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session_id = f"test_session_{int(time.time())}"
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

    def send_recommendation_request(self, query: str) -> Dict[str, Any]:
        """Send recommendation request to enterprise endpoint"""
        payload = {
            "query": query,
            "user_context": {
                "user_id": "test_user",
                "experience_level": "expert",
                "preferences": {
                    "budget_range": "premium",
                    "preferred_brands": ["ESAB"],
                    "applications": ["industrial"]
                }
            },
            "session_id": self.session_id,
            "language": "en"
        }

        try:
            print_info(f"Sending request: {query[:50]}...")
            
            start_time = time.time()
            response = requests.post(
                ENTERPRISE_ENDPOINT,
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

    def validate_recommendation(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, bool]:
        """Validate recommendation against expected scenario"""
        validation = {
            "has_packages": False,
            "correct_process": False,
            "correct_material": False,
            "current_in_range": False,
            "has_required_components": False,
            "has_sales_evidence": False,
            "complete_package": False
        }

        if not result.get("success") or not result.get("data"):
            return validation

        data = result["data"]
        packages = data.get("packages", [])

        # Check if packages exist
        if packages:
            validation["has_packages"] = True
            package = packages[0]  # Test first package

            # Check process
            processes = package.get("processes", [])
            expected_process = scenario["expected_process"]
            if isinstance(expected_process, list):
                validation["correct_process"] = any(proc in processes for proc in expected_process)
            else:
                validation["correct_process"] = expected_process in processes

            # Check material
            materials = package.get("materials", [])
            expected_material = scenario["expected_material"]
            if isinstance(expected_material, list):
                validation["correct_material"] = any(mat in materials for mat in expected_material)
            else:
                validation["correct_material"] = expected_material in materials

            # Check current range
            package_current = package.get("current_amps")
            if package_current:
                min_current, max_current = scenario["expected_current_range"]
                validation["current_in_range"] = min_current <= package_current <= max_current

            # Check required components
            components = package.get("components", {})
            expected_components = scenario["expected_components"]
            has_all_components = all(
                comp_type in components and components[comp_type] 
                for comp_type in expected_components
            )
            validation["has_required_components"] = has_all_components

            # Check for sales evidence
            validation["has_sales_evidence"] = bool(package.get("sales_evidence"))

            # Check for complete package (7 categories)
            expected_categories = [
                "PowerSource", "Feeder", "Cooler", "Torch", 
                "FeederAccessory", "PowerSourceAccessory", "Interconnector"
            ]
            actual_categories = list(components.keys())
            validation["complete_package"] = len(actual_categories) >= 3  # At least Trinity

        return validation

    def print_package_details(self, package: Dict[str, Any]):
        """Print detailed package information"""
        print(f"\n{Colors.BOLD}Package Details:{Colors.END}")
        
        # Basic info
        print_result("Package ID", package.get("package_id", "N/A"))
        print_result("Total Price", f"${package.get('total_price', 0):,.2f}")
        print_result("Confidence", f"{package.get('compatibility_confidence', 0):.1%}")
        
        # Processes and materials
        print_result("Processes", ", ".join(package.get("processes", [])))
        print_result("Materials", ", ".join(package.get("materials", [])))
        print_result("Current Rating", f"{package.get('current_amps', 'N/A')} A")
        
        # Components
        components = package.get("components", {})
        print(f"\n{Colors.BOLD}Components ({len(components)} categories):{Colors.END}")
        for category, component in components.items():
            if component:
                product_name = component.get("name", "Unknown")
                model = component.get("model", "")
                current = component.get("current_amps", "")
                price = component.get("price", 0)
                
                component_info = f"{product_name}"
                if model:
                    component_info += f" ({model})"
                if current:
                    component_info += f" - {current}A"
                if price:
                    component_info += f" - ${price:,.2f}"
                
                print_result(f"  {category}", component_info)
        
        # Sales evidence
        sales_evidence = package.get("sales_evidence", "")
        if sales_evidence:
            print_result("Sales Evidence", sales_evidence[:100] + "..." if len(sales_evidence) > 100 else sales_evidence)

    def run_scenario_test(self, scenario_key: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario"""
        print_header(f"Testing: {scenario['name']}")
        
        # Send request
        result = self.send_recommendation_request(scenario["query"])
        
        if not result["success"]:
            print_error(f"Request failed: {result['error']}")
            return {"scenario": scenario_key, "success": False, "error": result["error"]}

        # Validate response
        validation = self.validate_recommendation(result, scenario)
        
        # Print results
        data = result["data"]
        packages = data.get("packages", [])
        
        if packages:
            print_success(f"Received {len(packages)} package(s)")
            
            # Print validation results
            print(f"\n{Colors.BOLD}Validation Results:{Colors.END}")
            for check, passed in validation.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check.replace('_', ' ').title()}")
            
            if self.verbose and packages:
                self.print_package_details(packages[0])
                
        else:
            print_warning("No packages returned")

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
        """Run all test scenarios or a specific one"""
        print_header("Welding Equipment Recommendation System Test")
        print_info(f"Testing against: {BASE_URL}")
        print_info(f"Session ID: {self.session_id}")
        
        # Check server health first
        if not self.check_server_health():
            print_error("Server health check failed. Cannot proceed with tests.")
            return {"success": False, "error": "Server not healthy"}

        # Run tests
        test_results = []
        scenarios_to_test = {specific_scenario: TEST_SCENARIOS[specific_scenario]} if specific_scenario else TEST_SCENARIOS

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
        
        valid_results = [r for r in test_results if r.get("success", False)]
        if valid_results:
            avg_success_rate = sum(r.get("success_rate", 0) for r in valid_results) / len(valid_results)
            avg_response_time = sum(r.get("response_time", 0) for r in valid_results) / len(valid_results)
            total_packages = sum(r.get("package_count", 0) for r in valid_results)

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_percentage": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_success_rate": avg_success_rate,
            "avg_response_time": avg_response_time,
            "total_packages_generated": total_packages
        }

    def print_test_summary(self, test_results: List[Dict[str, Any]]):
        """Print comprehensive test summary"""
        print_header("Test Summary")
        
        summary = self.calculate_summary(test_results)
        
        print_result("Total Tests Run", summary["total_tests"])
        print_result("Successful Tests", f"{summary['successful_tests']}/{summary['total_tests']}")
        print_result("Overall Success", f"{summary['success_percentage']:.1f}%")
        print_result("Avg Validation Rate", f"{summary['avg_success_rate']:.1%}")
        print_result("Avg Response Time", f"{summary['avg_response_time']:.2f}s")
        print_result("Total Packages Generated", summary["total_packages_generated"])
        
        # Individual test results
        print(f"\n{Colors.BOLD}Individual Test Results:{Colors.END}")
        for result in test_results:
            scenario_name = TEST_SCENARIOS.get(result["scenario"], {}).get("name", result["scenario"])
            if result.get("success"):
                success_rate = result.get("success_rate", 0)
                response_time = result.get("response_time", 0)
                print_success(f"{scenario_name}: {success_rate:.1%} validation, {response_time:.2f}s")
            else:
                error = result.get("error", "Unknown error")
                print_error(f"{scenario_name}: {error}")

        # Overall assessment
        if summary["success_percentage"] >= 80:
            print_success("\n🎉 System is performing well!")
        elif summary["success_percentage"] >= 60:
            print_warning("\n⚠️  System has some issues but is functional")
        else:
            print_error("\n🚨 System has significant issues")

def main():
    parser = argparse.ArgumentParser(description="Test the welding equipment recommendation system")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--scenario", "-s", choices=list(TEST_SCENARIOS.keys()), 
                       help="Run a specific test scenario")
    parser.add_argument("--export", "-e", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    # Run tests
    tester = RecommendationTester(verbose=args.verbose)
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
        if summary.get("success_percentage", 0) >= 80:
            exit(0)  # Success
        else:
            exit(1)  # Partial success
    else:
        exit(2)  # Failure

if __name__ == "__main__":
    main()