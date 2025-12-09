"""
Configuration Utilities

Helper functions and utilities for configuration management.
"""

import hashlib
import json
import logging
import os
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


def load_env_file(env_file: str) -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if Path(env_file).exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
                    os.environ[key.strip()] = value.strip()
    return env_vars


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested keys
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """
    Unflatten a dictionary with dot - separated keys.

    Args:
        d: Flattened dictionary
        sep: Separator used in keys

    Returns:
        Nested dictionary
    """
    result = {}

    for key, value in d.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def calculate_hash(data: Union[str, Dict[str, Any]]) -> str:
    """
    Calculate SHA256 hash of data.

    Args:
        data: Data to hash

    Returns:
        Hexadecimal hash string
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, default=str)

    return hashlib.sha256(data.encode()).hexdigest()


def generate_config_hash(config: Dict[str, Any]) -> str:
    """
    Generate hash for configuration excluding sensitive fields.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration hash
    """
    # Remove sensitive fields
    sensitive_keys = ["password", "secret", "token", "key"]
    clean_config = {}

    def remove_sensitive(obj):
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    continue
                elif isinstance(value, (dict, list)):
                    result[key] = remove_sensitive(value)
                else:
                    result[key] = value
            return result
        elif isinstance(obj, list):
            return [remove_sensitive(item) for item in obj]
        else:
            return obj

    clean_config = remove_sensitive(config)
    return calculate_hash(clean_config)


def sanitize_value(value: Any, mask_char: str = "*") -> str:
    """
    Sanitize sensitive values for logging.

    Args:
        value: Value to sanitize
        mask_char: Character to use for masking

    Returns:
        Sanitized value
    """
    if value is None:
        return "None"

    value_str = str(value)

    # Check if it looks like a sensitive value
    sensitive_indicators = [
        len(value_str) > 20,  # Long values might be secrets
        any(char in value_str for char in "!@#$%^&*()"),  # Contains special chars
        any(char.isdigit() for char in value_str)
        and any(char.isalpha() for char in value_str),
    ]

    if any(sensitive_indicators):
        if len(value_str) <= 4:
            return mask_char * len(value_str)
        else:
            return value_str[:2] + mask_char * (len(value_str) - 4) + value_str[-2:]

    return value_str


def format_config_for_display(
    config: Dict[str, Any],
    sensitive_keys: Optional[List[str]] = None,
    max_depth: int = 3,
    current_depth: int = 0,
) -> str:
    """
    Format configuration for display with sensitive value masking.

    Args:
        config: Configuration dictionary
        sensitive_keys: List of sensitive key patterns
        max_depth: Maximum depth to display
        current_depth: Current recursion depth

    Returns:
        Formatted configuration string
    """
    if current_depth >= max_depth:
        return "..."

    if sensitive_keys is None:
        sensitive_keys = ["password", "secret", "token", "key"]

    lines = []

    for key, value in config.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            lines.append(f"  {key}: ***REDACTED***")
        elif isinstance(value, dict):
            lines.append(f"  {key}:")
            nested = format_config_for_display(
                value, sensitive_keys, max_depth, current_depth + 1
            )
            for nested_line in nested.split("\n"):
                if nested_line:
                    lines.append(f"    {nested_line}")
        elif isinstance(value, list):
            lines.append(f"  {key}: [{len(value)} items]")
        else:
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def validate_config_file_format(file_path: str) -> tuple[bool, str]:
    """
    Validate configuration file format and structure.

    Args:
        file_path: Path to configuration file

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)

    if not path.exists():
        return False, f"File not found: {file_path}"

    if path.suffix not in [".yaml", ".yml", ".json"]:
        return False, f"Unsupported file format: {path.suffix}"

    try:
        if path.suffix in [".yaml", ".yml"]:
            with open(path, "r") as f:
                yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path, "r") as f:
                json.load(f)

        return True, ""
    except Exception as e:
        return False, f"Invalid file format: {e}"


def backup_configuration_file(file_path: str, backup_dir: Optional[str] = None) -> str:
    """
    Create backup of configuration file.

    Args:
        file_path: Path to configuration file
        backup_dir: Backup directory (default: same directory)

    Returns:
        Path to backup file
    """
    source_path = Path(file_path)

    if backup_dir:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
    else:
        backup_path = source_path.parent / "backups"
        backup_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
    backup_file = (
        backup_path / f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
    )

    import shutil

    shutil.copy2(source_path, backup_file)

    return str(backup_file)


