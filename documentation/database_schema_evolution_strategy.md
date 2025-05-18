# Database Schema Evolution Strategy

This document outlines the strategy for managing database schema changes in the Roleplay Chat Web App. Following these guidelines ensures that schema changes are applied safely and consistently, minimizing risks to data integrity and application functionality.

## Core Principles

1. **Safety First**: Prioritize data integrity and minimize disruption
2. **Backward Compatibility**: Prefer non-breaking changes when possible
3. **Proper Planning**: Plan schema changes thoroughly before implementation
4. **Automated Migrations**: Use Alembic for schema version control
5. **Testing**: Test all schema changes and migrations thoroughly

## Migration Tool: Alembic

[Alembic](https://alembic.sqlalchemy.org) is the chosen tool for managing schema migrations with SQLAlchemy.

### Basic Configuration

```python
# In alembic.ini
sqlalchemy.url = sqlite:///./app.db  # Points to development database

# In env.py
from your_application.models.base import Base
target_metadata = Base.metadata  # Reference to SQLAlchemy models
```

### Migration Workflow

1. **Generate Migration Script**:
   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```
   
2. **Review and Edit**: Always review auto-generated scripts before applying them.
   - Alembic may not detect all changes (e.g., data type changes)
   - Ensure migrations are correct and include necessary data migrations
   
3. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```
   
4. **Version Control**: Commit migration scripts to your version control system

## Handling Schema Changes

### Types of Schema Changes

1. **Non-Breaking Changes**:
   - Adding a new nullable column
   - Adding a new table
   - Creating a new index
   - Adding a new constraint that existing data satisfies

2. **Breaking Changes**:
   - Renaming a column
   - Changing a column's data type
   - Making a nullable column non-nullable
   - Removing a column or table
   - Adding a constraint that existing data might violate

### Strategy for Non-Breaking Changes

Non-breaking changes can be applied directly using Alembic:

```python
# Example Alembic migration for adding a nullable column
def upgrade():
    op.add_column('user_profile', sa.Column('last_login', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('user_profile', 'last_login')
```

### Strategy for Breaking Changes: Two-Step Approach

Breaking changes require a more careful approach using a multi-step deployment:

#### Step 1: Expand (Add but don't remove)

1. Add new structures without removing old ones
2. Deploy code that can work with both old and new structures
3. Application writes to both old and new or reads from old and migrates data

Example:
```python
# Rename 'username' to 'user_name' - Step 1
def upgrade():
    # Add new column
    op.add_column('user_profile', sa.Column('user_name', sa.String(), nullable=True))
    
    # Copy data from old to new column
    op.execute("UPDATE user_profile SET user_name = username")

def downgrade():
    op.drop_column('user_profile', 'user_name')
```

#### Step 2: Migrate Data

Ensure all data is properly migrated from old to new structures. This can be:

1. **Within Alembic**: For small, fast data transformations
   ```python
   op.execute("UPDATE user_profile SET user_name = username WHERE user_name IS NULL")
   ```

2. **Separate Script**: For complex or large-volume migrations
   ```python
   # Example of a separate data migration script
   from sqlalchemy.orm import Session
   from your_application.models import UserProfile
   
   def migrate_usernames(session):
       profiles = session.query(UserProfile).filter(
           UserProfile.user_name.is_(None),
           UserProfile.username.isnot(None)
       ).all()
       
       for profile in profiles:
           profile.user_name = profile.username
       
       session.commit()
   ```

#### Step 3: Contract (Remove old structures)

Once all data is migrated and the application no longer relies on old structures:

```python
# Rename 'username' to 'user_name' - Step 3
def upgrade():
    # Make new column non-nullable if needed
    op.alter_column('user_profile', 'user_name', nullable=False)
    
    # Remove old column
    op.drop_column('user_profile', 'username')

def downgrade():
    op.add_column('user_profile', sa.Column('username', sa.String(), nullable=True))
    op.execute("UPDATE user_profile SET username = user_name")
    op.alter_column('user_profile', 'username', nullable=False)
```

## Data Migration Approaches

### 1. In-Migration Data Changes

Suitable for:
- Simple transformations
- Small data volumes
- Atomicity with schema changes

```python
def upgrade():
    # Add a new column
    op.add_column('character', sa.Column('display_name', sa.String(), nullable=True))
    
    # Populate the new column with data derived from existing columns
    op.execute("UPDATE character SET display_name = name WHERE display_name IS NULL")
```

### 2. Separate Migration Scripts

Suitable for:
- Complex transformations requiring application logic
- Large data volumes that could timeout during migration
- Migrations that need to be run or monitored separately

```python
# separate_migration.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from your_application.models import Character

def migrate_character_names():
    engine = create_engine('sqlite:///./app.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        characters = session.query(Character).filter(Character.display_name.is_(None)).all()
        
        for character in characters:
            character.display_name = character.name.title()  # Apply more complex logic
        
        session.commit()
        print(f"Migrated {len(characters)} character names")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {str(e)}")
    finally:
        session.close()
```

## Best Practices

1. **Always Back Up Data Before Migrations**:
   ```bash
   sqlite3 app.db .dump > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Make Migrations Idempotent**:
   - Design migrations to be safely re-runnable
   - Use checks like `WHERE new_column IS NULL` when updating data

3. **Test Migrations Thoroughly**:
   - Test on a copy of production data when possible
   - Verify both upgrade and downgrade paths

4. **Document Complex Migrations**:
   - Add detailed comments in migration scripts
   - Document any manual steps required

5. **Consider Performance Impact**:
   - For large tables, consider batching updates
   - Be aware of locking behavior in SQLite
   - Run potentially slow migrations during low-usage periods

## Versioning and Deployment Strategy

1. **Version Database Changes with Application Code**:
   - Migration scripts should be committed alongside application code changes
   - Keep migrations in sync with application versions

2. **Migration as Part of Deployment**:
   - Run migrations automatically as part of deployment process
   - Verify migrations complete successfully before deploying new application code

3. **Rollback Plan**:
   - Always have a tested rollback plan for each migration
   - For critical changes, script the rollback process

## Conclusion

This schema evolution strategy provides a structured approach to managing database changes throughout the Roleplay Chat Web App's lifecycle. By following these guidelines, we ensure that database changes are applied safely, consistently, and with minimal risk to data integrity or application functionality.

The strategy is flexible enough to accommodate both simple additions and complex structural changes, while maintaining backward compatibility during transition periods. This approach is especially valuable as the application grows and evolves over time.