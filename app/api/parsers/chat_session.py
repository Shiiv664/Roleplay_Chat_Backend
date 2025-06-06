"""Parsers for Chat Session API endpoints."""

from flask_restx import reqparse

# Parser for recent sessions endpoint
recent_sessions_parser = reqparse.RequestParser()
recent_sessions_parser.add_argument(
    "limit", type=int, default=10, help="Maximum number of recent sessions to return"
)
