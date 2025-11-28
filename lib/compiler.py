# compiler module
"""Go compiler wrapper for cross-compiling Windows payloads.

This module provides functionality for compiling Go source code into
Windows executables with proper cross-compilation support, debug symbol
stripping, and build artifact cleanup.

Features:
- Cross-compilation for Windows (x64/x86) from Linux/macOS
- Debug symbol stripping for smaller binaries
- Build artifact cleanup
- Configurable compiler paths via config.yaml
"""

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml


# Default config file path
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

# Supported target operating systems
SUPPORTED_OS = frozenset({"windows", "linux", "darwin"})

# Supported architectures
SUPPORTED_ARCH = frozenset({"amd64", "386", "arm64"})

# Architecture mapping from user-friendly names
ARCH_MAP = {
    "x64": "amd64",
    "x86": "386",
    "arm64": "arm64",
    "amd64": "amd64",
    "386": "386",
}

# Logger for this module
logger = logging.getLogger(__name__)


class CompilerError(Exception):
    """Base exception for compiler errors."""
    pass


class CompilerNotFoundError(CompilerError):
    """Raised when the Go compiler cannot be found."""
    pass


class CompilationError(CompilerError):
    """Raised when compilation fails."""
    pass


class ConfigurationError(CompilerError):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class CompileResult:
    """Result of a compilation operation.
    
    Attributes:
        success: Whether compilation succeeded.
        output_path: Path to the compiled binary (if successful).
        stdout: Compiler stdout output.
        stderr: Compiler stderr output.
        return_code: Compiler process return code.
    """
    success: bool
    output_path: str | None
    stdout: str
    stderr: str
    return_code: int


