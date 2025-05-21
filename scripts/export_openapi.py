#!/usr/bin/env python3
"""Simple script to export the OpenAPI specification by accessing the Swagger endpoint."""

import argparse
import json
import os
import sys

import requests
import yaml


def export_openapi(url, output_file, format_type="json", pretty=False):
    """Export the OpenAPI specification to a file by accessing the Swagger endpoint.

    Args:
        url: The base URL of the API
        output_file: Path to the output file
        format_type: 'json' or 'yaml'
        pretty: Whether to pretty print the JSON (only applies to JSON format)
    """
    # Construct the Swagger endpoint URL
    swagger_url = f"{url.rstrip('/')}/api/v1/swagger.json"

    try:
        # Get the OpenAPI specification from the Swagger endpoint
        response = requests.get(swagger_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        openapi_spec = response.json()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Write the OpenAPI specification to a file
        if format_type.lower() == "yaml":
            with open(output_file, "w") as f:
                yaml.dump(openapi_spec, f, default_flow_style=False)
        else:  # JSON format
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(openapi_spec, f, indent=2, sort_keys=True)
                else:
                    json.dump(openapi_spec, f)

        print(f"OpenAPI specification exported to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error accessing {swagger_url}: {e}")
        print("Make sure the server is running and the URL is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"Error exporting OpenAPI specification: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI specification to a file"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="Base URL of the API (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="documentation/api/openapi.json",
        help="Output file path (default: documentation/api/openapi.json)",
    )
    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty print the JSON output (only applies to JSON format)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format: json or yaml (default: json)",
    )

    args = parser.parse_args()

    # Update the file extension based on the format
    output_file = args.output
    if (
        args.format == "yaml"
        and not output_file.endswith(".yaml")
        and not output_file.endswith(".yml")
    ):
        output_file = output_file.rsplit(".", 1)[0] + ".yaml"
    elif args.format == "json" and not output_file.endswith(".json"):
        output_file = output_file.rsplit(".", 1)[0] + ".json"

    export_openapi(args.url, output_file, args.format, args.pretty)


if __name__ == "__main__":
    main()
