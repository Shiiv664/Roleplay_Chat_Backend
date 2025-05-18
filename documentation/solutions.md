# Phase 3 Advanced Backend Strategies

This document details strategies for critical backend development aspects, building upon the foundational tooling outlined in "Phase 3 Tooling Specifications." It's tailored for a developer aiming for a clean start, even if currently working solo.

## 1. Database Schema Evolution Strategy

Managing database schema changes effectively is crucial for long-term maintainability. Alembic is the chosen tool for schema migrations.

* **Handling Breaking Changes:**
    * **Prioritize Backward-Compatible Changes:** Whenever possible, opt for schema modifications that won't disrupt existing application functionality or data structures (e.g., adding new nullable columns, new tables).
    * **Two-Step (or Multi-Step) Deployment:** For unavoidable breaking changes (e.g., renaming a column, changing a column type with data loss potential, removing a column), follow this safe methodology:
        1.  **Expand:** Deploy code that can work with both the old and new schema. Add new columns/tables, but keep old ones. Application logic writes to both or reads from old and migrates to new on read/write.
        2.  **Migrate Data:** Run data migration scripts (see below) to move/transform data to the new schema.
        3.  **Contract:** Deploy code that only uses the new schema. Remove old columns/tables in a subsequent schema migration.
    * **Versioned APIs & Feature Flags:**
        * If schema changes significantly impact API contracts, consider versioning your API (e.g., `/v1/endpoint`, `/v2/endpoint`).
        * Feature flags can help enable/disable code paths that depend on new schema elements, allowing for gradual rollout and rollback.
        * **Note for Solo Developers:** While powerful, these might be overkill for an initial solo project unless you specifically foresee near-term needs (e.g., a public API or very complex features). Focus on the two-step deployment methodology for safety first; these can be integrated later as complexity grows.

* **Policy for Data Migration During Schema Changes:**
    * **Timing:** Data migrations can occur:
        * **Pre-Deployment (within migration script):** For small, fast data transformations that can be done atomically with the schema change via Alembic's `op.execute()`.
        * **Post-Deployment (separate scripts/tasks):** For large or complex data migrations that might take significant time. These are run after the schema change is applied.
        * **Online/Live Migration:** Application logic handles data transformation as data is accessed or modified.
    * **Idempotency:** Data migration scripts should be idempotent (safe to run multiple times).
    * **Testing:** Thoroughly test data migrations in a staging-like environment with a realistic data copy.
    * **Backup:** Always back up the database before applying schema or significant data migrations.

* **Alembic for Data Migrations vs. Separate Scripts:**
    * **Alembic for Data Migrations:** Alembic's `op.bulk_insert()` and `op.execute('UPDATE ...')` can be used directly within migration scripts for simpler data transformations, especially those tightly coupled with schema changes (e.g., populating a new column based on an existing one). This keeps schema and related data changes together.
    * **Separate Scripts:** For complex, long-running data migrations, or migrations requiring application logic not easily expressed in SQL, use separate Python scripts. These scripts would use SQLAlchemy ORM for data manipulation. They can be triggered manually or as part of a deployment pipeline after the Alembic schema migration has run.
    * **Recommendation:** Use Alembic for schema changes and simple, coupled data changes. Use separate, well-tested Python scripts (using SQLAlchemy Core or ORM) for complex or large-volume data migrations.

## 2. Transaction Management Approach

Ensuring data consistency and integrity through proper transaction management is vital.

* **Explicit vs. Implicit Transaction Boundaries:**
    * **Explicit Boundaries Preferred:** Use explicit `session.commit()` and `session.rollback()` within the service layer or at the highest appropriate level (e.g., per API request). This provides clear control over the unit of work.
    * **SQLAlchemy Session:** The SQLAlchemy session object itself manages the transaction. Typically, a session's lifecycle is tied to a request.
    * **Context Managers:** Use `try/except/finally` blocks or context managers to ensure sessions are closed and transactions are handled (committed or rolled back).
        ```python
        # Example in a service method
        from sqlalchemy.orm import Session
        
        def my_service_operation(db: Session, data: dict): # Assuming MyModel is defined
            try:
                # ... operations using db session ...
                # Example: new_object = MyModel(**data)
                # db.add(new_object)
                db.commit()
                # db.refresh(new_object) # To get DB-generated values like ID
                # return new_object
            except Exception as e:
                db.rollback()
                raise e # Re-raise or handle as appropriate
            # Ensure MyModel is defined or remove placeholder lines for actual use
        ```