def convert_config_format(
    input_file: str, output_file: str, target_format: str = "yaml"
) -> bool:
    """
    Convert configuration file between formats.

    Args:
        input_file: Input file path
        output_file: Output file path
        target_format: Target format ('yaml' or 'json')

    Returns:
        True if conversion was successful
    """
    try:
        # Load input file
        input_path = Path(input_file)
        if input_path.suffix in [".yaml", ".yml"]:
            with open(input_path, "r") as f:
                config = yaml.safe_load(f) or {}
        elif input_path.suffix == ".json":
            with open(input_path, "r") as f:
                config = json.load(f) or {}
        else:
            return False

        # Save output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            if target_format.lower() == "yaml":
                yaml.dump(config, f, default_flow_style=False, indent=2)
            elif target_format.lower() == "json":
                json.dump(config, f, indent=2)
            else:
                return False

        return True

    except Exception as e:
        logger.error(f"Config conversion failed: {e}")
        return False


def generate_secure_password(
    length: int = 16,
    include_symbols: bool = True,
    include_numbers: bool = True,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
) -> str:
    """
    Generate secure random password.

    Args:
        length: Password length
        include_symbols: Include special characters
        include_numbers: Include numbers
        include_uppercase: Include uppercase letters
        include_lowercase: Include lowercase letters

    Returns:
        Generated password
    """
    chars = ""

    if include_lowercase:
        chars += string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_numbers:
        chars += string.digits
    if include_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if not chars:
        raise ValueError("At least one character type must be included")

    password = "".join(secrets.choice(chars) for _ in range(length))

    # Ensure password contains at least one character from each included type
    requirements = []
    if include_lowercase and not any(c.islower() for c in password):
        requirements.append(secrets.choice(string.ascii_lowercase))
    if include_uppercase and not any(c.isupper() for c in password):
        requirements.append(secrets.choice(string.ascii_uppercase))
    if include_numbers and not any(c.isdigit() for c in password):
        requirements.append(secrets.choice(string.digits))
    if include_symbols and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        requirements.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

    if requirements:
        # Replace random characters with required ones
        password_list = list(password)
        for i, req_char in enumerate(requirements):
            if i < len(password_list):
                password_list[i] = req_char
        password = "".join(password_list)

    return password


def get_config_file_locations(config_dir: str = "config") -> Dict[str, List[str]]:
    """
    Get standard configuration file locations.

    Args:
        config_dir: Configuration directory

    Returns:
        Dictionary of file categories and their locations
    """
    base_path = Path(config_dir)

    return {
        "main_configs": [
            str(base_path / "base.yaml"),
            str(base_path / "base.yml"),
        ],
        "environment_configs": [
            str(base_path / "development.yaml"),
            str(base_path / "development.yml"),
            str(base_path / "testing.yaml"),
            str(base_path / "testing.yml"),
            str(base_path / "staging.yaml"),
            str(base_path / "staging.yml"),
            str(base_path / "production.yaml"),
            str(base_path / "production.yml"),
        ],
        "override_configs": [
            str(base_path / "local.yaml"),
            str(base_path / "local.yml"),
            str(base_path / "override.yaml"),
            str(base_path / "override.yml"),
        ],
        "environment_files": [
            str(base_path / ".env"),
            str(base_path / ".env.local"),
            str(base_path / ".env.production"),
            str(base_path / ".env.development"),
        ],
    }


def detect_config_environment(config_dict: Dict[str, Any]) -> str:
    """
    Detect the environment from configuration dictionary.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Detected environment name
    """
    # Check explicit environment setting
    if "system" in config_dict and "environment" in config_dict["system"]:
        return config_dict["system"]["environment"]

    # Check environment - specific indicators
    indicators = {
        "production": [
            ("system", "debug", False),
            ("security", "ssl_enabled", True),
            ("logging", "level", "WARNING"),
        ],
        "development": [
            ("system", "debug", True),
            ("database", "echo", True),
            ("logging", "level", "DEBUG"),
        ],
        "testing": [
            ("database", "name", lambda x: "test" in str(x).lower()),
        ],
    }

    scores = {env: 0 for env in indicators}

    for env, checks in indicators.items():
        for check in checks:
            key_path = check[0]
            key_name = check[1]
            expected_value = check[2]

            current = config_dict
            for key in key_path.split("."):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    break
            else:
                # Full path exists
                if callable(expected_value):
                    if expected_value(current):
                        scores[env] += 1
                elif current == expected_value:
                    scores[env] += 1

    # Return environment with highest score
    if scores and max(scores.values()) > 0:
        return max(scores, key=scores.get)

    return "unknown"
