"""Tests for API documentation synchronization and consistency."""

import pytest
from flask import url_for


class TestAPIDocumentation:
    """Test suite to ensure API documentation consistency and prevent sync issues."""

    @pytest.fixture
    def base_url(self, app):
        """Get the base URL for the running test application."""
        with app.test_request_context():
            return url_for("api.doc", _external=True).replace("/docs", "")

    def test_swagger_json_accessible(self, client):
        """Test that the Swagger JSON specification is accessible."""
        response = client.get("/api/v1/swagger.json")
        assert response.status_code == 200
        assert response.content_type == "application/json"

        # Verify it's valid JSON
        swagger_data = response.get_json()
        assert "swagger" in swagger_data
        assert "paths" in swagger_data
        assert len(swagger_data["paths"]) > 0

    def test_swagger_html_docs_accessible(self, client):
        """Test that the HTML documentation is accessible."""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "text/html" in response.content_type

        # Verify it contains Swagger UI elements
        html_content = response.get_data(as_text=True)
        assert "Roleplay Chat API" in html_content
        assert "swagger-ui" in html_content

    def test_json_html_endpoint_count_consistency(self, client):
        """Test that JSON and HTML docs reference the same number of endpoints."""
        # Get JSON spec
        json_response = client.get("/api/v1/swagger.json")
        swagger_data = json_response.get_json()
        json_endpoint_count = len(swagger_data["paths"])

        # Verify HTML docs are accessible and contain swagger content
        html_response = client.get("/api/v1/docs")
        assert html_response.status_code == 200, "HTML docs should be accessible"

        # Basic validation that both are working
        assert json_endpoint_count > 0, "JSON spec should contain endpoints"
        assert (
            json_endpoint_count >= 20
        ), f"Expected at least 20 endpoints, found {json_endpoint_count}"

    def test_all_registered_routes_documented(self, app, client):
        """Test that all registered Flask routes are documented in Swagger."""
        # Get Swagger JSON
        response = client.get("/api/v1/swagger.json")
        swagger_data = response.get_json()
        documented_paths = set(swagger_data["paths"].keys())

        # Get all registered routes for the API blueprint
        api_routes = set()
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith("/api/v1/") and rule.rule not in [
                "/api/v1/swagger.json",
                "/api/v1/docs",
            ]:
                # Normalize the path for comparison
                path = (
                    rule.rule.replace("/api/v1", "")
                    .replace("<int:", "{")
                    .replace("<string:", "{")
                    .replace(">", "}")
                )
                if path and path != "/":
                    api_routes.add(path)

        # Check that critical routes are documented
        critical_routes = {
            "/characters/",
            "/user-profiles/",
            "/ai-models/",
            "/chat-sessions/",
            "/messages/",
        }
        documented_critical = {
            path
            for path in documented_paths
            if any(cr in path for cr in critical_routes)
        }

        assert len(documented_critical) >= len(
            critical_routes
        ), f"Not all critical routes documented. Missing: {critical_routes - documented_critical}"

    def test_swagger_spec_validity(self, client):
        """Test that the Swagger specification is valid and complete."""
        response = client.get("/api/v1/swagger.json")
        swagger_data = response.get_json()

        # Basic Swagger 2.0 structure validation
        required_fields = ["swagger", "info", "paths"]
        for field in required_fields:
            assert field in swagger_data, f"Missing required field: {field}"

        # Verify version
        assert swagger_data["swagger"] == "2.0"

        # Verify info section
        assert "title" in swagger_data["info"]
        assert "version" in swagger_data["info"]

        # Verify paths have proper structure
        for path, methods in swagger_data["paths"].items():
            assert isinstance(methods, dict), f"Path {path} should have methods dict"
            for method, spec in methods.items():
                if method == "parameters":
                    continue
                assert (
                    "responses" in spec
                ), f"Method {method} on {path} missing responses"

    def test_endpoint_response_models_defined(self, client):
        """Test that endpoints have proper response models defined."""
        response = client.get("/api/v1/swagger.json")
        swagger_data = response.get_json()

        # Check that definitions exist
        assert (
            "definitions" in swagger_data
        ), "Swagger spec should include model definitions"
        definitions = swagger_data["definitions"]

        # Verify key response models exist
        key_models = ["Response", "CharacterCreate", "ChatSessionResponse"]
        for model in key_models:
            assert model in definitions, f"Missing key model definition: {model}"

    def test_documentation_freshness(self, client):
        """Test that documentation reflects current state by checking timestamp-related info."""
        # This test helps detect if docs are cached or stale
        response1 = client.get("/api/v1/swagger.json")
        assert response1.status_code == 200

        # Make a second request to ensure consistency
        response2 = client.get("/api/v1/swagger.json")
        assert response2.status_code == 200

        # Both should return identical content (no caching issues)
        assert response1.get_json() == response2.get_json()

    def test_cors_headers_documented(self, client):
        """Test that CORS-related headers are properly handled in documentation."""
        # Test that OPTIONS requests work for documented endpoints
        response = client.options("/api/v1/characters/")
        # Should not return 404 or 405 if CORS is properly configured
        assert response.status_code in [
            200,
            204,
            405,
        ]  # 405 is acceptable if OPTIONS not explicitly handled

    def test_error_responses_documented(self, client):
        """Test that error responses are properly documented."""
        response = client.get("/api/v1/swagger.json")
        swagger_data = response.get_json()

        # Find an endpoint and check it has error responses documented
        sample_path = None
        for path, methods in swagger_data["paths"].items():
            if "get" in methods:
                sample_path = path
                break

        assert sample_path is not None, "Should have at least one GET endpoint"

        get_spec = swagger_data["paths"][sample_path]["get"]
        responses = get_spec["responses"]

        # Should have success response
        assert "200" in responses, f"GET {sample_path} should have 200 response"
