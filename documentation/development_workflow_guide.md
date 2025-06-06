# Development Workflow Guide

This document outlines the development workflow for the Roleplay Chat Web App. It provides guidelines for git usage, commit conventions, code review, and version numbering to maintain high-quality code and a consistent development process.

## Core Principles

1. **Code Quality**: Maintain high standards for code quality
2. **Traceability**: Ensure changes are traceable and documented
3. **Reproducibility**: Make builds reproducible across environments
4. **Consistency**: Follow consistent patterns and conventions
5. **Self-Review**: Practice thorough self-review before finalizing changes

## Git Branching Strategy

The project will follow a simplified Feature Branch Workflow optimized for solo development:

### Main Branch

The `main` branch represents the stable, working state of the application. It should always contain production-ready code.

### Feature Branches

For new features, bug fixes, or any code changes:

1. Create a new branch from `main` with a descriptive name:
   ```bash
   # For new features
   git checkout -b feature/add-user-profiles

   # For bug fixes
   git checkout -b fix/message-ordering-bug

   # For refactoring
   git checkout -b refactor/restructure-services

   # For documentation
   git checkout -b docs/add-api-docs
   ```

2. Make regular, incremental commits to your feature branch
3. When the feature is complete and tested, merge it back to `main`

### Branch Naming Conventions

Follow these prefixes for branch names:
- `feature/` - For new features
- `fix/` - For bug fixes
- `refactor/` - For code refactoring without changing functionality
- `docs/` - For documentation changes
- `test/` - For adding or modifying tests
- `chore/` - For maintenance tasks, dependency updates, etc.

After the prefix, use kebab-case to describe the branch purpose:
```
feature/add-character-search
fix/incorrect-message-ordering
refactor/simplify-repository-pattern
```

## Commit Conventions

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that don't affect code functionality (formatting, etc.)
- `refactor`: Code refactoring without functionality changes
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks, dependency updates, etc.
- `perf`: Performance improvements

### Scope

Optional field specifying the part of the codebase affected:
- `models`
- `api`
- `services`
- `repositories`
- `ui`
- `db`
- etc.

### Examples

```
feat(characters): add character search functionality
fix(chat): correct message ordering in chat history
docs(api): add documentation for user profile endpoints
style: format code with black
refactor(services): simplify message service methods
test(repositories): add tests for character repository
chore(deps): update SQLAlchemy to 2.0
perf(queries): optimize character lookup query
```

### Commit Best Practices

1. **Atomic Commits**: Each commit should represent a single logical change
2. **Complete Commits**: Ensure each commit leaves the codebase in a working state
3. **Clear Messages**: Write clear, descriptive commit messages
4. **Reference Issues**: Reference issue numbers in commit messages when applicable
5. **Separate Concerns**: Keep unrelated changes in separate commits

## Code Self-Review Process

As a solo developer, implement a disciplined self-review process before merging changes:

### Pre-Merge Checklist

1. **Review Changes**:
   ```bash
   # Review all changes between main and your feature branch
   git diff main...your-feature-branch
   ```

2. **Run Automated Checks**:
   ```bash
   # Run tests
   pytest

   # Run linters
   flake8

   # Run type checking
   mypy

   # Run code formatters
   black .
   isort .
   ```

3. **Manual Testing**:
   - Test the feature or fix manually
   - Verify edge cases and error scenarios
   - Check both positive and negative test cases

4. **Documentation Review**:
   - Ensure code is properly documented
   - Update user documentation if needed
   - Add/update API documentation for changes

### Merging to Main

After completing self-review and ensuring all checks pass:

```bash
# Checkout main branch
git checkout main

# Merge feature branch with --no-ff to preserve branch history
git merge --no-ff your-feature-branch

# Delete the feature branch after successful merge
git branch -d your-feature-branch
```

The `--no-ff` (no fast-forward) flag creates a merge commit even when a fast-forward would be possible, making the history clearer by showing where feature branches were integrated.

## Version Numbering