def load_config(config_path: Path | None = None) -> dict:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to project config.yaml.
    
    Returns:
        Configuration dictionary.
    
    Raises:
        ConfigurationError: If config file cannot be loaded.
    """
    if config_path is None:
        config_path = CONFIG_PATH
    
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse config file: {e}") from e
    except OSError as e:
        raise ConfigurationError(f"Failed to read config file: {e}") from e


def get_compiler_path(config: dict | None = None) -> str:
    """Get the Go compiler path from configuration.
    
    Searches for the Go compiler in the following order:
    1. Path specified in config.yaml
    2. GOROOT/bin/go environment variable
    3. System PATH
    
    Args:
        config: Optional configuration dictionary.
    
    Returns:
        Absolute path to the Go compiler.
    
    Raises:
        CompilerNotFoundError: If Go compiler cannot be found.
    """
    # Try config path first
    if config:
        config_go_path = config.get("compiler_paths", {}).get("go")
        if config_go_path and Path(config_go_path).exists():
            return str(Path(config_go_path).resolve())
    
    # Try GOROOT environment variable
    goroot = os.environ.get("GOROOT")
    if goroot:
        goroot_bin = Path(goroot) / "bin" / "go"
        if goroot_bin.exists():
            return str(goroot_bin.resolve())
    
    # Try system PATH
    go_path = shutil.which("go")
    if go_path:
        return go_path
    
    raise CompilerNotFoundError(
        "Go compiler not found. Please install Go or configure compiler_paths.go in config.yaml"
    )


def get_mingw_path(config: dict | None = None) -> str | None:
    """Get the MinGW compiler path for CGO cross-compilation.
    
    Args:
        config: Optional configuration dictionary.
    
    Returns:
        Path to MinGW compiler or None if not configured.
    """
    if config:
        mingw_path = config.get("compiler_paths", {}).get("mingw")
        if mingw_path and Path(mingw_path).exists():
            return str(Path(mingw_path).resolve())
    
    # Try common MinGW paths
    common_paths = [
        "/usr/bin/x86_64-w64-mingw32-gcc",
        "/usr/local/bin/x86_64-w64-mingw32-gcc",
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    # Try system PATH
    return shutil.which("x86_64-w64-mingw32-gcc")


def build_ldflags(
    strip_debug: bool = True,
    strip_dwarf: bool = True,
    additional_flags: list[str] | None = None,
) -> str:
    """Build linker flags for Go compilation.
    
    Args:
        strip_debug: Strip debug information (-s flag).
        strip_dwarf: Strip DWARF symbol table (-w flag).
        additional_flags: Additional ldflags to include.
    
    Returns:
        Formatted ldflags string for -ldflags argument.
    
    Example:
        >>> build_ldflags()
        '-s -w'
        >>> build_ldflags(additional_flags=['-H=windowsgui'])
        '-s -w -H=windowsgui'
    """
    flags: list[str] = []
    
    if strip_debug:
        flags.append("-s")
    
    if strip_dwarf:
        flags.append("-w")
    
    if additional_flags:
        flags.extend(additional_flags)
    
    return " ".join(flags)


def build_environment(
    target_os: str,
    arch: str,
    cgo_enabled: bool = False,
    mingw_path: str | None = None,
) -> dict[str, str]:
    """Build environment variables for cross-compilation.
    
    Args:
        target_os: Target operating system (windows, linux, darwin).
        arch: Target architecture (amd64, 386, arm64).
        cgo_enabled: Whether to enable CGO (requires MinGW for Windows).
        mingw_path: Path to MinGW compiler for CGO.
    
    Returns:
        Dictionary of environment variables.
    """
    env = os.environ.copy()
    
    # Set Go cross-compilation variables
    env["GOOS"] = target_os
    env["GOARCH"] = arch
    
    # CGO settings
    if cgo_enabled:
        env["CGO_ENABLED"] = "1"
        if mingw_path and target_os == "windows":
            env["CC"] = mingw_path
    else:
        env["CGO_ENABLED"] = "0"
    
    return env


def compile_go(
    source_path: str | Path,
    output_path: str | Path,
    target_os: Literal["windows", "linux", "darwin"] = "windows",
    arch: str = "x64",
    strip_symbols: bool = True,
    cgo_enabled: bool = False,
    gui_app: bool = False,
    config: dict | None = None,
    timeout: int = 300,
) -> CompileResult:
    """Compile Go source code to a binary.
    
    Cross-compiles Go source to the specified target platform with
    optional symbol stripping and GUI subsystem settings.
    
    Args:
        source_path: Path to the Go source file.
        output_path: Path for the output binary.
        target_os: Target operating system.
        arch: Target architecture (x64, x86, arm64).
        strip_symbols: Strip debug symbols from binary.
        cgo_enabled: Enable CGO (requires MinGW for Windows cross-compile).
        gui_app: Build as Windows GUI app (no console window).
        config: Optional configuration dictionary.
        timeout: Compilation timeout in seconds.
    
    Returns:
        CompileResult with compilation status and output.
    
    Raises:
        CompilerNotFoundError: If Go compiler not found.
        CompilationError: If compilation fails.
        ValueError: If invalid target_os or arch specified.
    
    Example:
        >>> result = compile_go("implant.go", "payload.exe", target_os="windows", arch="x64")
        >>> if result.success:
        ...     print(f"Binary created: {result.output_path}")
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    
    # Validate inputs
    if not source_path.exists():
        raise CompilationError(f"Source file not found: {source_path}")
    
    if target_os not in SUPPORTED_OS:
        raise ValueError(f"Unsupported target OS: {target_os}. Supported: {SUPPORTED_OS}")
    
    # Map architecture name
    go_arch = ARCH_MAP.get(arch)
    if go_arch is None:
        raise ValueError(f"Unsupported architecture: {arch}. Supported: {list(ARCH_MAP.keys())}")
    
    # Load config if not provided
    if config is None:
        try:
            config = load_config()
        except ConfigurationError:
            config = {}
    
    # Get compiler path
    go_compiler = get_compiler_path(config)
    
    # Build ldflags
    extra_ldflags: list[str] = []
    if gui_app and target_os == "windows":
        extra_ldflags.append("-H=windowsgui")
    
    ldflags = build_ldflags(
        strip_debug=strip_symbols,
        strip_dwarf=strip_symbols,
        additional_flags=extra_ldflags if extra_ldflags else None,
    )
    
    # Get MinGW path for CGO
    mingw_path = get_mingw_path(config) if cgo_enabled else None
    
    # Build environment
    env = build_environment(
        target_os=target_os,
        arch=go_arch,
        cgo_enabled=cgo_enabled,
        mingw_path=mingw_path,
    )
    
    # Build command
    cmd = [
        go_compiler,
        "build",
        "-o", str(output_path),
        "-ldflags", ldflags,
        "-trimpath",  # Remove file system paths from binary
    ]
    
    # Add source file
    cmd.append(str(source_path))
    
    logger.info(f"Compiling {source_path} -> {output_path}")
    logger.debug(f"Command: {' '.join(cmd)}")
    logger.debug(f"Environment: GOOS={env['GOOS']}, GOARCH={env['GOARCH']}, CGO_ENABLED={env['CGO_ENABLED']}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=source_path.parent,
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info(f"Compilation successful: {output_path}")
        else:
            logger.error(f"Compilation failed: {result.stderr}")
        
        return CompileResult(
            success=success,
            output_path=str(output_path) if success else None,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )
    
    except subprocess.TimeoutExpired:
        raise CompilationError(f"Compilation timed out after {timeout} seconds")
    except FileNotFoundError:
        raise CompilerNotFoundError(f"Go compiler not found at: {go_compiler}")
    except OSError as e:
        raise CompilationError(f"Failed to execute compiler: {e}") from e


def compile_go_source(
    source_code: str,
    output_path: str | Path,
    target_os: Literal["windows", "linux", "darwin"] = "windows",
    arch: str = "x64",
    strip_symbols: bool = True,
    cgo_enabled: bool = False,
    gui_app: bool = False,
    config: dict | None = None,
    timeout: int = 300,
    cleanup: bool = True,
) -> CompileResult:
    """Compile Go source code string to a binary.
    
    Creates a temporary file with the source code, compiles it,
    and optionally cleans up the temporary file.
    
    Args:
        source_code: Go source code as a string.
        output_path: Path for the output binary.
        target_os: Target operating system.
        arch: Target architecture.
        strip_symbols: Strip debug symbols.
        cgo_enabled: Enable CGO.
        gui_app: Build as GUI app.
        config: Optional configuration dictionary.
        timeout: Compilation timeout.
        cleanup: Remove temporary source file after compilation.
    
    Returns:
        CompileResult with compilation status.
    
    Example:
        >>> source = '''
        ... package main
        ... func main() { println("hello") }
        ... '''
        >>> result = compile_go_source(source, "hello.exe")
    """
    # Create temporary directory for source file
    temp_dir = Path(tempfile.mkdtemp(prefix="sliver_compile_"))
    source_file = temp_dir / "main.go"
    
    try:
        # Write source to temp file
        source_file.write_text(source_code, encoding="utf-8")
        
        # Compile
        return compile_go(
            source_path=source_file,
            output_path=output_path,
            target_os=target_os,
            arch=arch,
            strip_symbols=strip_symbols,
            cgo_enabled=cgo_enabled,
            gui_app=gui_app,
            config=config,
            timeout=timeout,
        )
    finally:
        if cleanup:
            cleanup_artifacts(temp_dir)


def cleanup_artifacts(build_dir: str | Path) -> None:
    """Remove build artifacts and temporary files.
    
    Recursively removes the specified directory and its contents.
    Safe to call on non-existent directories.
    
    Args:
        build_dir: Path to the build directory to clean up.
    
    Example:
        >>> cleanup_artifacts("/tmp/sliver_compile_xyz")
    """
    build_dir = Path(build_dir)
    
    if not build_dir.exists():
        return
    
    try:
        shutil.rmtree(build_dir)
        logger.debug(f"Cleaned up build artifacts: {build_dir}")
    except OSError as e:
        logger.warning(f"Failed to clean up {build_dir}: {e}")


def verify_go_installation(config: dict | None = None) -> dict[str, str | bool]:
    """Verify Go installation and return version information.
    
    Args:
        config: Optional configuration dictionary.
    
    Returns:
        Dictionary with 'installed', 'path', 'version', and 'cross_compile' keys.
    
    Example:
        >>> info = verify_go_installation()
        >>> print(f"Go version: {info['version']}")
    """
    result = {
        "installed": False,
        "path": "",
        "version": "",
        "cross_compile": False,
    }
    
    try:
        go_path = get_compiler_path(config)
        result["path"] = go_path
        result["installed"] = True
        
        # Get version
        version_result = subprocess.run(
            [go_path, "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if version_result.returncode == 0:
            result["version"] = version_result.stdout.strip()
        
        # Test cross-compilation capability
        env_result = subprocess.run(
            [go_path, "env", "GOOS", "GOARCH"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        result["cross_compile"] = env_result.returncode == 0
        
    except (CompilerNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    
    return result


def get_supported_platforms() -> list[dict[str, str]]:
    """Get list of supported compilation targets.
    
    Returns:
        List of dictionaries with 'os' and 'arch' keys.
    """
    platforms = []
    for os_name in SUPPORTED_OS:
        for arch in SUPPORTED_ARCH:
            # Filter invalid combinations
            if os_name == "darwin" and arch == "386":
                continue  # macOS doesn't support 32-bit
            platforms.append({"os": os_name, "arch": arch})
    return platforms
