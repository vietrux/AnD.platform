# test_persistence module
"""Tests for persistence module functionality."""

from pathlib import Path

import pytest

from lib.persistence import (
    PersistenceError,
    SnippetNotFoundError,
    build_persistence_functions,
    get_available_persistence_methods,
    get_com_hijack_code,
    get_persistence_calls,
    get_persistence_imports,
    get_registry_persistence_code,
    get_schtasks_persistence_code,
    get_startup_folder_code,
    get_wmi_persistence_code,
    inject_persistence,
    load_snippet,
    remove_persistence,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_snippets_dir(tmp_path: Path) -> Path:
    """Create a temporary snippets directory with sample snippets."""
    snippets_dir = tmp_path / "snippets"
    snippets_dir.mkdir()

    # Create a sample snippet
    sample_snippet = """// Sample persistence snippet
package main

func samplePersistence() error {
    return nil
}
"""
    (snippets_dir / "sample_persistence.go").write_text(sample_snippet)
    return snippets_dir


@pytest.fixture
def basic_persistence_config() -> dict:
    """Basic persistence configuration with all methods enabled."""
    return {
        "enabled": True,
        "methods": ["registry", "schtasks", "wmi", "com_hijack"],
    }


@pytest.fixture
def minimal_persistence_config() -> dict:
    """Minimal persistence configuration with only registry."""
    return {
        "enabled": True,
        "methods": ["registry"],
    }


@pytest.fixture
def disabled_persistence_config() -> dict:
    """Persistence configuration with persistence disabled."""
    return {
        "enabled": False,
        "methods": ["registry", "schtasks"],
    }


@pytest.fixture
def custom_persistence_config() -> dict:
    """Persistence configuration with custom values."""
    return {
        "enabled": True,
        "methods": ["registry", "schtasks"],
        "registry_key_path": r"Software\CustomApp\Run",
        "registry_value_name": "CustomUpdate",
        "task_name": "CustomTaskName",
        "task_trigger": "DAILY",
    }


@pytest.fixture
def sample_template() -> str:
    """Sample Go template with persistence placeholders."""
    return '''package main

import (
    "time"
    {{PERSISTENCE_IMPORTS}}
)

func main() {
    {{PERSISTENCE_FUNCTIONS}}
    mainLoop()
}

func mainLoop() {
    for {
        time.Sleep(5 * time.Second)
    }
}
'''


@pytest.fixture
def template_with_existing_imports() -> str:
    """Template with existing imports to test import injection."""
    return '''package main

import (
    "fmt"
    "net/http"
    {{PERSISTENCE_IMPORTS}}
)

const C2_URL = "https://example.com"

func main() {
    {{PERSISTENCE_FUNCTIONS}}
    fmt.Println("Starting...")
}
'''


# =============================================================================
# Tests for load_snippet
# =============================================================================


class TestLoadSnippet:
    """Tests for load_snippet functionality."""

    def test_load_existing_snippet(self, temp_snippets_dir: Path) -> None:
        """Test loading an existing snippet file."""
        content = load_snippet("sample_persistence.go", temp_snippets_dir)
        assert "samplePersistence" in content
        assert "package main" in content

    def test_load_snippet_without_extension(self, temp_snippets_dir: Path) -> None:
        """Test loading snippet without .go extension."""
        content = load_snippet("sample_persistence", temp_snippets_dir)
        assert "samplePersistence" in content

    def test_load_nonexistent_snippet(self, temp_snippets_dir: Path) -> None:
        """Test loading a snippet that doesn't exist."""
        with pytest.raises(SnippetNotFoundError) as exc_info:
            load_snippet("nonexistent.go", temp_snippets_dir)
        assert "not found" in str(exc_info.value).lower()

    def test_load_real_registry_snippet(self) -> None:
        """Test loading the real registry persistence snippet."""
        content = load_snippet("persistence_registry.go")
        assert "installRegistryPersistence" in content
        assert "registry" in content.lower()

    def test_load_real_schtasks_snippet(self) -> None:
        """Test loading the real schtasks persistence snippet."""
        content = load_snippet("persistence_schtasks.go")
        assert "installScheduledTaskPersistence" in content
        assert "schtasks" in content.lower()

    def test_load_real_wmi_snippet(self) -> None:
        """Test loading the real WMI persistence snippet."""
        content = load_snippet("persistence_wmi.go")
        assert "installWMIPersistence" in content
        assert "WMI" in content or "wmi" in content.lower()

    def test_load_real_com_hijack_snippet(self) -> None:
        """Test loading the real COM hijack persistence snippet."""
        content = load_snippet("persistence_com_hijack.go")
        assert "installCOMHijackPersistence" in content
        assert "CLSID" in content


# =============================================================================
# Tests for get_registry_persistence_code
# =============================================================================


class TestGetRegistryPersistenceCode:
    """Tests for get_registry_persistence_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that registry persistence code is valid Go."""
        code = get_registry_persistence_code()
        assert "func installRegistryPersistence()" in code
        assert "error" in code  # Returns error

    def test_contains_registry_key(self) -> None:
        """Test that code references the Run key."""
        code = get_registry_persistence_code()
        assert "Run" in code
        assert "CurrentVersion" in code

    def test_uses_hkcu(self) -> None:
        """Test that code uses HKEY_CURRENT_USER."""
        code = get_registry_persistence_code()
        assert "CURRENT_USER" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_registry_persistence_code()
        assert "T1547.001" in code

    def test_custom_key_path(self) -> None:
        """Test custom registry key path."""
        code = get_registry_persistence_code(
            key_path=r"Software\CustomApp\Run",
            value_name="CustomValue"
        )
        assert "CustomApp" in code
        assert "CustomValue" in code

    def test_default_value_name(self) -> None:
        """Test default value name is WindowsUpdate."""
        code = get_registry_persistence_code()
        assert "WindowsUpdate" in code


# =============================================================================
# Tests for get_schtasks_persistence_code
# =============================================================================


class TestGetSchtasksPersistenceCode:
    """Tests for get_schtasks_persistence_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that schtasks persistence code is valid Go."""
        code = get_schtasks_persistence_code()
        assert "func installScheduledTaskPersistence()" in code
        assert "error" in code

    def test_contains_schtasks_command(self) -> None:
        """Test that code uses schtasks.exe."""
        code = get_schtasks_persistence_code()
        assert "schtasks.exe" in code

    def test_contains_create_option(self) -> None:
        """Test that code uses /Create option."""
        code = get_schtasks_persistence_code()
        assert "/Create" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_schtasks_persistence_code()
        assert "T1053.005" in code

    def test_custom_task_name(self) -> None:
        """Test custom task name."""
        code = get_schtasks_persistence_code(task_name="CustomTask")
        assert "CustomTask" in code

    def test_default_trigger_onlogon(self) -> None:
        """Test default trigger is ONLOGON."""
        code = get_schtasks_persistence_code()
        assert "ONLOGON" in code

    def test_custom_trigger(self) -> None:
        """Test custom trigger."""
        code = get_schtasks_persistence_code(trigger="DAILY")
        assert "DAILY" in code

    def test_hidden_window(self) -> None:
        """Test that command runs with hidden window."""
        code = get_schtasks_persistence_code()
        assert "HideWindow" in code


# =============================================================================
# Tests for get_wmi_persistence_code
# =============================================================================


class TestGetWmiPersistenceCode:
    """Tests for get_wmi_persistence_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that WMI persistence code is valid Go."""
        code = get_wmi_persistence_code()
        assert "func installWMIPersistence()" in code
        assert "error" in code

    def test_contains_wmi_namespace(self) -> None:
        """Test that code references WMI namespace."""
        code = get_wmi_persistence_code()
        assert "root\\subscription" in code or "root\\\\subscription" in code

    def test_contains_event_filter(self) -> None:
        """Test that code creates __EventFilter."""
        code = get_wmi_persistence_code()
        assert "__EventFilter" in code

    def test_contains_event_consumer(self) -> None:
        """Test that code creates CommandLineEventConsumer."""
        code = get_wmi_persistence_code()
        assert "CommandLineEventConsumer" in code

    def test_contains_binding(self) -> None:
        """Test that code creates FilterToConsumerBinding."""
        code = get_wmi_persistence_code()
        assert "FilterToConsumerBinding" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_wmi_persistence_code()
        assert "T1546.003" in code

    def test_custom_event_name(self) -> None:
        """Test custom event filter name."""
        code = get_wmi_persistence_code(event_name="CustomEventFilter")
        assert "CustomEventFilter" in code


# =============================================================================
# Tests for get_com_hijack_code
# =============================================================================


class TestGetComHijackCode:
    """Tests for get_com_hijack_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that COM hijack code is valid Go."""
        code = get_com_hijack_code()
        assert "func installCOMHijackPersistence()" in code
        assert "error" in code

    def test_contains_clsid(self) -> None:
        """Test that code references CLSID."""
        code = get_com_hijack_code()
        assert "CLSID" in code

    def test_uses_hkcu(self) -> None:
        """Test that code uses HKEY_CURRENT_USER."""
        code = get_com_hijack_code()
        assert "CURRENT_USER" in code

    def test_contains_inprocserver32(self) -> None:
        """Test that code references InprocServer32."""
        code = get_com_hijack_code()
        assert "InprocServer32" in code

    def test_contains_threading_model(self) -> None:
        """Test that code sets ThreadingModel."""
        code = get_com_hijack_code()
        assert "ThreadingModel" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_com_hijack_code()
        assert "T1546.015" in code

    def test_default_clsid(self) -> None:
        """Test default CLSID is Thumbcache."""
        code = get_com_hijack_code()
        assert "AB8902B4-09CA-4bb6-B78D-A8F59079A8D5" in code

    def test_custom_clsid(self) -> None:
        """Test custom CLSID."""
        code = get_com_hijack_code(clsid="{12345678-1234-1234-1234-123456789ABC}")
        assert "12345678-1234-1234-1234-123456789ABC" in code


# =============================================================================
# Tests for get_startup_folder_code
# =============================================================================


class TestGetStartupFolderCode:
    """Tests for get_startup_folder_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that startup folder code is valid Go."""
        code = get_startup_folder_code()
        assert "func installStartupFolderPersistence()" in code
        assert "error" in code

    def test_contains_appdata(self) -> None:
        """Test that code references APPDATA."""
        code = get_startup_folder_code()
        assert "APPDATA" in code

    def test_contains_startup_path(self) -> None:
        """Test that code references Startup folder path."""
        code = get_startup_folder_code()
        assert "Startup" in code
        assert "Start Menu" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_startup_folder_code()
        assert "T1547.001" in code


# =============================================================================
# Tests for get_persistence_imports
# =============================================================================


class TestGetPersistenceImports:
    """Tests for get_persistence_imports functionality."""

    def test_returns_required_imports(self) -> None:
        """Test that imports include required packages."""
        imports = get_persistence_imports()
        assert "os" in imports
        assert "syscall" in imports

    def test_returns_exec_import(self) -> None:
        """Test that imports include os/exec package."""
        imports = get_persistence_imports()
        assert "os/exec" in imports

    def test_returns_registry_import(self) -> None:
        """Test that imports include registry package."""
        imports = get_persistence_imports()
        assert "registry" in imports


# =============================================================================
# Tests for get_persistence_calls
# =============================================================================


class TestGetPersistenceCalls:
    """Tests for get_persistence_calls functionality."""

    def test_all_methods_enabled(self, basic_persistence_config: dict) -> None:
        """Test persistence calls with all methods enabled."""
        calls = get_persistence_calls(basic_persistence_config)
        assert "installRegistryPersistence()" in calls
        assert "installScheduledTaskPersistence()" in calls
        assert "installWMIPersistence()" in calls
        assert "installCOMHijackPersistence()" in calls

    def test_only_registry(self, minimal_persistence_config: dict) -> None:
        """Test persistence calls with only registry enabled."""
        calls = get_persistence_calls(minimal_persistence_config)
        assert "installRegistryPersistence()" in calls
        assert "installScheduledTaskPersistence()" not in calls
        assert "installWMIPersistence()" not in calls
        assert "installCOMHijackPersistence()" not in calls

    def test_empty_methods(self) -> None:
        """Test persistence calls with empty methods list."""
        calls = get_persistence_calls({"methods": []})
        assert calls == ""

    def test_empty_config(self) -> None:
        """Test persistence calls with empty config."""
        calls = get_persistence_calls({})
        assert calls == ""

    def test_startup_folder_method(self) -> None:
        """Test persistence calls include startup folder."""
        config = {"methods": ["startup_folder"]}
        calls = get_persistence_calls(config)
        assert "installStartupFolderPersistence()" in calls


# =============================================================================
# Tests for build_persistence_functions
# =============================================================================


class TestBuildPersistenceFunctions:
    """Tests for build_persistence_functions functionality."""

    def test_all_methods_enabled(self, basic_persistence_config: dict) -> None:
        """Test building functions with all methods enabled."""
        functions = build_persistence_functions(basic_persistence_config)
        assert "func installRegistryPersistence()" in functions
        assert "func installScheduledTaskPersistence()" in functions
        assert "func installWMIPersistence()" in functions
        assert "func installCOMHijackPersistence()" in functions

    def test_only_registry(self, minimal_persistence_config: dict) -> None:
        """Test building functions with only registry enabled."""
        functions = build_persistence_functions(minimal_persistence_config)
        assert "func installRegistryPersistence()" in functions
        assert "func installScheduledTaskPersistence()" not in functions
        assert "func installWMIPersistence()" not in functions

    def test_empty_methods(self) -> None:
        """Test building functions with empty methods list."""
        functions = build_persistence_functions({"methods": []})
        assert functions == ""

    def test_custom_config_values(self, custom_persistence_config: dict) -> None:
        """Test building functions with custom config values."""
        functions = build_persistence_functions(custom_persistence_config)
        assert "CustomApp" in functions
        assert "CustomUpdate" in functions
        assert "CustomTaskName" in functions
        assert "DAILY" in functions


# =============================================================================
# Tests for inject_persistence
# =============================================================================


class TestInjectPersistence:
    """Tests for inject_persistence functionality."""

    def test_injects_imports(
        self, sample_template: str, basic_persistence_config: dict
    ) -> None:
        """Test that imports are injected."""
        result = inject_persistence(sample_template, basic_persistence_config)
        assert "{{PERSISTENCE_IMPORTS}}" not in result
        assert '"os"' in result
        assert '"syscall"' in result

    def test_injects_function_calls(
        self, sample_template: str, basic_persistence_config: dict
    ) -> None:
        """Test that function calls are injected."""
        result = inject_persistence(sample_template, basic_persistence_config)
        assert "{{PERSISTENCE_FUNCTIONS}}" not in result
        assert "installRegistryPersistence()" in result

    def test_injects_function_definitions(
        self, sample_template: str, basic_persistence_config: dict
    ) -> None:
        """Test that function definitions are injected."""
        result = inject_persistence(sample_template, basic_persistence_config)
        assert "func installRegistryPersistence()" in result
        assert "func installScheduledTaskPersistence()" in result

    def test_disabled_clears_placeholders(
        self, sample_template: str, disabled_persistence_config: dict
    ) -> None:
        """Test that disabled config clears placeholders."""
        result = inject_persistence(sample_template, disabled_persistence_config)
        assert "{{PERSISTENCE_FUNCTIONS}}" not in result
        assert "{{PERSISTENCE_IMPORTS}}" not in result
        assert "installRegistryPersistence()" not in result

    def test_preserves_existing_imports(
        self, template_with_existing_imports: str, basic_persistence_config: dict
    ) -> None:
        """Test that existing imports are preserved."""
        result = inject_persistence(template_with_existing_imports, basic_persistence_config)
        assert '"fmt"' in result
        assert '"net/http"' in result
        assert '"os"' in result

    def test_preserves_template_structure(
        self, sample_template: str, basic_persistence_config: dict
    ) -> None:
        """Test that template structure is preserved."""
        result = inject_persistence(sample_template, basic_persistence_config)
        assert "package main" in result
        assert "func main()" in result
        assert "func mainLoop()" in result


# =============================================================================
# Tests for remove_persistence
# =============================================================================


class TestRemovePersistence:
    """Tests for remove_persistence functionality."""

    def test_remove_registry(self) -> None:
        """Test removal code for registry persistence."""
        code = remove_persistence("registry")
        assert "removeRegistryPersistence" in code
        assert "DeleteValue" in code

    def test_remove_schtasks(self) -> None:
        """Test removal code for schtasks persistence."""
        code = remove_persistence("schtasks")
        assert "removeScheduledTaskPersistence" in code
        assert "/Delete" in code

    def test_remove_wmi(self) -> None:
        """Test removal code for WMI persistence."""
        code = remove_persistence("wmi")
        assert "removeWMIPersistence" in code
        assert "Remove-WmiObject" in code

    def test_remove_com_hijack(self) -> None:
        """Test removal code for COM hijack persistence."""
        code = remove_persistence("com_hijack")
        assert "removeCOMHijackPersistence" in code
        assert "DeleteKey" in code

    def test_remove_startup_folder(self) -> None:
        """Test removal code for startup folder persistence."""
        code = remove_persistence("startup_folder")
        assert "removeStartupFolderPersistence" in code
        assert "os.Remove" in code

    def test_invalid_method(self) -> None:
        """Test that invalid method raises error."""
        with pytest.raises(ValueError) as exc_info:
            remove_persistence("invalid_method")
        assert "unknown" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


# =============================================================================
# Tests for get_available_persistence_methods
# =============================================================================


class TestGetAvailablePersistenceMethods:
    """Tests for get_available_persistence_methods functionality."""

    def test_returns_dict(self) -> None:
        """Test that function returns a dictionary."""
        methods = get_available_persistence_methods()
        assert isinstance(methods, dict)

    def test_contains_expected_methods(self) -> None:
        """Test that dict contains expected methods."""
        methods = get_available_persistence_methods()
        assert "registry" in methods
        assert "schtasks" in methods
        assert "wmi" in methods
        assert "com_hijack" in methods
        assert "startup_folder" in methods

    def test_descriptions_contain_mitre(self) -> None:
        """Test that descriptions reference MITRE ATT&CK."""
        methods = get_available_persistence_methods()
        # All methods should have MITRE references
        mitre_refs = sum(1 for desc in methods.values() if "T1" in desc)
        assert mitre_refs >= 4


# =============================================================================
# Integration Tests
# =============================================================================


class TestPersistenceIntegration:
    """Integration tests for persistence module."""

    def test_full_injection_workflow(self) -> None:
        """Test complete injection workflow with real template."""
        from lib.template_engine import load_template

        # Load the syscalls template that has persistence placeholders
        template = load_template("implant_go_syscalls.go")

        config = {
            "enabled": True,
            "methods": ["registry", "schtasks"],
        }

        result = inject_persistence(template, config)

        # Verify placeholder is replaced
        assert "{{PERSISTENCE_FUNCTIONS}}" not in result

        # Verify persistence code is present
        assert "installRegistryPersistence()" in result or "func installRegistryPersistence()" in result

    def test_no_duplicate_functions(self) -> None:
        """Test that function definitions aren't duplicated."""
        template = """package main

func main() {
    {{PERSISTENCE_FUNCTIONS}}
}
"""
        config = {"enabled": True, "methods": ["registry"]}
        result = inject_persistence(template, config)

        # Count occurrences of function definition
        count = result.count("func installRegistryPersistence()")
        assert count == 1

    def test_generated_code_syntax(self) -> None:
        """Test that generated code has valid Go syntax patterns."""
        config = {
            "enabled": True,
            "methods": ["registry", "schtasks", "wmi", "com_hijack"],
        }
        functions = build_persistence_functions(config)

        # Check for balanced braces (basic syntax check)
        open_braces = functions.count("{")
        close_braces = functions.count("}")
        assert open_braces == close_braces

        # Check for proper function signatures
        assert "func installRegistryPersistence() error {" in functions
        assert "func installScheduledTaskPersistence() error {" in functions
        assert "func installWMIPersistence() error {" in functions
        assert "func installCOMHijackPersistence() error {" in functions

    def test_combined_with_evasion(self) -> None:
        """Test that persistence works alongside evasion."""
        from lib.evasion import inject_evasion

        template = """package main

import (
    {{EVASION_IMPORTS}}
    {{PERSISTENCE_IMPORTS}}
)

func main() {
    {{EVASION_FUNCTIONS}}
    {{PERSISTENCE_FUNCTIONS}}
}
"""
        evasion_config = {"amsi_bypass": True}
        persistence_config = {"enabled": True, "methods": ["registry"]}

        # Apply both
        result = inject_evasion(template, evasion_config)
        result = inject_persistence(result, persistence_config)

        # Verify both are injected
        assert "bypassAMSI()" in result
        assert "installRegistryPersistence()" in result
