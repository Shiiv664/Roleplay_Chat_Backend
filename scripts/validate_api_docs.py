#!/usr/bin/env python3
"""
API Documentation Validation Script.

This script validates that the API documentation (JSON and HTML) is synchronized
and properly reflects the current state of the API endpoints.

Usage:
    python scripts/validate_api_docs.py [--host HOST] [--port PORT] [--verbose]
"""

import argparse
import json
import sys
import time
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class APIDocumentationValidator:
    """Validates API documentation consistency and accessibility."""

    def __init__(self, base_url: str, verbose: bool = False):
        """Initialize the validator."""
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.session = self._create_session()
        self.errors = []
        self.warnings = []

    def _create_session(self):
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _log(self, message: str, level: str = "INFO"):
        """Log a message if verbose mode is enabled."""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def _add_error(self, message: str):
        """Add an error to the error list."""
        self.errors.append(message)
        self._log(message, "ERROR")

    def _add_warning(self, message: str):
        """Add a warning to the warning list."""
        self.warnings.append(message)
        self._log(message, "WARNING")

    def validate_json_accessibility(self) -> bool:
        """Validate that the JSON API specification is accessible."""
        self._log("Validating JSON API specification accessibility...")

        try:
            url = f"{self.base_url}/api/v1/swagger.json"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                self._add_error(
                    f"JSON API spec not accessible: {response.status_code} at {url}"
                )
                return False

            if "application/json" not in response.headers.get("content-type", ""):
                self._add_error(
                    f"JSON API spec has wrong content type: {response.headers.get('content-type')}"
                )
                return False

            # Validate JSON structure
            try:
                swagger_data = response.json()
                if "swagger" not in swagger_data or "paths" not in swagger_data:
                    self._add_error(
                        "JSON API spec missing required fields (swagger, paths)"
                    )
                    return False

                endpoint_count = len(swagger_data["paths"])
                if endpoint_count < 10:  # Sanity check
                    self._add_warning(
                        f"Low endpoint count in JSON spec: {endpoint_count}"
                    )

                self._log(f"JSON API spec valid with {endpoint_count} endpoints")
                return True

            except json.JSONDecodeError as e:
                self._add_error(f"Invalid JSON in API spec: {e}")
                return False

        except requests.RequestException as e:
            self._add_error(f"Failed to fetch JSON API spec: {e}")
            return False

    def validate_html_accessibility(self) -> bool:
        """Validate that the HTML documentation is accessible."""
        self._log("Validating HTML documentation accessibility...")

        try:
            url = f"{self.base_url}/api/v1/docs"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                self._add_error(
                    f"HTML docs not accessible: {response.status_code} at {url}"
                )
                return False

            if "text/html" not in response.headers.get("content-type", ""):
                self._add_error(
                    f"HTML docs have wrong content type: {response.headers.get('content-type')}"
                )
                return False

            # Basic HTML validation
            html_content = response.text
            required_elements = ["swagger-ui", "Roleplay Chat API"]

            for element in required_elements:
                if element not in html_content:
                    self._add_error(f"HTML docs missing required element: {element}")
                    return False

            self._log("HTML documentation is accessible and valid")
            return True

        except requests.RequestException as e:
            self._add_error(f"Failed to fetch HTML docs: {e}")
            return False

    def validate_endpoint_consistency(self) -> bool:
        """Validate that documented endpoints actually work."""
        self._log("Validating endpoint consistency...")

        try:
            # Get the JSON spec first
            swagger_response = self.session.get(
                f"{self.base_url}/api/v1/swagger.json", timeout=10
            )
            if swagger_response.status_code != 200:
                self._add_error("Cannot validate endpoints: JSON spec not accessible")
                return False

            swagger_data = swagger_response.json()
            paths = swagger_data.get("paths", {})

            # Test a few key endpoints
            test_endpoints = [
                ("/characters/", "GET"),
                ("/ai-models/", "GET"),
                ("/user-profiles/", "GET"),
                ("/system-prompts/", "GET"),
            ]

            success_count = 0
            for path, method in test_endpoints:
                if path in paths and method.lower() in paths[path]:
                    try:
                        url = f"{self.base_url}/api/v1{path}"
                        response = self.session.get(url, timeout=5)

                        # Accept 200 or 404 (empty database is OK)
                        if response.status_code in [200, 404]:
                            success_count += 1
                            self._log(
                                f"Endpoint {path} responding correctly ({response.status_code})"
                            )
                        else:
                            self._add_warning(
                                f"Endpoint {path} returned unexpected status: {response.status_code}"
                            )

                    except requests.RequestException as e:
                        self._add_warning(f"Failed to test endpoint {path}: {e}")
                else:
                    self._add_warning(
                        f"Endpoint {path} {method} not found in documentation"
                    )

            if success_count >= len(test_endpoints) // 2:  # At least half should work
                self._log(
                    f"Endpoint consistency check passed ({success_count}/{len(test_endpoints)})"
                )
                return True
            else:
                self._add_error(
                    f"Too many endpoint failures ({success_count}/{len(test_endpoints)})"
                )
                return False

        except Exception as e:
            self._add_error(f"Endpoint consistency validation failed: {e}")
            return False

    def validate_api_server_running(self) -> bool:
        """Validate that the API server is running and responding."""
        self._log("Checking if API server is running...")

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("app") == "LLM Roleplay Chat Client API":
                    self._log("API server is running and responding correctly")
                    return True
                else:
                    self._add_error("API server responding but with unexpected content")
                    return False
            else:
                self._add_error(
                    f"API server not responding correctly: {response.status_code}"
                )
                return False

        except requests.RequestException as e:
            self._add_error(f"Cannot reach API server: {e}")
            return False

    def run_validation(self) -> bool:
        """Run all validation checks."""
        self._log("Starting API documentation validation...")

        validations = [
            ("API Server", self.validate_api_server_running),
            ("JSON Accessibility", self.validate_json_accessibility),
            ("HTML Accessibility", self.validate_html_accessibility),
            ("Endpoint Consistency", self.validate_endpoint_consistency),
        ]

        results = {}
        for name, validation_func in validations:
            self._log(f"Running {name} validation...")
            results[name] = validation_func()

        # Summary
        passed = sum(results.values())
        total = len(results)

        print(f"\n{'='*50}")
        print("VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Passed: {passed}/{total}")

        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{name}: {status}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        overall_success = (
            len(self.errors) == 0 and passed >= total - 1
        )  # Allow one warning

        if overall_success:
            print("\n✅ Overall: VALIDATION PASSED")
        else:
            print("\n❌ Overall: VALIDATION FAILED")

        return overall_success


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate API documentation consistency"
    )
    parser.add_argument(
        "--host", default="localhost", help="API server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="API server port (default: 5000)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    validator = APIDocumentationValidator(base_url, verbose=args.verbose)

    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