* **Handling Transaction Retries for Certain Error Conditions:**
    * **Identify Transient Errors:** Retry transactions primarily for transient errors like deadlocks (`DeadlockError`) or temporary network issues.
    * **Retry Mechanism:** Implement a retry mechanism with an exponential backoff and jitter strategy to avoid overwhelming the database.
    * **Idempotency:** Ensure operations within the transaction are idempotent if retries are implemented, or that the retry logic can handle non-idempotent operations safely.
    * **Limit Retries:** Set a maximum number of retries.
    * **Decorator Approach:** A decorator can be a clean way to add retry logic to service methods.

* **Transaction Isolation Levels for Different Operations:**
    * **Default (READ COMMITTED):** Most databases default to `READ COMMITTED`. This is generally a good balance for web applications. For many operations, this is sufficient.
    * **REPEATABLE READ:** Use if a transaction requires reading the same data multiple times and needs to ensure that data doesn't change between reads by other concurrent transactions.
    * **SERIALIZABLE:** The highest isolation level. Use for critical operations where data consistency is paramount. Be aware that this can reduce concurrency.
    * **Configuration:** Isolation levels can often be set per-session or per-transaction using SQLAlchemy's `session.connection(execution_options={"isolation_level": "SERIALIZABLE"})`.

## 3. API Authentication/Authorization

No authentification is needed.

## 4. Backend Performance Considerations

Proactive performance planning ensures a responsive application.

* **Database Indexing Strategy:**
    * Index foreign keys and columns frequently used in `WHERE`, `JOIN`, `ORDER BY`, `GROUP BY` clauses.
    * Use composite indexes for multi-column filters.
    * Analyze query plans (`EXPLAIN`) to optimize.
    * Avoid over-indexing; review indexes periodically.

* **Query Optimization Guidelines:**
    * Select only necessary columns (avoid `SELECT *`).
    * Ensure joins use indexed columns.
    * Minimize N+1 problems with SQLAlchemy's eager loading (`joinedload`, `selectinload`).
    * Filter early; perform operations database-side where possible.
    * Use `exists()` for existence checks.

* **Caching Approach (Iterative Implementation):**
    * **Initial Phase (No Caching or Minimal In-Memory):**
        * For initial development, especially as a solo developer on a local application, explicit caching layers might not be necessary. Focus on well-structured data access and efficient queries first.
        * If specific, very frequently accessed and rarely changing data points are identified early (e.g., global application settings), consider simple in-memory caching like Python's `functools.lru_cache` for those specific functions. Ensure clear invalidation if this data can change.
    * **Designing for Cacheability:** As you build services and data access logic, structure code in a way that caching could be introduced later without major refactoring (e.g., dedicated service methods for fetching data that could be wrapped with caching logic).
    * **Future Consideration (If Performance Dictates):**
        * **Application-Level Caching (In-Memory):** If performance bottlenecks arise that can be solved with in-process caching, expand the use of tools like `cachetools` or `functools.lru_cache`. This would be the first step for more comprehensive caching.
        * **External Cache (e.g., Redis):** If the application scales, requires a shared cache between multiple processes/servers, or needs advanced caching features, an external cache like Redis can be integrated. This would be a more significant step, taken when clear benefits are identified.
    * **HTTP Caching:** Regardless of application-level caching, always consider using HTTP headers (e.g., `ETag`, `Cache-Control`) to allow clients and proxies to cache API responses appropriately. This is a separate concern from server-side application caching.

## 5. Deployment & Configuration Strategy

A clear strategy simplifies operations, even for a local project that might be deployed later.

* **Configuration Management:**
    * **Environment Variables:** Prioritize for settings that vary between environments (e.g., database URLs, API keys, debug flags) or for sensitive data.
        * **How they work:** Environment variables are key-value pairs set outside the application code, in the operating system's environment.
        * **Accessing in Python:** Use `os.getenv("MY_VARIABLE_NAME")` or `os.environ.get("MY_VARIABLE_NAME")`. `os.getenv()` is often preferred as it returns `None` if the variable isn't set, rather than raising a `KeyError`.
    * **Configuration Files:** Use for base settings, default values, or complex, non-sensitive configurations (e.g., a `config.py` or `settings.yaml`). These files can be version-controlled.
    * **Precedence:** Design your application so that environment variables always override values from configuration files.

* **Secret Management Approach (Handling API Keys and Sensitive Data):**
    * **Core Principle:** Never hardcode secrets directly into your source code or commit them to version control.
    * **Local Development:**
        * **`.env` Files:** Create a file named `.env` in your project's root directory. Store secrets here as `KEY="VALUE"` pairs.
            ```
            # Example .env content:
            API_SECRET_KEY="your_actual_secret_key_here"
            DATABASE_URL="your_local_database_connection_string"
            ```
        * **`.gitignore`:** **Crucially, add `.env` to your `.gitignore` file** to prevent it from ever being committed.
        * **Loading `.env`:** Use a library like `python-dotenv`. Call `load_dotenv()` early in your application's startup to load these variables into the environment.
            ```python
            from dotenv import load_dotenv
            import os
            load_dotenv() # Loads variables from .env
            
            my_api_key = os.getenv("API_SECRET_KEY")
            ```
        * **`env.example` File:** Provide an `env.example` file (committed to Git) that lists the required environment variables without their actual values, serving as a template.
    * **Staging/Production (Future):**
        * When deploying, secrets will be set directly as environment variables through the hosting platform's interface or via dedicated secret management tools (e.g., HashiCorp Vault, AWS Secrets Manager). The application code (`os.getenv()`) remains the same.

