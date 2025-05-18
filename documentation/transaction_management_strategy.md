# Transaction Management Strategy

This document outlines the approach to managing database transactions in the Roleplay Chat Web App. Proper transaction management is crucial for ensuring data consistency, integrity, and application reliability.

## Core Principles

1. **Data Integrity**: Prevent data corruption and inconsistencies
2. **Predictable Behavior**: Ensure transactions behave consistently
3. **Error Handling**: Properly handle transaction failures
4. **Simplicity**: Favor clear, straightforward transaction patterns
5. **Performance**: Be mindful of transaction duration and scope

## Transaction Boundaries

### Explicit Transaction Management

The application will use **explicit transaction boundaries** rather than relying on implicit commits. This provides clear control over the unit of work.

#### Service Layer Transaction Control

Transactions should be managed primarily at the service layer, which represents a single unit of business logic:

```python
class CharacterService:
    def __init__(self, session):
        self.session = session
        self.repo = CharacterRepository(session)
    
    def create_character(self, data):
        try:
            # Validate data
            if not self._validate_character_data(data):
                raise ValidationError("Invalid character data")
            
            # Perform database operations
            character = self.repo.create(data)
            
            # Commit the transaction
            self.session.commit()
            
            return character
        except Exception as e:
            # Rollback on any exception
            self.session.rollback()
            # Re-raise the exception or transform to application-specific exception
            raise
```

#### Context Managers

For more complex operations or when used across multiple service calls, consider using context managers to ensure proper transaction handling:

```python
from contextlib import contextmanager

@contextmanager
def transaction_context(session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
```

Usage example:

```python
def complex_operation(session, data):
    with transaction_context(session):
        # Multiple operations that need to be atomic
        character = character_service.create_character(data["character"])
        profile = profile_service.create_profile(data["profile"])
        chat_session = chat_service.create_session(character.id, profile.id)
        
        return chat_session
```

## Handling Transaction Errors

### Identifying Transient Errors

Certain database errors are transient and can be resolved by retrying the operation:

- Deadlocks (`DeadlockError`)
- Temporary connection issues
- Serialization failures in higher isolation levels

### Retry Mechanism

For operations that might encounter transient errors, implement a retry mechanism:

```python
import time
import random
from functools import wraps
from sqlalchemy.exc import DBAPIError, OperationalError

def with_retry(max_retries=3, retry_on=(DBAPIError, OperationalError)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    
                    # Exponential backoff with jitter
                    backoff = (2 ** retries) * 0.1
                    jitter = random.uniform(0, 0.1)
                    time.sleep(backoff + jitter)
                    
                    # Log retry attempt
                    print(f"Retrying operation after error: {str(e)} (attempt {retries}/{max_retries})")
        return wrapper
    return decorator
```

Usage example:

```python
class CharacterService:
    @with_retry(max_retries=3)
    def create_character(self, data):
        try:
            character = self.repo.create(data)
            self.session.commit()
            return character
        except Exception as e:
            self.session.rollback()
            raise
```

### Ensuring Idempotency

When implementing retry logic, operations should be idempotent whenever possible:

1. **Use unique constraints** to prevent duplicate records
2. **Check for existence** before creating records
3. **Use transaction savepoints** for complex operations

Example:

```python
def create_character_idempotent(self, data):
    try:
        # Check if character with this label already exists
        existing = self.repo.get_by_label(data["label"])
        if existing:
            return existing
            
        # Create new character
        character = self.repo.create(data)
        self.session.commit()
        return character
    except Exception as e:
        self.session.rollback()
        raise
```

## Transaction Isolation Levels

### Default Isolation Level

The application will primarily use the **READ COMMITTED** isolation level, which is the default for most databases including SQLite and PostgreSQL.

READ COMMITTED provides a good balance between isolation and performance for web applications:
- Each query sees only committed data at the start of the query
- Does not block reads while writes are in progress
- Allows for consistent reads within a transaction

### When to Use Higher Isolation Levels

Higher isolation levels should be used for specific operations that require stronger consistency guarantees:

1. **REPEATABLE READ**:
   - Use when a transaction reads the same data multiple times and needs consistent results
   - Appropriate for reports or calculations that should use a consistent snapshot

2. **SERIALIZABLE**:
   - The highest isolation level, ensuring complete transaction isolation
   - Use only for critical operations where data consistency is paramount
   - Be aware that this can significantly reduce concurrency

### Setting Isolation Levels

For SQLAlchemy with SQLite or PostgreSQL:

```python
# Set isolation level for a specific transaction
with session.begin():
    session.connection(execution_options={"isolation_level": "SERIALIZABLE"})
    # ... operations requiring serializable isolation ...
```

## Session Management

### Session Scope

The application will follow these guidelines for session scope:

1. **Request-scoped sessions** for API requests:
   - Create a new session at the beginning of each request
   - Close the session at the end of each request
   - Use a dependency injection pattern to provide sessions to services

2. **Explicit session handling** for background tasks or scripts:
   - Create sessions with a context manager
   - Ensure sessions are properly closed

### Session Factory Pattern

Use a session factory pattern to create SQLAlchemy sessions:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Create engine and session factory
engine = create_engine("sqlite:///./app.db")
SessionFactory = sessionmaker(bind=engine)

# For web applications with request context
ScopedSession = scoped_session(SessionFactory)

# Session context manager for explicit usage
@contextmanager
def get_session():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
```

## Testing Transactions

### Transaction Testing Strategy

1. **Use SQLite in-memory database** for testing:
   ```python
   engine = create_engine("sqlite:///:memory:")
   ```

2. **Create transaction fixture** for tests:
   ```python
   @pytest.fixture
   def db_session():
       # Create in-memory engine and tables
       engine = create_engine("sqlite:///:memory:")
       Base.metadata.create_all(engine)
       
       # Create session
       Session = sessionmaker(bind=engine)
       session = Session()
       
       yield session
       
       # Rollback and close after test
       session.rollback()
       session.close()
   ```

3. **Verify transaction behavior** in tests:
   ```python
   def test_transaction_rollback(db_session):
       repo = CharacterRepository(db_session)
       service = CharacterService(db_session)
       
       # Create a character that should succeed
       character = repo.create({"label": "test", "name": "Test Character"})
       db_session.commit()
       
       # Try an operation that should fail and rollback
       try:
           service.create_character({"label": "test", "name": "Duplicate"})  # Should fail due to unique constraint
           assert False, "Expected unique constraint violation"
       except Exception:
           pass
           
       # Verify the failed transaction was rolled back
       characters = repo.get_all()
       assert len(characters) == 1
   ```

## Best Practices

1. **Keep transactions short**:
   - Minimize the time between begin and commit/rollback
   - Avoid external API calls within transactions
   - Perform data validation before beginning the transaction when possible

2. **Handle nested transactions carefully**:
   - Be aware of SQLAlchemy's nested transaction behavior
   - Consider using savepoints for partial rollbacks

3. **Always close sessions**:
   - Use context managers or try/finally blocks to ensure sessions are closed
   - Session leaks can exhaust connection pools

4. **Be mindful of connection usage**:
   - Release connections promptly when not needed
   - Use connection pooling appropriately
   - Monitor connection usage in production

## Conclusion

This transaction management strategy provides guidance for ensuring data consistency and integrity in the Roleplay Chat Web App. By following explicit transaction boundaries, proper error handling, and appropriate isolation levels, the application will maintain reliable data operations while providing a responsive user experience.

The strategy prioritizes clarity and safety while remaining flexible enough to handle complex operations. As the application grows, these transaction management practices will help maintain database integrity and application reliability.