# API Documentation

This document provides guidance on the API documentation strategy used in the Roleplay Chat Web App.

## Automatic API Documentation with Flask-RESTX

The application uses Flask-RESTX to automatically generate interactive API documentation in the form of a Swagger UI.

### Benefits

- **Interactive Documentation**: Provides a user-friendly interface for exploring and testing API endpoints
- **Code-First Approach**: Documentation is generated from code annotations, ensuring it stays in sync with implementation
- **Request/Response Validation**: Validates requests and responses against defined models
- **Client SDK Generation**: Tools can use the Swagger specification to generate client libraries

### Implementation

The API is structured around Flask-RESTX namespaces, each corresponding to a resource group:

```python
# Example namespace setup in api/__init__.py
from flask_restx import Api

api = Api(
    version='1.0',
    title='Roleplay Chat API',
    description='API for the Roleplay Chat Web App',
    doc='/api/docs'  # Swagger UI will be available at this endpoint
)

# Add namespaces
from .namespaces.character_namespace import character_ns
from .namespaces.user_profile_namespace import user_profile_ns
# ... other namespaces

api.add_namespace(character_ns)
api.add_namespace(user_profile_ns)
# ... add other namespaces
```

### Namespaces and Models

Each API resource has:

1. **Namespace**: Groups related endpoints
2. **Models**: Defines request/response data structures
3. **Routes**: Endpoint implementations with documentation

```python
# Example namespace definition (api/namespaces/character_namespace.py)
from flask_restx import Namespace, Resource, fields

character_ns = Namespace('characters', description='Character operations')

# Model definitions
character_model = character_ns.model('Character', {
    'id': fields.Integer(readonly=True, description='The character identifier'),
    'label': fields.String(required=True, description='Unique label for the character'),
    'name': fields.String(required=True, description='Display name of the character'),
    'avatar_image': fields.String(description='Path to character avatar image'),
    'description': fields.String(description='Character description')
})

character_list_model = character_ns.model('CharacterList', {
    'characters': fields.List(fields.Nested(character_model)),
    'count': fields.Integer
})

# Route definitions with documentation
@character_ns.route('/')
class CharacterList(Resource):
    @character_ns.doc('list_characters')
    @character_ns.marshal_list_with(character_model)
    def get(self):
        """List all characters"""
        # Implementation...

    @character_ns.doc('create_character')
    @character_ns.expect(character_model)
    @character_ns.marshal_with(character_model, code=201)
    def post(self):
        """Create a new character"""
        # Implementation...
```

### Accessing the Documentation

The Swagger UI will be available at `/api/docs` when the application is running.

### Supplementary Documentation

While Flask-RESTX generates interactive documentation automatically, this repository still maintains manual documentation:

1. **API Endpoint Overview**: Found in `technical_architecture.md`
2. **This Reference**: Provides guidance on the documentation approach

### API Versioning

The API will include version information in:
1. The API's base path (e.g., `/api/v1/`)
2. The Swagger documentation title and metadata

## Best Practices

When implementing new API endpoints:

1. **Document All Parameters**: Include descriptions for all path, query, and body parameters
2. **Define Response Models**: Create models for all response structures
3. **Include Example Values**: Add example values to model fields where helpful
4. **Document Error Responses**: Define models for error responses
5. **Use Standard HTTP Status Codes**: Follow REST conventions for status codes

## Integration with Frontend

The frontend will utilize the API documentation to:
1. Understand available endpoints
2. Validate request/response formats
3. Test API interactions before implementation

This ensures the frontend and backend remain in sync throughout development.