## 6. Development Workflow (Adapted for Local Solo Development)

A standardized workflow improves code quality and maintainability, even when working alone. This workflow uses Git locally and does not require platforms like GitHub.

* **Git Branching Strategy and Commit Conventions:**
    * **Branching Strategy:** **Feature Branch Workflow** is recommended for its simplicity:
        * Your local `main` branch should always represent a stable, working state.
        * For any new feature or bug fix, create a new branch off `main` (e.g., `git checkout -b feature/new-user-endpoint` or `git checkout -b fix/login-bug`).
    * **Commit Conventions:** Use **Conventional Commits** (e.g., `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`). This creates a clear and descriptive Git history.

* **"Pull Request" (Self-Review) and Merging Process:**
    * **No Platform PRs:** Since you're local, you won't use a platform's Pull Request interface. The "PR" becomes a conceptual step of self-review and quality assurance.
    * **Feature Branch Development:** Do all your work on the feature branch. Commit regularly.
    * **Pre-Merge Checklist (Self-Review):** Before merging a feature branch back into `main`, perform a self-review:
        1.  **Review Changes:** Look over all the changes made on the branch. Use `git diff main...your-feature-branch` to see a summary of differences.
        2.  **Run Local Checks:**
            * Execute all automated tests (e.g., `pytest`).
            * Run linters (e.g., `flake8`) and type checkers (e.g., `mypy`).
            * Ensure code formatters (e.g., `black`, `isort`) have been applied.
            * (Pre-commit hooks can automate many of these checks before each commit on your feature branch).
        3.  **Verify Functionality:** Manually test the new feature or bug fix to ensure it works as expected.
    * **Merging:** Once satisfied, merge the feature branch into `main`:
        ```bash
        git checkout main
        # Optional: git pull (if you ever sync main with a remote, not relevant for purely local)
        git merge --no-ff your-feature-branch # --no-ff preserves branch history as a distinct merge
        git branch -d your-feature-branch     # Delete the feature branch after successful merge
        ```
        Using `--no-ff` (no fast-forward) for merges creates a merge commit, which can make the history clearer by showing where feature branches were integrated.

* **Version Numbering Scheme:**
    * **Semantic Versioning (SemVer):** `MAJOR.MINOR.PATCH`. Use Git tags to mark releases/versions locally (e.g., `git tag v0.1.0`).

## 7. Dependencies Management

Properly managing dependencies is key to a stable and secure application.

* **Tool for Dependency Management:**
    * **Poetry** will be used for managing project dependencies, packaging, and virtual environments. It utilizes `pyproject.toml` for project metadata and dependencies, and `poetry.lock` for ensuring deterministic builds by locking dependency versions.
    * **Virtual Environments:** Always use virtual environments. Poetry creates and manages these automatically for the project.

* **Policy for Dependency Updates and Security Patches:**
    * Regularly review and update dependencies using Poetry's update commands (e.g., `poetry update`).
    * Later on: Use tools like `dependabot` (if the project is ever hosted on platforms like GitHub/GitLab), `pip-audit` (which can work with Poetry projects), or `safety` to scan for known vulnerabilities in dependencies.
    * Update patch versions frequently.
    * Update minor versions with caution and thorough testing, as they may introduce new features or, rarely, minor breaking changes.
    * Plan for major version updates carefully, as they often include breaking changes. Always consult changelogs.

* **Approach to Handling Dependency Conflicts:**
    * **Lock Files:** The `poetry.lock` file is critical as it records the exact versions of all dependencies and sub-dependencies, preventing "works on my machine" issues and ensuring consistent environments.
    * **Resolution Tools:** Poetry has a robust dependency resolver that attempts to find a compatible set of versions for all declared dependencies.
    * **Manual Intervention:** If conflicts arise that Poetry cannot resolve automatically:
        * Examine Poetry's output for details on the conflicting packages and their version constraints.
        * Consult the documentation for the conflicting packages to understand compatibility.
        * You may need to explicitly set version constraints for certain packages in your `pyproject.toml` to guide the resolver (e.g., `package_a = ">=1.0,<2.0"`).
        * In some cases, you might need to find an alternative package or wait for updates if a direct resolution isn't possible.
