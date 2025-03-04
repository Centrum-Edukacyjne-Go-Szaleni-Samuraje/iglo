# IGLO Project Guide

## Build Commands
- Run server: `poetry run python iglo/manage.py runserver`
- Run tests: `poetry run pytest iglo/`
- Run single test: `poetry run pytest iglo/path/to/test.py::test_name`
- Run with coverage: `poetry run pytest --cov=iglo`
- Run migrations: `poetry run python iglo/manage.py migrate`
- Format code: `poetry run black .`
- Update translations: `poetry run python iglo/manage.py makemessages --all` 

## Style Guidelines
- Use Black for formatting with 120 character line length
- Follow Django naming conventions (snake_case for functions/variables, PascalCase for classes)
- Group imports: standard lib, third-party, local with a blank line between groups
- Type hints: Use Optional[] for nullable fields and add return type annotations
- DocStrings: Add for complex functions and classes using """triple quotes"""
- Error handling: Use appropriate Django exceptions (ValidationError, etc.)
- Prefer explicit over implicit (no wildcard imports)
- Model fields should use verbose_name for translations using gettext_lazy
- IMPORTANT: Never add trailing whitespace to any lines, including empty lines
- When writing multiline strings or code blocks, ensure no trailing spaces

## Git and Commit Guidelines
- Don't mention "Claude" or include Claude co-authorship in commit messages
- Write concise but descriptive commit messages
- First line should be a summary under 50 characters
- Follow with blank line and more detailed explanation if needed
- Use present tense ("Add feature" rather than "Added feature")

## Environment Setup
- Python 3.10+
- PostgreSQL database (via Docker)
- Set CELERY_TASK_ALWAYS_EAGER=True for local development