The project will follow [Semantic Versioning](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH
```

Where:
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible new functionality
- **PATCH**: Backwards-compatible bug fixes

### Version Tagging

Use Git tags to mark versions:

```bash
# Tag a new version
git tag -a v0.1.0 -m "Initial release with basic chat functionality"

# Push tags to remote (if using a remote repository)
git push --tags
```

### Version Increments

- Increment **PATCH** (0.1.0 → 0.1.1) for bug fixes and minor changes
- Increment **MINOR** (0.1.1 → 0.2.0) for new features
- Increment **MAJOR** (0.2.0 → 1.0.0) for breaking changes

### Pre-release Versions

For pre-release versions, use the following format:

```
MAJOR.MINOR.PATCH-alpha.N
MAJOR.MINOR.PATCH-beta.N
MAJOR.MINOR.PATCH-rc.N
```

Example:
```bash
git tag -a v0.2.0-alpha.1 -m "Alpha release of user profiles feature"
```

## Code Quality Enforcement

### Pre-commit Hooks

Set up pre-commit hooks to enforce code quality standards:

1. **Install pre-commit**:
   ```bash
   pip install pre-commit
   ```

2. **Create a .pre-commit-config.yaml file**:
   ```yaml
   repos:
   - repo: https://github.com/pre-commit/pre-commit-hooks
     rev: v4.4.0
     hooks:
     - id: trailing-whitespace
     - id: end-of-file-fixer
     - id: check-yaml
     - id: check-added-large-files

   - repo: https://github.com/pycqa/flake8
     rev: 6.0.0
     hooks:
     - id: flake8
       additional_dependencies:
       - flake8-bugbear
       - flake8-comprehensions
       - flake8-pytest-style
       - flake8-docstrings
       - flake8-import-order

   - repo: https://github.com/pycqa/isort
     rev: 5.12.0
     hooks:
     - id: isort

   - repo: https://github.com/psf/black
     rev: 23.3.0
     hooks:
     - id: black

   - repo: https://github.com/pre-commit/mirrors-mypy
     rev: v1.3.0
     hooks:
     - id: mypy
       additional_dependencies:
       - types-requests
   ```

3. **Install hooks**:
   ```bash
   pre-commit install
   ```

The pre-commit hooks will run automatically on `git commit`, preventing commits that don't meet the quality standards.

### Manual Quality Checks

In addition to automated checks, perform these manual checks before merging:

1. **Code Readability**: Is the code clear and easy to understand?
2. **Error Handling**: Are errors properly handled and logged?
3. **Security**: Are there any security concerns with the changes?
4. **Performance**: Could the changes impact performance negatively?
5. **Maintainability**: Will the code be easy to maintain in the future?

## Development Environment Setup

Maintain a consistent development environment:

```bash
# Clone the repository
git clone <repository-url>
cd roleplay-chat

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies with Poetry
poetry install

# Set up pre-commit hooks
pre-commit install

# Create initial database
flask db upgrade

# Run the application
flask run
```

## Documentation Workflow

Documentation should be treated with the same care as code:

1. **Update Documentation with Code Changes**:
   - Update API documentation when endpoints change
   - Update model documentation when data structures change
   - Update the README for significant changes

2. **Documentation Types**:
   - **Code Documentation**: Docstrings and comments within code
   - **API Documentation**: Endpoint specifications, request/response formats
   - **User Documentation**: How to use the application
   - **Developer Documentation**: How to develop and maintain the application

3. **Documentation Format**:
   - Use Markdown for all documentation
   - Follow a consistent style within documents
   - Include examples where appropriate

## Release Process

Even for a local application, following a structured release process helps maintain quality:

1. **Prepare Release**:
   - Review and update version number in code
   - Update CHANGELOG.md with notable changes
   - Run full test suite and fix any issues
   - Update documentation

2. **Create Release**:
   - Tag the release in Git
   - Build distribution package (if applicable)
   - Create release notes

3. **Post-Release**:
   - Plan next development cycle
   - Create issues for known bugs or planned features

## Best Practices

1. **Commit Frequently**: Make small, focused commits rather than large, sweeping changes
2. **Test Before Committing**: Run tests before committing changes
3. **Keep the Main Branch Stable**: Never commit directly to main for significant changes
4. **Document As You Go**: Update documentation alongside code changes
5. **Regular Self-Review**: Cultivate a habit of reviewing your own code critically

## Handling Hotfixes

For urgent fixes to production code:

1. Create a `hotfix/` branch from `main`:
   ```bash
   git checkout -b hotfix/critical-security-issue main
   ```

2. Make the minimal necessary changes to fix the issue

3. Test thoroughly

4. Merge back to `main` with proper version increment:
   ```bash
   git checkout main
   git merge --no-ff hotfix/critical-security-issue
   git tag -a v1.0.1 -m "Fix critical security issue"
   ```

## Conclusion

This development workflow guide provides a structured approach to developing and maintaining the Roleplay Chat Web App. By following these guidelines, you can ensure consistent code quality, clear version history, and a maintainable codebase.

Even as a solo developer, implementing these professional practices will help keep the project organized and make it easier to onboard others if the team expands in the future. The workflow is designed to be lightweight yet effective, balancing formality with practicality for a solo developer.
