# OpenAPI Specification Usage

This document explains how to generate and use the OpenAPI (Swagger) specification for this API.

## What is the OpenAPI Specification?

The OpenAPI Specification (OAS) defines a standard, language-agnostic interface to RESTful APIs which allows both humans and computers to discover and understand the capabilities of the service without access to source code, documentation, or through network traffic inspection.

## Generating the OpenAPI Specification

You can generate the OpenAPI specification file using the provided script:

```bash
# Make sure your Flask application is running first!

# Export as JSON (default)
python scripts/export_openapi.py

# Export as pretty-printed JSON
python scripts/export_openapi.py --pretty

# Export as YAML (requires PyYAML)
python scripts/export_openapi.py --format yaml

# Specify a custom API URL (if not running on localhost:5000)
python scripts/export_openapi.py --url http://yourapi.example.com

# Specify a custom output path
python scripts/export_openapi.py --output path/to/openapi.json
```

By default, the specification is exported to `documentation/api/openapi.json`.

**Note:** The script requires the Flask application to be running when executed, as it fetches the specification directly from the Swagger endpoint.

## Using the OpenAPI Specification

Once you have the OpenAPI specification file, you can use it in various ways:

1. **Frontend Development**: Import the specification into your frontend tooling to generate client SDKs or interfaces.

2. **Documentation**: Use tools like [Swagger UI](https://swagger.io/tools/swagger-ui/) or [ReDoc](https://github.com/Redocly/redoc) to render beautiful, interactive API documentation.

3. **Testing**: Use tools like [Postman](https://www.postman.com/) or [Insomnia](https://insomnia.rest/) to import the spec and test your API.

4. **Mock Servers**: Generate mock servers based on the specification for frontend development without needing the real backend.

## Online Viewing

You can also view the live Swagger UI documentation by accessing the running application at:

```
http://localhost:5000/api/v1/docs
```

## Example: Generating TypeScript Client

If you're using TypeScript for your frontend, you can generate a client SDK using tools like [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen):

```bash
# Install the tool
npm install openapi-typescript-codegen --save-dev

# Generate the client
npx openapi-typescript-codegen --input documentation/api/openapi.json --output src/api-client
```

This will generate a fully typed API client based on the OpenAPI specification.
