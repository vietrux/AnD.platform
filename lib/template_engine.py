# template_engine module
"""Template engine for loading and processing Go implant templates.

This module handles loading Go templates from the templates/ directory,
substituting placeholder variables, generating random identifiers for
obfuscation, and validating templates for missing variables.
"""

import re
import secrets
import string
from pathlib import Path


# Default templates directory relative to project root
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Regex pattern to match {{VARIABLE_NAME}} placeholders
TEMPLATE_VAR_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# Standard template variables that should be present in templates
STANDARD_VARIABLES = frozenset({
    "C2_URL",
    "ENCRYPTION_KEY",
    "MAIN_FUNC",
    "CONNECT_FUNC",
    "EXECUTE_FUNC",
})

# Optional block variables (may be empty)
OPTIONAL_VARIABLES = frozenset({
    "EVASION_IMPORTS",
    "EVASION_FUNCTIONS",
    "PERSISTENCE_FUNCTIONS",
    "FORENSICS_FUNCTIONS",
})


class TemplateError(Exception):
    """Base exception for template engine errors."""

    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template file cannot be found."""

    pass


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""

    pass


def load_template(template_name: str, templates_dir: Path | None = None) -> str:
    """Load a Go template file from the templates directory.

    Args:
        template_name: Name of the template file (with or without .go extension).
        templates_dir: Optional custom templates directory path.

    Returns:
        The raw template content as a string.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateError: If the template cannot be read.
    """
    if templates_dir is None:
        templates_dir = TEMPLATES_DIR

    # Ensure .go extension
    if not template_name.endswith(".go"):
        template_name = f"{template_name}.go"

    template_path = templates_dir / template_name

    if not template_path.exists():
        raise TemplateNotFoundError(
            f"Template not found: {template_path}"
        )

    try:
        return template_path.read_text(encoding="utf-8")
    except OSError as e:
        raise TemplateError(f"Failed to read template {template_path}: {e}") from e


def substitute_variables(template: str, variables: dict[str, str]) -> str:
    """Substitute placeholder variables in a template.

    Replaces all occurrences of {{VARIABLE_NAME}} with the corresponding
    value from the variables dictionary.

    Args:
        template: The template string containing {{VAR}} placeholders.
        variables: Dictionary mapping variable names to replacement values.

    Returns:
        The template with all known variables substituted.

    Example:
        >>> substitute_variables("const URL = \"{{C2_URL}}\"", {"C2_URL": "https://example.com"})
        'const URL = "https://example.com"'
    """

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            return variables[var_name]
        # Keep original placeholder if not in variables dict
        return match.group(0)

    return TEMPLATE_VAR_PATTERN.sub(replace_var, template)


def generate_random_identifier(
    length: int = 12,
    prefix: str = "",
    charset: str | None = None,
) -> str:
    """Generate a random identifier for function/variable obfuscation.

    Creates cryptographically random identifiers suitable for Go code.
    Identifiers start with a letter and contain only alphanumeric characters.

    Args:
        length: Total length of the identifier (including prefix).
        prefix: Optional prefix for the identifier.
        charset: Optional custom character set. Defaults to letters + digits.

    Returns:
        A random identifier string.

    Raises:
        ValueError: If length is too short or prefix is invalid.

    Example:
        >>> identifier = generate_random_identifier(12)
        >>> len(identifier)
        12
        >>> identifier[0].isalpha()
        True
    """
    if length < 1:
        raise ValueError("Identifier length must be at least 1")

    if len(prefix) >= length:
        raise ValueError(f"Prefix '{prefix}' is too long for length {length}")

    if charset is None:
        charset = string.ascii_letters + string.digits

    remaining_length = length - len(prefix)

    # First character must be a letter (Go identifier rules)
    if prefix:
        first_char = ""
    else:
        first_char = secrets.choice(string.ascii_letters)
        remaining_length -= 1

    # Generate remaining characters
    remaining_chars = "".join(
        secrets.choice(charset) for _ in range(remaining_length)
    )

    return f"{prefix}{first_char}{remaining_chars}"


def extract_variables(template: str) -> set[str]:
    """Extract all placeholder variable names from a template.

    Args:
        template: The template string to scan.

    Returns:
        Set of variable names found in the template.

    Example:
        >>> extract_variables("{{C2_URL}} and {{MAIN_FUNC}}")
        {'C2_URL', 'MAIN_FUNC'}
    """
    return set(TEMPLATE_VAR_PATTERN.findall(template))


def validate_template(
    template: str,
    required_vars: set[str] | frozenset[str] | None = None,
) -> list[str]:
    """Validate a template and return list of missing required variables.

    Checks that all required variables are present in the template.
    By default, checks for STANDARD_VARIABLES.

    Args:
        template: The template string to validate.
        required_vars: Optional set of required variable names.
                      Defaults to STANDARD_VARIABLES.

    Returns:
        List of missing variable names (empty if all present).

    Example:
        >>> validate_template("const URL = \"{{C2_URL}}\"")
        ['ENCRYPTION_KEY', 'MAIN_FUNC', 'CONNECT_FUNC', 'EXECUTE_FUNC']
    """
    check_vars: set[str] | frozenset[str]
    if required_vars is None:
        check_vars = STANDARD_VARIABLES
    else:
        check_vars = required_vars

    found_vars = extract_variables(template)
    missing = sorted(check_vars - found_vars)

    return missing


def get_available_templates(templates_dir: Path | None = None) -> list[str]:
    """List all available template files in the templates directory.

    Args:
        templates_dir: Optional custom templates directory path.

    Returns:
        List of template filenames (without path).
    """
    if templates_dir is None:
        templates_dir = TEMPLATES_DIR

    if not templates_dir.exists():
        return []

    return sorted(
        f.name for f in templates_dir.glob("*.go") if f.is_file()
    )


def generate_identifier_set(
    count: int,
    length: int = 12,
    prefix: str = "",
) -> set[str]:
    """Generate a set of unique random identifiers.

    Useful for generating multiple unique function/variable names at once.

    Args:
        count: Number of unique identifiers to generate.
        length: Length of each identifier.
        prefix: Optional prefix for all identifiers.

    Returns:
        Set of unique random identifiers.

    Raises:
        ValueError: If unable to generate enough unique identifiers.
    """
    identifiers: set[str] = set()
    max_attempts = count * 10  # Prevent infinite loop

    attempts = 0
    while len(identifiers) < count and attempts < max_attempts:
        identifiers.add(generate_random_identifier(length, prefix))
        attempts += 1

    if len(identifiers) < count:
        raise ValueError(
            f"Could not generate {count} unique identifiers of length {length}"
        )

    return identifiers


def prepare_template(
    template_name: str,
    config_vars: dict[str, str],
    identifier_length: int = 12,
    templates_dir: Path | None = None,
) -> str:
    """Load a template and prepare it with config and random identifiers.

    This is a convenience function that combines loading, identifier
    generation, and variable substitution.

    Args:
        template_name: Name of the template file.
        config_vars: Dictionary of configuration variables (C2_URL, etc.).
        identifier_length: Length for generated random identifiers.
        templates_dir: Optional custom templates directory.

    Returns:
        The fully prepared template with all variables substituted.

    Raises:
        TemplateNotFoundError: If template does not exist.
        TemplateValidationError: If required variables are missing from config.
    """
    template = load_template(template_name, templates_dir)

    # Generate random identifiers for function names
    func_identifiers = {
        "MAIN_FUNC": generate_random_identifier(identifier_length),
        "CONNECT_FUNC": generate_random_identifier(identifier_length),
        "EXECUTE_FUNC": generate_random_identifier(identifier_length),
    }

    # Merge config vars with generated identifiers (config takes precedence)
    all_vars = {**func_identifiers, **config_vars}

    # Set empty defaults for optional block variables
    for opt_var in OPTIONAL_VARIABLES:
        if opt_var not in all_vars:
            all_vars[opt_var] = ""

    # Validate that required config vars are provided
    required_config = {"C2_URL", "ENCRYPTION_KEY"}
    missing_config = required_config - set(config_vars.keys())
    if missing_config:
        raise TemplateValidationError(
            f"Missing required configuration variables: {sorted(missing_config)}"
        )

    return substitute_variables(template, all_vars)
