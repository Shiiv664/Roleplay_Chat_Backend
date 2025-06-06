"""Pagination parsers for list endpoints."""

from flask_restx import reqparse

# Pagination parser for list endpoints
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument("page", type=int, default=1, help="Page number")
pagination_parser.add_argument("page_size", type=int, default=20, help="Items per page")

# Search parser for search endpoints
search_parser = reqparse.RequestParser()
search_parser.add_argument("query", type=str, required=True, help="Search query")
search_parser.add_argument("page", type=int, default=1, help="Page number")
search_parser.add_argument("page_size", type=int, default=20, help="Items per page")
