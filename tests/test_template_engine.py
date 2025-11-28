# test_template_engine module
"""Tests for template engine functionality."""

import re
import string
from pathlib import Path

import pytest

from lib.template_engine import (
    OPTIONAL_VARIABLES,
    STANDARD_VARIABLES,
    TEMPLATE_VAR_PATTERN,
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    extract_variables,
    generate_identifier_set,
    generate_random_identifier,
    get_available_templates,
    load_template,
    prepare_template,
    substitute_variables,
    validate_template,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_templates_dir(tmp_path: Path) -> Path:
    """Create a temporary templates directory with sample templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a basic template
    basic_template = '''package main

const C2_URL = "{{C2_URL}}"
const KEY = "{{ENCRYPTION_KEY}}"

func {{MAIN_FUNC}}() {
    {{CONNECT_FUNC}}()
}

func {{CONNECT_FUNC}}() {}
func {{EXECUTE_FUNC}}(cmd string) {}
'''
    (templates_dir / "test_basic.go").write_text(basic_template)

    # Create a template with optional vars
    advanced_template = '''package main

import (
    {{EVASION_IMPORTS}}
)

const C2_URL = "{{C2_URL}}"
const KEY = "{{ENCRYPTION_KEY}}"

func {{MAIN_FUNC}}() {
    {{EVASION_FUNCTIONS}}
    {{PERSISTENCE_FUNCTIONS}}
    {{FORENSICS_FUNCTIONS}}
    {{CONNECT_FUNC}}()
}

func {{CONNECT_FUNC}}() {}
func {{EXECUTE_FUNC}}(cmd string) {}
'''
    (templates_dir / "test_advanced.go").write_text(advanced_template)

    return templates_dir


@pytest.fixture
def sample_config() -> dict[str, str]:
    """Sample configuration variables."""
    return {
        "C2_URL": "https://10.0.0.1:443",
        "ENCRYPTION_KEY": "supersecretkey123",
    }


# =============================================================================
# Tests for load_template
# =============================================================================


class TestLoadTemplate:
    """Tests for load_template functionality."""

    def test_load_existing_template(self, temp_templates_dir: Path) -> None:
        """Test loading an existing template file."""
        content = load_template("test_basic.go", temp_templates_dir)
        assert "{{C2_URL}}" in content
        assert "{{MAIN_FUNC}}" in content

    def test_load_template_without_extension(self, temp_templates_dir: Path) -> None:
        """Test loading template without .go extension."""
        content = load_template("test_basic", temp_templates_dir)
        assert "{{C2_URL}}" in content

    def test_load_nonexistent_template(self, temp_templates_dir: Path) -> None:
        """Test loading a template that doesn't exist."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            load_template("nonexistent.go", temp_templates_dir)
        assert "not found" in str(exc_info.value).lower()

    def test_load_template_default_dir(self) -> None:
        """Test loading template from default directory."""
        # This should work with the actual templates directory
        content = load_template("implant_go_basic.go")
        assert "{{C2_URL}}" in content


# =============================================================================
# Tests for substitute_variables
# =============================================================================


class TestSubstituteVariables:
    """Tests for substitute_variables functionality."""

    def test_basic_substitution(self) -> None:
        """Test basic variable substitution."""
        template = 'const URL = "{{C2_URL}}"'
        result = substitute_variables(template, {"C2_URL": "https://example.com"})
        assert result == 'const URL = "https://example.com"'

    def test_multiple_substitutions(self) -> None:
        """Test substituting multiple variables."""
        template = "{{VAR1}} and {{VAR2}} and {{VAR1}}"
        result = substitute_variables(template, {"VAR1": "A", "VAR2": "B"})
        assert result == "A and B and A"

    def test_missing_variable_preserved(self) -> None:
        """Test that missing variables are preserved."""
        template = "{{KNOWN}} and {{UNKNOWN}}"
        result = substitute_variables(template, {"KNOWN": "value"})
        assert result == "value and {{UNKNOWN}}"

    def test_empty_variables_dict(self) -> None:
        """Test substitution with empty variables dict."""
        template = "{{VAR1}} {{VAR2}}"
        result = substitute_variables(template, {})
        assert result == "{{VAR1}} {{VAR2}}"

    def test_empty_value_substitution(self) -> None:
        """Test substituting with empty string value."""
        template = "before{{VAR}}after"
        result = substitute_variables(template, {"VAR": ""})
        assert result == "beforeafter"

    def test_multiline_substitution(self) -> None:
        """Test substitution in multiline template."""
        template = """line1 {{VAR1}}
line2 {{VAR2}}
line3 {{VAR1}}"""
        result = substitute_variables(template, {"VAR1": "A", "VAR2": "B"})
        expected = """line1 A
line2 B
line3 A"""
        assert result == expected


# =============================================================================
# Tests for generate_random_identifier
# =============================================================================


class TestGenerateRandomIdentifier:
    """Tests for generate_random_identifier functionality."""

    def test_default_length(self) -> None:
        """Test default identifier length."""
        identifier = generate_random_identifier()
        assert len(identifier) == 12

    def test_custom_length(self) -> None:
        """Test custom identifier length."""
        identifier = generate_random_identifier(length=20)
        assert len(identifier) == 20

    def test_starts_with_letter(self) -> None:
        """Test that identifier starts with a letter."""
        for _ in range(100):  # Test multiple times due to randomness
            identifier = generate_random_identifier()
            assert identifier[0].isalpha()

    def test_alphanumeric_only(self) -> None:
        """Test that identifier contains only alphanumeric characters."""
        for _ in range(50):
            identifier = generate_random_identifier()
            assert identifier.isalnum()

    def test_with_prefix(self) -> None:
        """Test identifier with prefix."""
        identifier = generate_random_identifier(length=15, prefix="fn_")
        assert identifier.startswith("fn_")
        assert len(identifier) == 15

    def test_uniqueness(self) -> None:
        """Test that generated identifiers are unique."""
        identifiers = {generate_random_identifier() for _ in range(100)}
        assert len(identifiers) == 100

    def test_invalid_length(self) -> None:
        """Test that invalid length raises ValueError."""
        with pytest.raises(ValueError):
            generate_random_identifier(length=0)

    def test_prefix_too_long(self) -> None:
        """Test that prefix too long raises ValueError."""
        with pytest.raises(ValueError):
            generate_random_identifier(length=5, prefix="toolongprefix")

    def test_custom_charset(self) -> None:
        """Test identifier with custom charset."""
        charset = "abc"
        identifier = generate_random_identifier(length=10, charset=charset)
        # First char is always a letter (from string.ascii_letters)
        assert identifier[0].isalpha()
        assert all(c in charset or c.isalpha() for c in identifier)


# =============================================================================
# Tests for extract_variables
# =============================================================================


class TestExtractVariables:
    """Tests for extract_variables functionality."""

    def test_extract_single_variable(self) -> None:
        """Test extracting a single variable."""
        result = extract_variables("{{VAR}}")
        assert result == {"VAR"}

    def test_extract_multiple_variables(self) -> None:
        """Test extracting multiple unique variables."""
        result = extract_variables("{{VAR1}} {{VAR2}} {{VAR3}}")
        assert result == {"VAR1", "VAR2", "VAR3"}

    def test_extract_duplicate_variables(self) -> None:
        """Test that duplicates result in single entry."""
        result = extract_variables("{{VAR}} and {{VAR}}")
        assert result == {"VAR"}

    def test_extract_no_variables(self) -> None:
        """Test template with no variables."""
        result = extract_variables("no variables here")
        assert result == set()

    def test_extract_from_real_template(self, temp_templates_dir: Path) -> None:
        """Test extracting variables from a real template."""
        content = load_template("test_basic.go", temp_templates_dir)
        variables = extract_variables(content)
        assert STANDARD_VARIABLES.issubset(variables)


# =============================================================================
# Tests for validate_template
# =============================================================================


class TestValidateTemplate:
    """Tests for validate_template functionality."""

    def test_all_standard_vars_present(self, temp_templates_dir: Path) -> None:
        """Test validation passes with all standard vars."""
        content = load_template("test_basic.go", temp_templates_dir)
        missing = validate_template(content)
        assert missing == []

    def test_missing_variables(self) -> None:
        """Test validation detects missing variables."""
        template = "{{C2_URL}} only"
        missing = validate_template(template)
        assert "ENCRYPTION_KEY" in missing
        assert "MAIN_FUNC" in missing
        assert "C2_URL" not in missing

    def test_custom_required_vars(self) -> None:
        """Test validation with custom required vars."""
        template = "{{VAR1}} {{VAR2}}"
        missing = validate_template(template, required_vars={"VAR1", "VAR2", "VAR3"})
        assert missing == ["VAR3"]

    def test_empty_template(self) -> None:
        """Test validation of empty template."""
        missing = validate_template("")
        assert set(missing) == STANDARD_VARIABLES

    def test_sorted_output(self) -> None:
        """Test that missing vars are sorted."""
        template = ""
        missing = validate_template(template, required_vars={"Z_VAR", "A_VAR", "M_VAR"})
        assert missing == ["A_VAR", "M_VAR", "Z_VAR"]


# =============================================================================
# Tests for get_available_templates
# =============================================================================


class TestGetAvailableTemplates:
    """Tests for get_available_templates functionality."""

    def test_list_templates(self, temp_templates_dir: Path) -> None:
        """Test listing available templates."""
        templates = get_available_templates(temp_templates_dir)
        assert "test_basic.go" in templates
        assert "test_advanced.go" in templates

    def test_sorted_output(self, temp_templates_dir: Path) -> None:
        """Test that templates are sorted."""
        templates = get_available_templates(temp_templates_dir)
        assert templates == sorted(templates)

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test listing from nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        templates = get_available_templates(nonexistent)
        assert templates == []

    def test_default_templates_dir(self) -> None:
        """Test listing from default templates directory."""
        templates = get_available_templates()
        assert "implant_go_basic.go" in templates
        assert "implant_go_syscalls.go" in templates


# =============================================================================
# Tests for generate_identifier_set
# =============================================================================


class TestGenerateIdentifierSet:
    """Tests for generate_identifier_set functionality."""

    def test_generate_correct_count(self) -> None:
        """Test generating correct number of identifiers."""
        identifiers = generate_identifier_set(5)
        assert len(identifiers) == 5

    def test_all_unique(self) -> None:
        """Test that all identifiers are unique."""
        identifiers = generate_identifier_set(50, length=8)
        assert len(identifiers) == 50

    def test_with_prefix(self) -> None:
        """Test generating identifiers with prefix."""
        identifiers = generate_identifier_set(5, length=10, prefix="fn")
        assert all(ident.startswith("fn") for ident in identifiers)

    def test_all_valid_go_identifiers(self) -> None:
        """Test that all identifiers are valid Go identifiers."""
        identifiers = generate_identifier_set(20)
        for ident in identifiers:
            assert ident[0].isalpha()
            assert ident.isalnum()


# =============================================================================
# Tests for prepare_template
# =============================================================================


class TestPrepareTemplate:
    """Tests for prepare_template functionality."""

    def test_full_preparation(
        self, temp_templates_dir: Path, sample_config: dict[str, str]
    ) -> None:
        """Test full template preparation."""
        result = prepare_template(
            "test_basic.go",
            sample_config,
            identifier_length=10,
            templates_dir=temp_templates_dir,
        )

        # Config vars should be substituted
        assert "https://10.0.0.1:443" in result
        assert "supersecretkey123" in result

        # Template vars should be replaced with random identifiers
        assert "{{MAIN_FUNC}}" not in result
        assert "{{CONNECT_FUNC}}" not in result
        assert "{{EXECUTE_FUNC}}" not in result

    def test_missing_c2_url(self, temp_templates_dir: Path) -> None:
        """Test error when C2_URL is missing."""
        with pytest.raises(TemplateValidationError) as exc_info:
            prepare_template(
                "test_basic.go",
                {"ENCRYPTION_KEY": "key"},
                templates_dir=temp_templates_dir,
            )
        assert "C2_URL" in str(exc_info.value)

    def test_missing_encryption_key(self, temp_templates_dir: Path) -> None:
        """Test error when ENCRYPTION_KEY is missing."""
        with pytest.raises(TemplateValidationError) as exc_info:
            prepare_template(
                "test_basic.go",
                {"C2_URL": "https://example.com"},
                templates_dir=temp_templates_dir,
            )
        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_optional_vars_default_empty(
        self, temp_templates_dir: Path, sample_config: dict[str, str]
    ) -> None:
        """Test that optional vars default to empty string."""
        result = prepare_template(
            "test_advanced.go",
            sample_config,
            templates_dir=temp_templates_dir,
        )

        # Optional vars should be replaced (with empty string)
        for opt_var in OPTIONAL_VARIABLES:
            assert f"{{{{{opt_var}}}}}" not in result

    def test_custom_identifier_length(
        self, temp_templates_dir: Path, sample_config: dict[str, str]
    ) -> None:
        """Test custom identifier length."""
        result = prepare_template(
            "test_basic.go",
            sample_config,
            identifier_length=20,
            templates_dir=temp_templates_dir,
        )

        # Find the function definitions
        func_pattern = re.compile(r"func (\w+)\(")
        funcs = func_pattern.findall(result)

        # Filter to only randomized funcs (not main)
        random_funcs = [f for f in funcs if f != "main"]
        assert len(random_funcs) > 0
        assert all(len(f) == 20 for f in random_funcs)

    def test_nonexistent_template(
        self, temp_templates_dir: Path, sample_config: dict[str, str]
    ) -> None:
        """Test error with nonexistent template."""
        with pytest.raises(TemplateNotFoundError):
            prepare_template(
                "nonexistent.go",
                sample_config,
                templates_dir=temp_templates_dir,
            )


# =============================================================================
# Tests for TEMPLATE_VAR_PATTERN
# =============================================================================


class TestTemplateVarPattern:
    """Tests for the template variable regex pattern."""

    def test_matches_valid_patterns(self) -> None:
        """Test pattern matches valid variable names."""
        valid = ["{{VAR}}", "{{C2_URL}}", "{{MAIN_FUNC}}", "{{VAR123}}", "{{A}}"]
        for pattern in valid:
            assert TEMPLATE_VAR_PATTERN.search(pattern) is not None

    def test_no_match_invalid_patterns(self) -> None:
        """Test pattern doesn't match invalid variable names."""
        invalid = [
            "{{var}}",  # lowercase
            "{{_VAR}}",  # starts with underscore
            "{{123VAR}}",  # starts with number
            "{{ VAR }}",  # spaces
            "{VAR}",  # single braces
            "{{VAR",  # unclosed
        ]
        for pattern in invalid:
            match = TEMPLATE_VAR_PATTERN.search(pattern)
            if match:
                # If it matches, ensure it's not capturing the invalid parts
                assert match.group(0) != pattern

    def test_captures_variable_name(self) -> None:
        """Test pattern captures the variable name correctly."""
        match = TEMPLATE_VAR_PATTERN.search("prefix{{MY_VAR}}suffix")
        assert match is not None
        assert match.group(1) == "MY_VAR"
