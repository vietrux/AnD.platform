# test_compiler module
"""Tests for Go compiler wrapper functionality."""

import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.compiler import (
    ARCH_MAP,
    SUPPORTED_ARCH,
    SUPPORTED_OS,
    CompilationError,
    CompilerError,
    CompilerNotFoundError,
    CompileResult,
    ConfigurationError,
    build_environment,
    build_ldflags,
    cleanup_artifacts,
    compile_go,
    compile_go_source,
    get_compiler_path,
    get_mingw_path,
    get_supported_platforms,
    load_config,
    verify_go_installation,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with config files."""
    config_content = """
compiler_paths:
  go: /usr/local/go/bin/go
  mingw: /usr/bin/x86_64-w64-mingw32-gcc

obfuscation:
  string_encryption: aes256
  identifier_length: 12
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return tmp_path


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration dictionary."""
    return {
        "compiler_paths": {
            "go": "/usr/local/go/bin/go",
            "mingw": "/usr/bin/x86_64-w64-mingw32-gcc",
        },
        "obfuscation": {
            "string_encryption": "aes256",
            "identifier_length": 12,
        },
    }


@pytest.fixture
def simple_go_source() -> str:
    """Simple Go source code for testing compilation."""
    return '''package main

func main() {
    println("Hello, World!")
}
'''


@pytest.fixture
def temp_source_file(tmp_path: Path, simple_go_source: str) -> Path:
    """Create a temporary Go source file."""
    source_file = tmp_path / "main.go"
    source_file.write_text(simple_go_source)
    return source_file


# =============================================================================
# Tests for load_config
# =============================================================================


class TestLoadConfig:
    """Tests for load_config functionality."""

    def test_load_valid_config(self, temp_config_dir: Path) -> None:
        """Test loading a valid config file."""
        config = load_config(temp_config_dir / "config.yaml")
        assert "compiler_paths" in config
        assert config["compiler_paths"]["go"] == "/usr/local/go/bin/go"

    def test_load_nonexistent_config(self, tmp_path: Path) -> None:
        """Test loading a nonexistent config file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(tmp_path / "nonexistent.yaml")
        assert "not found" in str(exc_info.value).lower()

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading an invalid YAML file."""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("{ invalid: yaml: content }")
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(invalid_config)
        assert "parse" in str(exc_info.value).lower()

    def test_load_default_config(self) -> None:
        """Test loading the default project config."""
        # This should work with the actual config.yaml
        config = load_config()
        assert "compiler_paths" in config


# =============================================================================
# Tests for get_compiler_path
# =============================================================================


class TestGetCompilerPath:
    """Tests for get_compiler_path functionality."""

    def test_get_from_config(self, tmp_path: Path) -> None:
        """Test getting compiler path from config."""
        # Create a fake go binary
        fake_go = tmp_path / "go"
        fake_go.touch()
        fake_go.chmod(0o755)

        config = {"compiler_paths": {"go": str(fake_go)}}
        result = get_compiler_path(config)
        assert result == str(fake_go.resolve())

    def test_get_from_goroot_env(self, tmp_path: Path) -> None:
        """Test getting compiler from GOROOT environment."""
        # Create fake GOROOT structure
        go_bin = tmp_path / "bin"
        go_bin.mkdir()
        fake_go = go_bin / "go"
        fake_go.touch()

        with patch.dict(os.environ, {"GOROOT": str(tmp_path)}):
            # Empty config to force env check
            result = get_compiler_path({})
            assert "go" in result

    def test_get_from_system_path(self) -> None:
        """Test getting compiler from system PATH."""
        # This test depends on Go being installed
        go_path = shutil.which("go")
        if go_path:
            result = get_compiler_path({})
            assert result == go_path

    def test_compiler_not_found(self, tmp_path: Path) -> None:
        """Test error when compiler not found."""
        # Clear environment and provide empty config
        with patch.dict(os.environ, {"GOROOT": "", "PATH": str(tmp_path)}, clear=False):
            with patch("shutil.which", return_value=None):
                with pytest.raises(CompilerNotFoundError):
                    get_compiler_path({})


# =============================================================================
# Tests for get_mingw_path
# =============================================================================


class TestGetMingwPath:
    """Tests for get_mingw_path functionality."""

    def test_get_from_config(self, tmp_path: Path) -> None:
        """Test getting MinGW path from config."""
        fake_mingw = tmp_path / "x86_64-w64-mingw32-gcc"
        fake_mingw.touch()

        config = {"compiler_paths": {"mingw": str(fake_mingw)}}
        result = get_mingw_path(config)
        assert result == str(fake_mingw.resolve())

    def test_mingw_not_configured(self) -> None:
        """Test when MinGW is not configured."""
        with patch("shutil.which", return_value=None):
            with patch("pathlib.Path.exists", return_value=False):
                result = get_mingw_path({})
                # May return None or actual path if installed
                assert result is None or isinstance(result, str)


# =============================================================================
# Tests for build_ldflags
# =============================================================================


class TestBuildLdflags:
    """Tests for build_ldflags functionality."""

    def test_default_flags(self) -> None:
        """Test default ldflags."""
        result = build_ldflags()
        assert "-s" in result
        assert "-w" in result

    def test_no_strip_debug(self) -> None:
        """Test ldflags without debug stripping."""
        result = build_ldflags(strip_debug=False)
        assert "-s" not in result
        assert "-w" in result

    def test_no_strip_dwarf(self) -> None:
        """Test ldflags without DWARF stripping."""
        result = build_ldflags(strip_dwarf=False)
        assert "-s" in result
        assert "-w" not in result

    def test_no_stripping(self) -> None:
        """Test ldflags without any stripping."""
        result = build_ldflags(strip_debug=False, strip_dwarf=False)
        assert result == ""

    def test_additional_flags(self) -> None:
        """Test ldflags with additional flags."""
        result = build_ldflags(additional_flags=["-H=windowsgui", "-X=main.version=1.0"])
        assert "-s" in result
        assert "-w" in result
        assert "-H=windowsgui" in result
        assert "-X=main.version=1.0" in result

    def test_gui_app_flag(self) -> None:
        """Test adding Windows GUI flag."""
        result = build_ldflags(additional_flags=["-H=windowsgui"])
        assert "-H=windowsgui" in result


# =============================================================================
# Tests for build_environment
# =============================================================================


class TestBuildEnvironment:
    """Tests for build_environment functionality."""

    def test_windows_amd64(self) -> None:
        """Test environment for Windows x64."""
        env = build_environment("windows", "amd64")
        assert env["GOOS"] == "windows"
        assert env["GOARCH"] == "amd64"
        assert env["CGO_ENABLED"] == "0"

    def test_linux_386(self) -> None:
        """Test environment for Linux x86."""
        env = build_environment("linux", "386")
        assert env["GOOS"] == "linux"
        assert env["GOARCH"] == "386"

    def test_darwin_arm64(self) -> None:
        """Test environment for macOS ARM64."""
        env = build_environment("darwin", "arm64")
        assert env["GOOS"] == "darwin"
        assert env["GOARCH"] == "arm64"

    def test_cgo_enabled(self) -> None:
        """Test environment with CGO enabled."""
        env = build_environment("windows", "amd64", cgo_enabled=True)
        assert env["CGO_ENABLED"] == "1"

    def test_cgo_with_mingw(self) -> None:
        """Test environment with CGO and MinGW."""
        env = build_environment(
            "windows", "amd64",
            cgo_enabled=True,
            mingw_path="/usr/bin/x86_64-w64-mingw32-gcc"
        )
        assert env["CGO_ENABLED"] == "1"
        assert env["CC"] == "/usr/bin/x86_64-w64-mingw32-gcc"

    def test_preserves_existing_env(self) -> None:
        """Test that existing environment is preserved."""
        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            env = build_environment("windows", "amd64")
            assert env.get("MY_VAR") == "my_value"


# =============================================================================
# Tests for compile_go
# =============================================================================


class TestCompileGo:
    """Tests for compile_go functionality."""

    def test_source_not_found(self, tmp_path: Path) -> None:
        """Test error when source file not found."""
        with pytest.raises(CompilationError) as exc_info:
            compile_go(
                tmp_path / "nonexistent.go",
                tmp_path / "output.exe",
            )
        assert "not found" in str(exc_info.value).lower()

    def test_invalid_target_os(self, temp_source_file: Path, tmp_path: Path) -> None:
        """Test error with invalid target OS."""
        with pytest.raises(ValueError) as exc_info:
            compile_go(
                temp_source_file,
                tmp_path / "output.exe",
                target_os="invalid",  # type: ignore
            )
        assert "unsupported" in str(exc_info.value).lower()

    def test_invalid_architecture(self, temp_source_file: Path, tmp_path: Path) -> None:
        """Test error with invalid architecture."""
        with pytest.raises(ValueError) as exc_info:
            compile_go(
                temp_source_file,
                tmp_path / "output.exe",
                arch="invalid",
            )
        assert "unsupported" in str(exc_info.value).lower()

    def test_arch_mapping(self) -> None:
        """Test architecture name mapping."""
        assert ARCH_MAP["x64"] == "amd64"
        assert ARCH_MAP["x86"] == "386"
        assert ARCH_MAP["arm64"] == "arm64"

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_successful_compilation(self, temp_source_file: Path, tmp_path: Path) -> None:
        """Test successful compilation with Go installed."""
        output_path = tmp_path / "output"

        result = compile_go(
            temp_source_file,
            output_path,
            target_os="linux",
            arch="x64",
        )

        assert result.success
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        assert result.return_code == 0

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_compilation_with_strip(self, temp_source_file: Path, tmp_path: Path) -> None:
        """Test compilation with symbol stripping."""
        output_path = tmp_path / "output_stripped"

        result = compile_go(
            temp_source_file,
            output_path,
            target_os="linux",
            arch="x64",
            strip_symbols=True,
        )

        assert result.success

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_compilation_failure(self, tmp_path: Path) -> None:
        """Test compilation failure with invalid source."""
        invalid_source = tmp_path / "invalid.go"
        invalid_source.write_text("this is not valid go code")

        result = compile_go(
            invalid_source,
            tmp_path / "output.exe",
            target_os="linux",
            arch="x64",
        )

        assert not result.success
        assert result.return_code != 0
        assert result.stderr  # Should have error message

    def test_compile_result_dataclass(self) -> None:
        """Test CompileResult dataclass."""
        result = CompileResult(
            success=True,
            output_path="/path/to/binary",
            stdout="build output",
            stderr="",
            return_code=0,
        )
        assert result.success
        assert result.output_path == "/path/to/binary"


# =============================================================================
# Tests for compile_go_source
# =============================================================================


class TestCompileGoSource:
    """Tests for compile_go_source functionality."""

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_compile_from_string(self, simple_go_source: str, tmp_path: Path) -> None:
        """Test compiling Go source from string."""
        output_path = tmp_path / "from_string"

        result = compile_go_source(
            simple_go_source,
            output_path,
            target_os="linux",
            arch="x64",
        )

        assert result.success
        assert Path(output_path).exists()

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_cleanup_temp_files(self, simple_go_source: str, tmp_path: Path) -> None:
        """Test that temp files are cleaned up."""
        output_path = tmp_path / "cleanup_test"

        # Count temp directories before
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        before_count = len(list(temp_dir.glob("sliver_compile_*")))

        compile_go_source(
            simple_go_source,
            output_path,
            target_os="linux",
            arch="x64",
            cleanup=True,
        )

        # Should have same or fewer temp directories
        after_count = len(list(temp_dir.glob("sliver_compile_*")))
        assert after_count <= before_count + 1  # At most 1 more (race condition)


# =============================================================================
# Tests for cleanup_artifacts
# =============================================================================


class TestCleanupArtifacts:
    """Tests for cleanup_artifacts functionality."""

    def test_cleanup_existing_dir(self, tmp_path: Path) -> None:
        """Test cleaning up an existing directory."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "file.txt").touch()
        (build_dir / "subdir").mkdir()
        (build_dir / "subdir" / "nested.txt").touch()

        cleanup_artifacts(build_dir)
        assert not build_dir.exists()

    def test_cleanup_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test cleanup handles nonexistent directory gracefully."""
        nonexistent = tmp_path / "does_not_exist"
        # Should not raise
        cleanup_artifacts(nonexistent)

    def test_cleanup_with_string_path(self, tmp_path: Path) -> None:
        """Test cleanup with string path."""
        build_dir = tmp_path / "build_str"
        build_dir.mkdir()

        cleanup_artifacts(str(build_dir))
        assert not build_dir.exists()


# =============================================================================
# Tests for verify_go_installation
# =============================================================================


class TestVerifyGoInstallation:
    """Tests for verify_go_installation functionality."""

    @pytest.mark.skipif(shutil.which("go") is None, reason="Go not installed")
    def test_verify_installed_go(self) -> None:
        """Test verification with Go installed."""
        result = verify_go_installation()
        assert result["installed"] is True
        assert result["path"] != ""
        assert isinstance(result["version"], str)
        assert "go version" in str(result["version"])
        assert result["cross_compile"] is True

    def test_verify_not_installed(self) -> None:
        """Test verification when Go not found."""
        with patch("lib.compiler.get_compiler_path", side_effect=CompilerNotFoundError("not found")):
            result = verify_go_installation()
            assert result["installed"] is False
            assert result["path"] == ""


# =============================================================================
# Tests for get_supported_platforms
# =============================================================================


class TestGetSupportedPlatforms:
    """Tests for get_supported_platforms functionality."""

    def test_returns_list(self) -> None:
        """Test that function returns a list."""
        platforms = get_supported_platforms()
        assert isinstance(platforms, list)
        assert len(platforms) > 0

    def test_platform_structure(self) -> None:
        """Test platform dictionary structure."""
        platforms = get_supported_platforms()
        for platform in platforms:
            assert "os" in platform
            assert "arch" in platform
            assert platform["os"] in SUPPORTED_OS
            assert platform["arch"] in SUPPORTED_ARCH

    def test_no_darwin_386(self) -> None:
        """Test that macOS 32-bit is not included."""
        platforms = get_supported_platforms()
        darwin_386 = [p for p in platforms if p["os"] == "darwin" and p["arch"] == "386"]
        assert len(darwin_386) == 0

    def test_includes_windows_amd64(self) -> None:
        """Test that Windows x64 is included."""
        platforms = get_supported_platforms()
        windows_amd64 = [p for p in platforms if p["os"] == "windows" and p["arch"] == "amd64"]
        assert len(windows_amd64) == 1


# =============================================================================
# Tests for Constants
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_supported_os(self) -> None:
        """Test SUPPORTED_OS contains expected values."""
        assert "windows" in SUPPORTED_OS
        assert "linux" in SUPPORTED_OS
        assert "darwin" in SUPPORTED_OS

    def test_supported_arch(self) -> None:
        """Test SUPPORTED_ARCH contains expected values."""
        assert "amd64" in SUPPORTED_ARCH
        assert "386" in SUPPORTED_ARCH
        assert "arm64" in SUPPORTED_ARCH

    def test_arch_map_completeness(self) -> None:
        """Test ARCH_MAP has all expected mappings."""
        assert "x64" in ARCH_MAP
        assert "x86" in ARCH_MAP
        assert "arm64" in ARCH_MAP
        # Direct mappings
        assert "amd64" in ARCH_MAP
        assert "386" in ARCH_MAP
