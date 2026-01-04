"""
Environment Variable Loader

Loads .env file from project root directory.
Should be imported at the very beginning of the application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_env():
    """
    Load .env file from project root directory.

    Project structure:
        Nexus/
        ├── .env              # Environment variables file
        ├── backend/
        │   ├── config/
        │   │   └── env_loader.py  # This file
        │   └── service/
        │       └── api.py
        └── ...
    """
    # Get the directory where this file is located: backend/config/
    current_file = Path(__file__).resolve()

    # Go up to backend/config/ -> backend/ -> Nexus/ (project root)
    project_root = current_file.parent.parent.parent

    # Path to .env file
    env_path = project_root / '.env'

    # Load .env file
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✓ Loaded environment variables from: {env_path}")
        return True
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        print(f"⚠️  Create a .env file in the project root directory")
        return False


def get_env(key: str, default: str = None) -> str:
    """
    Get environment variable with optional default value.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def require_env(key: str) -> str:
    """
    Get required environment variable.
    Raises error if not found.

    Args:
        key: Environment variable name

    Returns:
        Environment variable value

    Raises:
        EnvironmentError: If environment variable not found
    """
    value = os.getenv(key)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' not found. "
            f"Please set it in the .env file."
        )
    return value


# Auto-load on import
load_env()
