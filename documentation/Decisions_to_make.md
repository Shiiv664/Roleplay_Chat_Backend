1. Database Schema Evolution Strategy
    - How to handle breaking changes in the schema
    - Policy for data migration during schema changes
    - Whether to use Alembic for data migrations or separate scripts
  2. Transaction Management Approach
    - Whether to use explicit transaction boundaries or implicit ones
    - How to handle transaction retries for certain error conditions
    - Transaction isolation levels for different operations
  3. API Authentication/Authorization
    - Even for a local app, will you implement any authentication?
    - How will different API endpoints be protected, if at all?
    - Whether to use API keys, tokens, or other methods
  4. Backend Performance Considerations
    - Database indexing strategy
    - Query optimization guidelines
    - Caching approach (if any)
  5. Deployment & Configuration Strategy
    - How configuration will be managed across environments
    - Environment variables vs. config files
    - Secret management approach
  6. Development Workflow
    - Git branching strategy and commit conventions
    - Pull request and code review processes
    - Version numbering scheme
  7. Dependencies Management
    - Tool for dependency management (pip, poetry, etc.)
    - Policy for dependency updates and security patches
    - Approach to handling dependency conflicts