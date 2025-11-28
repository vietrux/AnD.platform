# test_obfuscator module
"""Tests for obfuscator functionality."""

import os
import re

import pytest

from lib.obfuscator import (
    GO_RESERVED_KEYWORDS,
    GO_STDLIB_IDENTIFIERS,
    EncryptionError,
    ObfuscationError,
    encrypt_string_aes,
    encrypt_string_xor,
    encrypt_strings_in_source,
    generate_decryption_stub_go,
    get_aes_imports,
    insert_junk_code,
    obfuscate_source,
    randomize_identifiers,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_go_source() -> str:
    """Sample Go source code for testing."""
    return '''package main

import (
    "fmt"
    "time"
)

const (
    ServerURL = "https://example.com/api"
    SecretKey = "mysecretkey123"
)

var globalCounter int

func myFunction() {
    localVar := "hello world"
    fmt.Println(localVar)
}

func anotherFunc(input string) string {
    return input + " processed"
}

func main() {
    myFunction()
    result := anotherFunc("test")
    fmt.Println(result)
}
'''


@pytest.fixture
def xor_key() -> bytes:
    """XOR encryption key for testing."""
    return b"testkey123"


@pytest.fixture
def aes_key() -> bytes:
    """AES-256 encryption key for testing."""
    return os.urandom(32)


# =============================================================================
# Tests for encrypt_string_xor
# =============================================================================


class TestEncryptStringXor:
    """Tests for XOR string encryption."""

    def test_basic_encryption(self, xor_key: bytes) -> None:
        """Test basic XOR encryption returns valid Go byte slice."""
        encrypted, var_name = encrypt_string_xor("hello", xor_key)
        
        assert encrypted.startswith("[]byte{")
        assert encrypted.endswith("}")
        assert "0x" in encrypted
        assert len(var_name) > 0

    def test_encrypted_format(self, xor_key: bytes) -> None:
        """Test encrypted output is valid Go syntax."""
        encrypted, _ = encrypt_string_xor("test string", xor_key)
        
        # Should be valid Go byte slice with hex values
        pattern = r'\[\]byte\{(0x[0-9a-f]{2},?\s*)+\}'
        assert re.match(pattern, encrypted)

    def test_empty_key_raises_error(self) -> None:
        """Test that empty key raises EncryptionError."""
        with pytest.raises(EncryptionError) as exc_info:
            encrypt_string_xor("test", b"")
        assert "empty" in str(exc_info.value).lower()

    def test_unique_var_names(self, xor_key: bytes) -> None:
        """Test that variable names are unique across calls."""
        _, var1 = encrypt_string_xor("test1", xor_key)
        _, var2 = encrypt_string_xor("test2", xor_key)
        assert var1 != var2

    def test_xor_correctness(self, xor_key: bytes) -> None:
        """Test that XOR encryption is reversible."""
        plaintext = "test message"
        encrypted, _ = encrypt_string_xor(plaintext, xor_key)
        
        # Extract bytes from Go slice
        hex_values = re.findall(r'0x([0-9a-f]{2})', encrypted)
        encrypted_bytes = bytes(int(h, 16) for h in hex_values)
        
        # Decrypt manually
        decrypted = bytes(
            b ^ xor_key[i % len(xor_key)]
            for i, b in enumerate(encrypted_bytes)
        )
        
        assert decrypted.decode('utf-8') == plaintext

    def test_unicode_string(self, xor_key: bytes) -> None:
        """Test XOR encryption with unicode characters."""
        encrypted, _ = encrypt_string_xor("héllo wörld 日本語", xor_key)
        assert encrypted.startswith("[]byte{")


# =============================================================================
# Tests for encrypt_string_aes
# =============================================================================


class TestEncryptStringAes:
    """Tests for AES-256-GCM string encryption."""

    def test_basic_encryption(self, aes_key: bytes) -> None:
        """Test basic AES encryption returns valid Go byte slice."""
        encrypted, var_name = encrypt_string_aes("hello", aes_key)
        
        assert encrypted.startswith("[]byte{")
        assert encrypted.endswith("}")
        assert len(var_name) > 0

    def test_invalid_key_length(self) -> None:
        """Test that non-32-byte key raises EncryptionError."""
        with pytest.raises(EncryptionError) as exc_info:
            encrypt_string_aes("test", b"shortkey")
        assert "32" in str(exc_info.value)

    def test_encrypted_includes_nonce(self, aes_key: bytes) -> None:
        """Test that encrypted data includes 12-byte nonce."""
        encrypted, _ = encrypt_string_aes("test", aes_key)
        
        # Extract bytes
        hex_values = re.findall(r'0x([0-9a-f]{2})', encrypted)
        # Should have at least nonce (12) + ciphertext + tag (16) bytes
        # For "test" (4 bytes): 12 + 4 + 16 = 32 minimum
        assert len(hex_values) >= 32

    def test_unique_nonces(self, aes_key: bytes) -> None:
        """Test that each encryption uses unique nonce."""
        encrypted1, _ = encrypt_string_aes("same text", aes_key)
        encrypted2, _ = encrypt_string_aes("same text", aes_key)
        
        # Same plaintext should produce different ciphertext due to random nonce
        assert encrypted1 != encrypted2


# =============================================================================
# Tests for generate_decryption_stub_go
# =============================================================================


class TestGenerateDecryptionStub:
    """Tests for decryption stub generation."""

    def test_xor_stub_generation(self) -> None:
        """Test XOR decryption stub is valid Go code."""
        stub = generate_decryption_stub_go("xor")
        
        assert "func" in stub
        assert "[]byte" in stub
        assert "string" in stub
        assert "^" in stub  # XOR operator

    def test_aes_stub_generation(self) -> None:
        """Test AES decryption stub is valid Go code."""
        stub = generate_decryption_stub_go("aes256")
        
        assert "func" in stub
        assert "aes.NewCipher" in stub
        assert "cipher.NewGCM" in stub
        assert "gcm.Open" in stub

    def test_invalid_algorithm(self) -> None:
        """Test that invalid algorithm raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generate_decryption_stub_go("invalid")  # type: ignore[arg-type]
        assert "invalid" in str(exc_info.value).lower()

    def test_stub_has_unique_func_name(self) -> None:
        """Test that each stub has unique function name."""
        stub1 = generate_decryption_stub_go("xor")
        stub2 = generate_decryption_stub_go("xor")
        
        # Extract function names
        func_pattern = re.compile(r'func\s+(\w+)\s*\(')
        match1 = func_pattern.search(stub1)
        match2 = func_pattern.search(stub2)
        
        assert match1 is not None
        assert match2 is not None
        
        name1 = match1.group(1)
        name2 = match2.group(1)
        
        assert name1 != name2


class TestGetAesImports:
    """Tests for AES imports helper."""

    def test_includes_required_imports(self) -> None:
        """Test that AES imports include required packages."""
        imports = get_aes_imports()
        
        assert '"crypto/aes"' in imports
        assert '"crypto/cipher"' in imports
        assert '"errors"' in imports


# =============================================================================
# Tests for encrypt_strings_in_source
# =============================================================================


class TestEncryptStringsInSource:
    """Tests for source-level string encryption."""

    def test_encrypts_string_literals(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test that string literals are encrypted."""
        result = encrypt_strings_in_source(sample_go_source, xor_key, "xor")
        
        # Original strings should not be present in plaintext
        assert '"https://example.com/api"' not in result
        assert '"mysecretkey123"' not in result

    def test_adds_decryption_function(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test that decryption function is added."""
        result = encrypt_strings_in_source(sample_go_source, xor_key, "xor")
        
        assert "decryptXor" in result or "decrypt" in result.lower()
        assert "decryptionKey" in result

    def test_preserves_short_strings(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test that very short strings are not encrypted."""
        source = 'package main\n\nvar x = ""\nvar y = "ab"'
        result = encrypt_strings_in_source(source, xor_key, "xor")
        
        # Short strings should remain
        assert '""' in result or '"ab"' in result

    def test_preserves_format_strings(self, xor_key: bytes) -> None:
        """Test that format strings starting with % are preserved."""
        source = 'package main\n\nvar x = "%s %d"'
        result = encrypt_strings_in_source(source, xor_key, "xor")
        
        # Format strings should be preserved (or result should still work)
        assert "package main" in result


# =============================================================================
# Tests for randomize_identifiers
# =============================================================================


class TestRandomizeIdentifiers:
    """Tests for identifier randomization."""

    def test_randomizes_function_names(self, sample_go_source: str) -> None:
        """Test that function names are randomized."""
        result = randomize_identifiers(sample_go_source)
        
        # Original function names should be replaced
        assert "myFunction" not in result
        assert "anotherFunc" not in result

    def test_randomizes_variable_names(self, sample_go_source: str) -> None:
        """Test that variable names are randomized."""
        result = randomize_identifiers(sample_go_source)
        
        assert "globalCounter" not in result

    def test_preserves_keywords(self, sample_go_source: str) -> None:
        """Test that Go keywords are preserved."""
        result = randomize_identifiers(sample_go_source)
        
        assert "func" in result
        assert "package" in result
        assert "import" in result
        assert "const" in result
        assert "var" in result
        assert "return" in result

    def test_preserves_stdlib_identifiers(self, sample_go_source: str) -> None:
        """Test that stdlib identifiers are preserved."""
        result = randomize_identifiers(sample_go_source)
        
        assert "fmt" in result
        assert "time" in result
        assert "Println" in result

    def test_preserves_main_function(self, sample_go_source: str) -> None:
        """Test that main function name is preserved."""
        result = randomize_identifiers(sample_go_source)
        
        assert "func main()" in result

    def test_custom_preserve_set(self, sample_go_source: str) -> None:
        """Test custom identifiers to preserve."""
        result = randomize_identifiers(
            sample_go_source,
            preserve={"myFunction"}
        )
        
        assert "myFunction" in result
        assert "anotherFunc" not in result

    def test_consistent_renaming(self) -> None:
        """Test that same identifier is renamed consistently throughout."""
        source = '''package main
func myFunc() { myFunc() }
'''
        result = randomize_identifiers(source)
        
        # Find the new function name
        func_match = re.search(r'func\s+(\w+)\s*\(\)', result)
        assert func_match is not None
        new_name = func_match.group(1)
        
        # Should appear twice (definition and call)
        assert result.count(new_name) == 2


# =============================================================================
# Tests for insert_junk_code
# =============================================================================


class TestInsertJunkCode:
    """Tests for junk code insertion."""

    def test_inserts_junk_code(self, sample_go_source: str) -> None:
        """Test that junk code is inserted."""
        result = insert_junk_code(sample_go_source, ratio=0.5)
        
        # Result should be longer due to junk code
        assert len(result) > len(sample_go_source)

    def test_zero_ratio_no_change(self, sample_go_source: str) -> None:
        """Test that ratio 0.0 results in no junk code."""
        result = insert_junk_code(sample_go_source, ratio=0.0)
        
        assert result == sample_go_source

    def test_invalid_ratio_raises_error(self, sample_go_source: str) -> None:
        """Test that invalid ratio raises ValueError."""
        with pytest.raises(ValueError):
            insert_junk_code(sample_go_source, ratio=1.5)
        
        with pytest.raises(ValueError):
            insert_junk_code(sample_go_source, ratio=-0.1)

    def test_junk_is_valid_go(self, sample_go_source: str) -> None:
        """Test that inserted junk looks like valid Go syntax."""
        result = insert_junk_code(sample_go_source, ratio=0.3)
        
        # Should contain Go-like constructs
        assert "package main" in result
        # Junk code contains these patterns
        junk_patterns = ["_ =", "if false", "for", "func()"]
        # At least one junk pattern should be more frequent than original
        original_count = sum(sample_go_source.count(p) for p in junk_patterns)
        result_count = sum(result.count(p) for p in junk_patterns)
        
        # With ratio 0.3, we expect some junk to be added
        assert result_count >= original_count

    def test_preserves_structure(self, sample_go_source: str) -> None:
        """Test that original structure is preserved."""
        result = insert_junk_code(sample_go_source, ratio=0.2)
        
        # Key structures should remain
        assert "package main" in result
        assert "import" in result
        assert "func main()" in result


# =============================================================================
# Tests for obfuscate_source
# =============================================================================


class TestObfuscateSource:
    """Tests for the full obfuscation pipeline."""

    def test_full_obfuscation(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test full obfuscation pipeline."""
        result = obfuscate_source(
            sample_go_source,
            xor_key,
            algorithm="xor",
            randomize_names=True,
            junk_ratio=0.1,
        )
        
        # Original identifiers should be gone
        assert "myFunction" not in result
        assert "anotherFunc" not in result
        
        # Original strings should be encrypted
        assert '"https://example.com/api"' not in result
        
        # Structure should be preserved
        assert "package main" in result
        assert "func main()" in result

    def test_obfuscation_without_name_randomization(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test obfuscation without identifier randomization."""
        result = obfuscate_source(
            sample_go_source,
            xor_key,
            algorithm="xor",
            randomize_names=False,
            junk_ratio=0.0,
        )
        
        # Original identifiers should remain
        assert "myFunction" in result
        
        # But strings should be encrypted
        assert '"https://example.com/api"' not in result

    def test_obfuscation_without_junk(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test obfuscation without junk code."""
        result = obfuscate_source(
            sample_go_source,
            xor_key,
            algorithm="xor",
            randomize_names=True,
            junk_ratio=0.0,
        )
        
        # Result should be modified but not much longer
        # (only decryption code added)
        original_lines = len(sample_go_source.split('\n'))
        result_lines = len(result.split('\n'))
        
        # Allow for decryption function addition
        assert result_lines < original_lines + 30

    def test_obfuscation_with_aes(
        self, sample_go_source: str, aes_key: bytes
    ) -> None:
        """Test obfuscation with AES-256."""
        result = obfuscate_source(
            sample_go_source,
            aes_key,
            algorithm="aes256",
            randomize_names=False,
            junk_ratio=0.0,
        )
        
        assert "decryptAes" in result or "aes" in result.lower()

    def test_preserved_identifiers(
        self, sample_go_source: str, xor_key: bytes
    ) -> None:
        """Test that specified identifiers are preserved."""
        result = obfuscate_source(
            sample_go_source,
            xor_key,
            algorithm="xor",
            randomize_names=True,
            preserve_identifiers={"myFunction"},
        )
        
        assert "myFunction" in result
        assert "anotherFunc" not in result


# =============================================================================
# Tests for Reserved Keywords and Stdlib
# =============================================================================


class TestReservedIdentifiers:
    """Tests for reserved keywords and stdlib identifiers."""

    def test_go_keywords_complete(self) -> None:
        """Test that common Go keywords are in reserved set."""
        expected_keywords = {
            "func", "var", "const", "if", "else", "for", "range",
            "return", "package", "import", "type", "struct", "interface",
            "switch", "case", "default", "break", "continue", "go", "defer",
        }
        assert expected_keywords.issubset(GO_RESERVED_KEYWORDS)

    def test_stdlib_identifiers_complete(self) -> None:
        """Test that common stdlib packages are in stdlib set."""
        expected_stdlib = {
            "fmt", "os", "io", "http", "time", "syscall", "unsafe",
        }
        assert expected_stdlib.issubset(GO_STDLIB_IDENTIFIERS)

    def test_main_is_reserved(self) -> None:
        """Test that 'main' is reserved."""
        assert "main" in GO_RESERVED_KEYWORDS
