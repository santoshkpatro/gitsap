# Django Setup Guide

This guide walks you through setting up a Django project with proper dependency management and environment configuration.

## Prerequisites

- Python 3.8+
- UV package manager installed

## Project Setup

### 1. Create Project Directory

```bash
mkdir my-django-project
cd my-django-project
```

### 2. Initialize UV Project

```bash
uv init
```

### 3. Install Django

```bash
uv add django
```

### 4. Create Django Project

```bash
uv run django-admin startproject myproject .
```

## Environment Configuration

### 1. Create Environment Files

Create a `.env.dev` file for development settings:

```bash
# .env.dev
DEBUG=True
SECRET_KEY=your-development-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Copy Environment File

Copy the development environment file to create your main environment file:

```bash
cp .env.dev .env
```

### 3. Install Python-dotenv

```bash
uv add python-dotenv
```

### 4. Configure Django Settings

Update your `settings.py` to use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database configuration
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'))
}
```

## Dependency Management

### 1. Add Development Dependencies

```bash
uv add --group dev black flake8 pytest pytest-django
```

### 2. Compile Requirements Files

Generate requirements files from your pyproject.toml:

```bash
# Generate production requirements
uv pip compile pyproject.toml -o requirements.txt

# Generate development requirements (includes dev group)
uv pip compile pyproject.toml -o requirements-dev.txt --group dev
```

### 3. Example pyproject.toml Structure

Your `pyproject.toml` should look similar to this:

```toml
[project]
name = "my-django-project"
version = "0.1.0"
description = ""
readme = "README.md"
dependencies = [
    "django>=4.2",
    "python-dotenv>=1.0.0",
    "dj-database-url>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pytest>=7.0.0",
    "pytest-django>=4.5.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Database Setup

### 1. Run Migrations

```bash
uv run python manage.py migrate
```

### 2. Create Superuser

```bash
uv run python manage.py createsuperuser
```

## Running the Development Server

```bash
uv run python manage.py runserver
```

Your Django application will be available at `http://127.0.0.1:8000/`

## Project Structure

After setup, your project structure should look like this:

```
my-django-project/
├── .env
├── .env.dev
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── db.sqlite3
```

## Additional Commands

### Update Requirements

When you add new dependencies, regenerate the requirements files:

```bash
uv pip compile pyproject.toml -o requirements.txt
uv pip compile pyproject.toml -o requirements-dev.txt --group dev
```

### Install from Requirements

To install dependencies from requirements files:

```bash
# Production dependencies
uv pip install -r requirements.txt

# Development dependencies
uv pip install -r requirements-dev.txt
```

## Git Setup

Don't forget to add a `.gitignore` file:

```gitignore
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Django
*.log
db.sqlite3
db.sqlite3-journal
media/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Next Steps

1. Create your first Django app: `uv run python manage.py startapp myapp`
2. Configure your database settings for production
3. Set up static files handling
4. Configure your web server (nginx, Apache, etc.)
5. Set up CI/CD pipeline

---

**Note**: Remember to keep your `.env` file secure and never commit it to version control. Always use `.env.dev` as a template for other developers.
