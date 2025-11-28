# test_evasion module
"""Tests for evasion module functionality."""

from pathlib import Path

import pytest

from lib.evasion import (
    EvasionError,
    SnippetNotFoundError,
    build_evasion_functions,
    get_amsi_bypass_code,
    get_available_evasion_techniques,
    get_etw_bypass_code,
    get_evasion_calls,
    get_evasion_imports,
    get_obfuscated_sleep_code,
    get_sandbox_detection_code,
    get_syscall_stub,
    inject_evasion,
    load_snippet,
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
    sample_snippet = """// Sample evasion snippet
package main

func sampleEvasion() error {
    return nil
}
"""
    (snippets_dir / "sample_evasion.go").write_text(sample_snippet)
    return snippets_dir


@pytest.fixture
def basic_evasion_config() -> dict:
    """Basic evasion configuration with all techniques enabled."""
    return {
        "amsi_bypass": True,
        "etw_bypass": True,
        "sandbox_checks": True,
        "obfuscated_sleep": True,
    }


@pytest.fixture
def minimal_evasion_config() -> dict:
    """Minimal evasion configuration with only AMSI bypass."""
    return {
        "amsi_bypass": True,
        "etw_bypass": False,
        "sandbox_checks": False,
    }


@pytest.fixture
def sample_template() -> str:
    """Sample Go template with evasion placeholders."""
    return '''package main

import (
    "time"
    {{EVASION_IMPORTS}}
)

func main() {
    {{EVASION_FUNCTIONS}}
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
    {{EVASION_IMPORTS}}
)

const C2_URL = "https://example.com"

func main() {
    {{EVASION_FUNCTIONS}}
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
        content = load_snippet("sample_evasion.go", temp_snippets_dir)
        assert "sampleEvasion" in content
        assert "package main" in content

    def test_load_snippet_without_extension(self, temp_snippets_dir: Path) -> None:
        """Test loading snippet without .go extension."""
        content = load_snippet("sample_evasion", temp_snippets_dir)
        assert "sampleEvasion" in content

    def test_load_nonexistent_snippet(self, temp_snippets_dir: Path) -> None:
        """Test loading a snippet that doesn't exist."""
        with pytest.raises(SnippetNotFoundError) as exc_info:
            load_snippet("nonexistent.go", temp_snippets_dir)
        assert "not found" in str(exc_info.value).lower()

    def test_load_real_amsi_snippet(self) -> None:
        """Test loading the real AMSI bypass snippet."""
        content = load_snippet("amsi_bypass.go")
        assert "bypassAMSI" in content
        assert "AmsiScanBuffer" in content

    def test_load_real_etw_snippet(self) -> None:
        """Test loading the real ETW bypass snippet."""
        content = load_snippet("etw_bypass.go")
        assert "bypassETW" in content
        assert "EtwEventWrite" in content

    def test_load_real_sandbox_snippet(self) -> None:
        """Test loading the real sandbox detection snippet."""
        content = load_snippet("sandbox_detect.go")
        assert "detectSandbox" in content
        assert "IsDebuggerPresent" in content


# =============================================================================
# Tests for get_amsi_bypass_code
# =============================================================================


class TestGetAmsiBypassCode:
    """Tests for get_amsi_bypass_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that AMSI bypass code is valid Go."""
        code = get_amsi_bypass_code()
        assert "func bypassAMSI()" in code
        assert "error" in code  # Returns error

    def test_contains_amsi_dll(self) -> None:
        """Test that code references amsi.dll."""
        code = get_amsi_bypass_code()
        assert "amsi.dll" in code

    def test_contains_patch_bytes(self) -> None:
        """Test that code contains patch bytes."""
        code = get_amsi_bypass_code()
        assert "0xB8" in code  # mov eax
        assert "0xC3" in code  # ret

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_amsi_bypass_code()
        assert "T1562.001" in code

    def test_uses_virtual_protect(self) -> None:
        """Test that code uses VirtualProtect."""
        code = get_amsi_bypass_code()
        assert "VirtualProtect" in code


# =============================================================================
# Tests for get_etw_bypass_code
# =============================================================================


class TestGetEtwBypassCode:
    """Tests for get_etw_bypass_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that ETW bypass code is valid Go."""
        code = get_etw_bypass_code()
        assert "func bypassETW()" in code
        assert "error" in code

    def test_contains_ntdll(self) -> None:
        """Test that code references ntdll.dll."""
        code = get_etw_bypass_code()
        assert "ntdll.dll" in code

    def test_contains_etw_function(self) -> None:
        """Test that code references EtwEventWrite."""
        code = get_etw_bypass_code()
        assert "EtwEventWrite" in code

    def test_contains_ret_patch(self) -> None:
        """Test that code contains ret instruction patch."""
        code = get_etw_bypass_code()
        assert "0xC3" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_etw_bypass_code()
        assert "T1562.001" in code


# =============================================================================
# Tests for get_sandbox_detection_code
# =============================================================================


class TestGetSandboxDetectionCode:
    """Tests for get_sandbox_detection_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that sandbox detection code is valid Go."""
        code = get_sandbox_detection_code()
        assert "func detectSandbox()" in code
        assert "bool" in code

    def test_contains_time_check(self) -> None:
        """Test that code contains time acceleration check."""
        code = get_sandbox_detection_code()
        assert "time.Sleep" in code
        assert "time.Since" in code

    def test_contains_debugger_check(self) -> None:
        """Test that code contains debugger check."""
        code = get_sandbox_detection_code()
        assert "IsDebuggerPresent" in code

    def test_contains_cpu_check(self) -> None:
        """Test that code contains CPU count check."""
        code = get_sandbox_detection_code()
        assert "NumCPU" in code

    def test_contains_mitre_reference(self) -> None:
        """Test that code contains MITRE ATT&CK reference."""
        code = get_sandbox_detection_code()
        assert "T1497" in code


# =============================================================================
# Tests for get_obfuscated_sleep_code
# =============================================================================


class TestGetObfuscatedSleepCode:
    """Tests for get_obfuscated_sleep_code functionality."""

    def test_returns_valid_go_code(self) -> None:
        """Test that obfuscated sleep code is valid Go."""
        code = get_obfuscated_sleep_code()
        assert "func obfuscatedSleep(" in code

    def test_uses_windows_api(self) -> None:
        """Test that code uses Windows Sleep API."""
        code = get_obfuscated_sleep_code()
        assert "kernel32.dll" in code
        assert "Sleep" in code


# =============================================================================
# Tests for get_evasion_imports
# =============================================================================


class TestGetEvasionImports:
    """Tests for get_evasion_imports functionality."""

    def test_returns_required_imports(self) -> None:
        """Test that imports include required packages."""
        imports = get_evasion_imports()
        assert "syscall" in imports
        assert "unsafe" in imports

    def test_returns_runtime_import(self) -> None:
        """Test that imports include runtime package."""
        imports = get_evasion_imports()
        assert "runtime" in imports


# =============================================================================
# Tests for get_evasion_calls
# =============================================================================


class TestGetEvasionCalls:
    """Tests for get_evasion_calls functionality."""

    def test_all_enabled(self, basic_evasion_config: dict) -> None:
        """Test evasion calls with all techniques enabled."""
        calls = get_evasion_calls(basic_evasion_config)
        assert "detectSandbox()" in calls
        assert "bypassAMSI()" in calls
        assert "bypassETW()" in calls

    def test_only_amsi(self, minimal_evasion_config: dict) -> None:
        """Test evasion calls with only AMSI enabled."""
        calls = get_evasion_calls(minimal_evasion_config)
        assert "bypassAMSI()" in calls
        assert "bypassETW()" not in calls
        assert "detectSandbox()" not in calls

    def test_sandbox_exit(self, basic_evasion_config: dict) -> None:
        """Test that sandbox detection includes exit call."""
        calls = get_evasion_calls(basic_evasion_config)
        assert "os.Exit(0)" in calls

    def test_empty_config(self) -> None:
        """Test evasion calls with empty config."""
        calls = get_evasion_calls({})
        assert calls == ""

    def test_all_disabled(self) -> None:
        """Test evasion calls with all disabled."""
        config = {
            "amsi_bypass": False,
            "etw_bypass": False,
            "sandbox_checks": False,
        }
        calls = get_evasion_calls(config)
        assert calls == ""


# =============================================================================
# Tests for build_evasion_functions
# =============================================================================


class TestBuildEvasionFunctions:
    """Tests for build_evasion_functions functionality."""

    def test_all_enabled(self, basic_evasion_config: dict) -> None:
        """Test building functions with all techniques enabled."""
        functions = build_evasion_functions(basic_evasion_config)
        assert "func bypassAMSI()" in functions
        assert "func bypassETW()" in functions
        assert "func detectSandbox()" in functions
        assert "func obfuscatedSleep(" in functions

    def test_only_amsi(self, minimal_evasion_config: dict) -> None:
        """Test building functions with only AMSI enabled."""
        functions = build_evasion_functions(minimal_evasion_config)
        assert "func bypassAMSI()" in functions
        assert "func bypassETW()" not in functions
        assert "func detectSandbox()" not in functions

    def test_obfuscated_sleep_default_on(self) -> None:
        """Test that obfuscated sleep is on by default."""
        config = {"amsi_bypass": True}
        functions = build_evasion_functions(config)
        assert "func obfuscatedSleep(" in functions

    def test_obfuscated_sleep_disabled(self) -> None:
        """Test disabling obfuscated sleep."""
        config = {"amsi_bypass": True, "obfuscated_sleep": False}
        functions = build_evasion_functions(config)
        assert "func obfuscatedSleep(" not in functions

    def test_empty_config(self) -> None:
        """Test building functions with empty config."""
        # Only obfuscated_sleep should be present (default True)
        functions = build_evasion_functions({})
        assert "func bypassAMSI()" not in functions
        assert "func obfuscatedSleep(" in functions


# =============================================================================
# Tests for inject_evasion
# =============================================================================


class TestInjectEvasion:
    """Tests for inject_evasion functionality."""

    def test_injects_imports(
        self, sample_template: str, basic_evasion_config: dict
    ) -> None:
        """Test that imports are injected."""
        result = inject_evasion(sample_template, basic_evasion_config)
        assert "{{EVASION_IMPORTS}}" not in result
        assert '"syscall"' in result
        assert '"unsafe"' in result

    def test_injects_function_calls(
        self, sample_template: str, basic_evasion_config: dict
    ) -> None:
        """Test that function calls are injected."""
        result = inject_evasion(sample_template, basic_evasion_config)
        assert "{{EVASION_FUNCTIONS}}" not in result
        assert "bypassAMSI()" in result

    def test_injects_function_definitions(
        self, sample_template: str, basic_evasion_config: dict
    ) -> None:
        """Test that function definitions are injected."""
        result = inject_evasion(sample_template, basic_evasion_config)
        assert "func bypassAMSI()" in result
        assert "func bypassETW()" in result

    def test_empty_config_clears_placeholders(self, sample_template: str) -> None:
        """Test that empty config clears placeholders."""
        result = inject_evasion(sample_template, {})
        assert "{{EVASION_FUNCTIONS}}" not in result

    def test_preserves_existing_imports(
        self, template_with_existing_imports: str, basic_evasion_config: dict
    ) -> None:
        """Test that existing imports are preserved."""
        result = inject_evasion(template_with_existing_imports, basic_evasion_config)
        assert '"fmt"' in result
        assert '"net/http"' in result
        assert '"syscall"' in result

    def test_preserves_template_structure(
        self, sample_template: str, basic_evasion_config: dict
    ) -> None:
        """Test that template structure is preserved."""
        result = inject_evasion(sample_template, basic_evasion_config)
        assert "package main" in result
        assert "func main()" in result
        assert "func mainLoop()" in result


# =============================================================================
# Tests for get_syscall_stub
# =============================================================================


class TestGetSyscallStub:
    """Tests for get_syscall_stub functionality."""

    def test_direct_syscall(self) -> None:
        """Test generating direct syscall stub."""
        stub = get_syscall_stub("NtAllocateVirtualMemory", "direct")
        assert "NtAllocateVirtualMemoryDirect" in stub
        assert "direct syscall" in stub.lower()

    def test_indirect_syscall(self) -> None:
        """Test generating indirect syscall stub."""
        stub = get_syscall_stub("NtAllocateVirtualMemory", "indirect")
        assert "NtAllocateVirtualMemoryIndirect" in stub
        assert "ntdll.dll" in stub

    def test_hybrid_syscall(self) -> None:
        """Test generating hybrid syscall stub."""
        stub = get_syscall_stub("NtAllocateVirtualMemory", "hybrid")
        assert "NtAllocateVirtualMemoryHybrid" in stub
        assert "ntdll.dll" in stub

    def test_invalid_syscall_type(self) -> None:
        """Test that invalid syscall type raises error."""
        with pytest.raises(ValueError) as exc_info:
            get_syscall_stub("NtAllocateVirtualMemory", "invalid")
        assert "invalid" in str(exc_info.value).lower()

    def test_contains_mitre_reference(self) -> None:
        """Test that syscall stubs contain MITRE reference."""
        stub = get_syscall_stub("NtAllocateVirtualMemory", "direct")
        assert "T1106" in stub


# =============================================================================
# Tests for get_available_evasion_techniques
# =============================================================================


class TestGetAvailableEvasionTechniques:
    """Tests for get_available_evasion_techniques functionality."""

    def test_returns_dict(self) -> None:
        """Test that function returns a dictionary."""
        techniques = get_available_evasion_techniques()
        assert isinstance(techniques, dict)

    def test_contains_expected_techniques(self) -> None:
        """Test that dict contains expected techniques."""
        techniques = get_available_evasion_techniques()
        assert "amsi_bypass" in techniques
        assert "etw_bypass" in techniques
        assert "sandbox_checks" in techniques

    def test_descriptions_contain_mitre(self) -> None:
        """Test that descriptions reference MITRE ATT&CK."""
        techniques = get_available_evasion_techniques()
        # At least some techniques should have MITRE references
        mitre_refs = sum(1 for desc in techniques.values() if "T1" in desc)
        assert mitre_refs >= 3


# =============================================================================
# Integration Tests
# =============================================================================


class TestEvasionIntegration:
    """Integration tests for evasion module."""

    def test_full_injection_workflow(self) -> None:
        """Test complete injection workflow with real template."""
        from lib.template_engine import load_template

        # Load the basic template that has evasion placeholders
        template = load_template("implant_go_basic.go")

        config = {
            "amsi_bypass": True,
            "etw_bypass": True,
            "sandbox_checks": True,
        }

        result = inject_evasion(template, config)

        # Verify all placeholders are replaced
        assert "{{EVASION_IMPORTS}}" not in result
        assert "{{EVASION_FUNCTIONS}}" not in result

        # Verify evasion code is present
        assert '"syscall"' in result
        assert "bypassAMSI()" in result

    def test_no_duplicate_functions(self) -> None:
        """Test that function definitions aren't duplicated."""
        template = """package main

func main() {
    {{EVASION_FUNCTIONS}}
}
"""
        config = {"amsi_bypass": True}
        result = inject_evasion(template, config)

        # Count occurrences of function definition
        count = result.count("func bypassAMSI()")
        assert count == 1

    def test_generated_code_syntax(self) -> None:
        """Test that generated code has valid Go syntax patterns."""
        config = {
            "amsi_bypass": True,
            "etw_bypass": True,
            "sandbox_checks": True,
        }
        functions = build_evasion_functions(config)

        # Check for balanced braces (basic syntax check)
        open_braces = functions.count("{")
        close_braces = functions.count("}")
        assert open_braces == close_braces

        # Check for proper function signatures
        assert "func bypassAMSI() error {" in functions
        assert "func bypassETW() error {" in functions
        assert "func detectSandbox() bool {" in functions
