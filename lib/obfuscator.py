# obfuscator module
"""Obfuscation module for Go source code transformation.

This module provides functionality for obfuscating Go source code through:
- String literal encryption (XOR and AES-256-GCM)
- Identifier randomization (function/variable renaming)
- Junk code insertion (dead code blocks)

All transformations maintain valid Go syntax and compile correctly.
"""

import base64
import os
import re
import secrets
import string
from typing import Literal


# Regex patterns for Go source analysis
GO_STRING_LITERAL_PATTERN = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
GO_FUNC_PATTERN = re.compile(r'\bfunc\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
GO_VAR_PATTERN = re.compile(r'\b(?:var|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+')

# Reserved Go keywords that should never be renamed
GO_RESERVED_KEYWORDS = frozenset({
    "break", "case", "chan", "const", "continue", "default", "defer", "else",
    "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
    "map", "package", "range", "return", "select", "struct", "switch", "type",
    "var", "true", "false", "nil", "iota", "append", "cap", "close", "complex",
    "copy", "delete", "imag", "len", "make", "new", "panic", "print", "println",
    "real", "recover", "string", "int", "int8", "int16", "int32", "int64",
    "uint", "uint8", "uint16", "uint32", "uint64", "uintptr", "float32",
    "float64", "complex64", "complex128", "byte", "rune", "bool", "error",
    "main",  # main function should not be renamed directly
})

# Standard library identifiers that should not be renamed
GO_STDLIB_IDENTIFIERS = frozenset({
    "fmt", "os", "io", "http", "tls", "time", "exec", "runtime", "syscall",
    "unsafe", "strings", "bytes", "encoding", "crypto", "net", "ioutil",
    "context", "sync", "errors", "log", "path", "filepath", "regexp",
})


class ObfuscationError(Exception):
    """Base exception for obfuscation errors."""
    pass


class EncryptionError(ObfuscationError):
    """Raised when string encryption fails."""
    pass


def encrypt_string_xor(plaintext: str, key: bytes) -> tuple[str, str]:
    """Encrypt a string using XOR cipher for Go code embedding.
    
    Args:
        plaintext: The string to encrypt.
        key: Encryption key (any length, will be cycled).
    
    Returns:
        Tuple of (Go byte slice literal, variable name for decrypted result).
        The byte slice contains the XOR-encrypted bytes as hex values.
    
    Raises:
        EncryptionError: If key is empty or encryption fails.
    
    Example:
        >>> encrypted, var_name = encrypt_string_xor("secret", b"key123")
        >>> print(encrypted)  # Go byte slice like []byte{0x1a, 0x0b, ...}
    """
    if not key:
        raise EncryptionError("Encryption key cannot be empty")
    
    # XOR encrypt the plaintext
    plaintext_bytes = plaintext.encode('utf-8')
    encrypted_bytes = bytes(
        b ^ key[i % len(key)] for i, b in enumerate(plaintext_bytes)
    )
    
    # Format as Go byte slice literal
    hex_values = ", ".join(f"0x{b:02x}" for b in encrypted_bytes)
    go_byte_slice = f"[]byte{{{hex_values}}}"
    
    # Generate unique variable name
    var_name = _generate_var_name()
    
    return go_byte_slice, var_name


def encrypt_string_aes(plaintext: str, key: bytes) -> tuple[str, str]:
    """Encrypt a string using AES-256-GCM for Go code embedding.
    
    Uses AES-256 in GCM mode for authenticated encryption.
    The nonce is prepended to the ciphertext.
    
    Args:
        plaintext: The string to encrypt.
        key: 32-byte encryption key for AES-256.
    
    Returns:
        Tuple of (Go byte slice literal with nonce+ciphertext, variable name).
    
    Raises:
        EncryptionError: If key is not 32 bytes or encryption fails.
    
    Example:
        >>> key = os.urandom(32)
        >>> encrypted, var_name = encrypt_string_aes("secret", key)
    """
    if len(key) != 32:
        raise EncryptionError(f"AES-256 requires 32-byte key, got {len(key)}")
    
    try:
        from Crypto.Cipher import AES
    except ImportError:
        raise EncryptionError(
            "pycryptodome package required for AES encryption. "
            "Install with: pip install pycryptodome"
        )
    
    # Generate random 12-byte nonce
    nonce = os.urandom(12)
    
    # Encrypt using AES-GCM
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)
    
    # Prepend nonce and append tag to ciphertext
    encrypted_data = nonce + ciphertext + tag
    
    # Format as Go byte slice literal
    hex_values = ", ".join(f"0x{b:02x}" for b in encrypted_data)
    go_byte_slice = f"[]byte{{{hex_values}}}"
    
    var_name = _generate_var_name()
    
    return go_byte_slice, var_name


def generate_decryption_stub_go(
    algorithm: Literal["xor", "aes256"],
    key_var: str = "decryptionKey",
) -> str:
    """Generate Go code for runtime string decryption.
    
    Creates a decryption function that can be embedded in the payload
    to decrypt strings at runtime.
    
    Args:
        algorithm: Encryption algorithm ("xor" or "aes256").
        key_var: Name of the variable holding the decryption key.
    
    Returns:
        Go source code for the decryption function.
    
    Raises:
        ValueError: If algorithm is not supported.
    """
    if algorithm == "xor":
        return _generate_xor_decrypt_stub(key_var)
    elif algorithm == "aes256":
        return _generate_aes_decrypt_stub(key_var)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def _generate_xor_decrypt_stub(key_var: str) -> str:
    """Generate XOR decryption function for Go."""
    func_name = _generate_func_name()
    return f'''
// {func_name} decrypts XOR-encrypted data at runtime
func {func_name}(encrypted []byte, key []byte) string {{
    decrypted := make([]byte, len(encrypted))
    for i := 0; i < len(encrypted); i++ {{
        decrypted[i] = encrypted[i] ^ key[i % len(key)]
    }}
    return string(decrypted)
}}
'''


def _generate_aes_decrypt_stub(key_var: str) -> str:
    """Generate AES-256-GCM decryption function for Go."""
    func_name = _generate_func_name()
    return f'''
// {func_name} decrypts AES-256-GCM encrypted data at runtime
// First 12 bytes are the nonce, remainder is ciphertext+tag
func {func_name}(encrypted []byte, key []byte) (string, error) {{
    block, err := aes.NewCipher(key)
    if err != nil {{
        return "", err
    }}
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {{
        return "", err
    }}
    
    nonceSize := gcm.NonceSize()
    if len(encrypted) < nonceSize {{
        return "", errors.New("ciphertext too short")
    }}
    
    nonce, ciphertext := encrypted[:nonceSize], encrypted[nonceSize:]
    plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {{
        return "", err
    }}
    
    return string(plaintext), nil
}}
'''


def get_aes_imports() -> str:
    """Return required imports for AES decryption in Go."""
    return '''
    "crypto/aes"
    "crypto/cipher"
    "errors"
'''


def encrypt_strings_in_source(
    source: str,
    key: bytes,
    algorithm: Literal["xor", "aes256"] = "xor",
    exclude_patterns: list[str] | None = None,
) -> str:
    """Encrypt all string literals in Go source code.
    
    Finds string literals in the source, encrypts them, and replaces
    them with decryption calls.
    
    Args:
        source: Go source code.
        key: Encryption key.
        algorithm: Encryption algorithm to use.
        exclude_patterns: List of regex patterns for strings to exclude.
    
    Returns:
        Modified source with encrypted strings and decryption code.
    """
    if exclude_patterns is None:
        exclude_patterns = [
            r'^$',  # Empty strings
            r'^\\n$',  # Single newline
            r'^%',  # Format strings
            r'^[0-9]+$',  # Numeric strings
        ]
    
    exclude_compiled = [re.compile(p) for p in exclude_patterns]
    
    # Track encrypted strings to avoid duplicates
    encrypted_strings: dict[str, tuple[str, str]] = {}
    decryption_func_added = False
    
    def should_encrypt(s: str) -> bool:
        """Check if string should be encrypted."""
        if len(s) < 3:  # Skip very short strings
            return False
        for pattern in exclude_compiled:
            if pattern.match(s):
                return False
        return True
    
    def replace_string(match: re.Match) -> str:
        nonlocal decryption_func_added
        original = match.group(1)
        
        if not should_encrypt(original):
            return match.group(0)
        
        # Check if already encrypted
        if original in encrypted_strings:
            byte_slice, var_name = encrypted_strings[original]
        else:
            if algorithm == "xor":
                byte_slice, var_name = encrypt_string_xor(original, key)
            else:
                byte_slice, var_name = encrypt_string_aes(original, key)
            encrypted_strings[original] = (byte_slice, var_name)
        
        # Return decryption call
        if algorithm == "xor":
            return f'decryptXor({byte_slice}, decryptionKey)'
        else:
            return f'decryptAes({byte_slice}, decryptionKey)'
    
    # Replace strings in source
    modified_source = GO_STRING_LITERAL_PATTERN.sub(replace_string, source)
    
    # Add decryption function if strings were encrypted
    if encrypted_strings:
        key_hex = ", ".join(f"0x{b:02x}" for b in key)
        key_decl = f"\nvar decryptionKey = []byte{{{key_hex}}}\n"
        decrypt_stub = generate_decryption_stub_go(algorithm)
        
        # Insert after package declaration
        package_end = modified_source.find('\n', modified_source.find('package'))
        if package_end != -1:
            modified_source = (
                modified_source[:package_end + 1] +
                key_decl +
                decrypt_stub +
                modified_source[package_end + 1:]
            )
    
    return modified_source


def randomize_identifiers(
    source: str,
    identifier_length: int = 12,
    preserve: set[str] | None = None,
) -> str:
    """Randomize function and variable names in Go source code.
    
    Replaces user-defined identifiers with random names while preserving
    Go keywords, standard library references, and specified identifiers.
    
    Args:
        source: Go source code.
        identifier_length: Length of generated random identifiers.
        preserve: Additional identifiers to preserve (not rename).
    
    Returns:
        Source code with randomized identifiers.
    """
    preserved = GO_RESERVED_KEYWORDS | GO_STDLIB_IDENTIFIERS
    if preserve:
        preserved = preserved | preserve
    
    # Find all user-defined identifiers
    func_matches = GO_FUNC_PATTERN.findall(source)
    var_matches = GO_VAR_PATTERN.findall(source)
    
    all_identifiers = set(func_matches + var_matches)
    identifiers_to_rename = all_identifiers - preserved
    
    # Generate mapping of old -> new names
    rename_map: dict[str, str] = {}
    used_names: set[str] = set()
    
    for identifier in identifiers_to_rename:
        new_name = _generate_unique_identifier(identifier_length, used_names)
        rename_map[identifier] = new_name
        used_names.add(new_name)
    
    # Apply renaming
    modified_source = source
    for old_name, new_name in rename_map.items():
        # Use word boundary matching to avoid partial replacements
        pattern = re.compile(rf'\b{re.escape(old_name)}\b')
        modified_source = pattern.sub(new_name, modified_source)
    
    return modified_source


def insert_junk_code(source: str, ratio: float = 0.2) -> str:
    """Insert junk (dead) code into Go source to increase entropy.
    
    Adds non-functional code blocks that will be optimized away by
    the compiler but make static analysis more difficult.
    
    Args:
        source: Go source code.
        ratio: Ratio of junk code to add (0.0 to 1.0).
               0.2 = add junk after ~20% of statements.
    
    Returns:
        Source code with junk code inserted.
    """
    if not 0.0 <= ratio <= 1.0:
        raise ValueError("Junk code ratio must be between 0.0 and 1.0")
    
    if ratio == 0.0:
        return source
    
    junk_snippets = _get_junk_code_snippets()
    
    # Find positions after statements (lines ending with ; or {)
    lines = source.split('\n')
    modified_lines = []
    
    for line in lines:
        modified_lines.append(line)
        
        # Skip empty lines, comments, and imports
        stripped = line.strip()
        if (not stripped or 
            stripped.startswith('//') or 
            stripped.startswith('import') or
            stripped.startswith('package')):
            continue
        
        # Add junk code based on ratio
        if secrets.randbelow(100) < int(ratio * 100):
            junk = secrets.choice(junk_snippets)
            # Indent junk code to match context
            indent = len(line) - len(line.lstrip())
            indented_junk = ' ' * indent + junk
            modified_lines.append(indented_junk)
    
    return '\n'.join(modified_lines)


def _get_junk_code_snippets() -> list[str]:
    """Return a list of junk code snippets for Go."""
    # These snippets do nothing but look like real code
    # They will be optimized away by the compiler
    var1 = _generate_var_name()
    var2 = _generate_var_name()
    var3 = _generate_var_name()
    
    return [
        f'_ = func() int {{ {var1} := 0; for i := 0; i < 0; i++ {{ {var1}++ }}; return {var1} }}()',
        f'if false {{ _ = {var2} }}',
        f'var {var3} = []byte{{}}; _ = len({var3})',
        f'_ = func() {{ }}',
        f'for {var1} := 0; {var1} < 0; {var1}++ {{ }}',
        f'switch {{ default: _ = 0 }}',
        f'_ = func() bool {{ return false && true }}()',
        f'{{ {var1} := 0; _ = {var1} }}',
    ]


def _generate_var_name(length: int = 8) -> str:
    """Generate a random variable name."""
    first = secrets.choice(string.ascii_lowercase)
    rest = ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                   for _ in range(length - 1))
    return first + rest


def _generate_func_name(length: int = 10) -> str:
    """Generate a random function name."""
    first = secrets.choice(string.ascii_lowercase)
    rest = ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                   for _ in range(length - 1))
    return first + rest


def _generate_unique_identifier(length: int, existing: set[str]) -> str:
    """Generate a unique random identifier not in existing set."""
    max_attempts = 1000
    for _ in range(max_attempts):
        identifier = _generate_var_name(length)
        if identifier not in existing and identifier not in GO_RESERVED_KEYWORDS:
            return identifier
    raise ObfuscationError(f"Could not generate unique identifier after {max_attempts} attempts")


def obfuscate_source(
    source: str,
    key: bytes,
    algorithm: Literal["xor", "aes256"] = "xor",
    randomize_names: bool = True,
    junk_ratio: float = 0.2,
    identifier_length: int = 12,
    preserve_identifiers: set[str] | None = None,
) -> str:
    """Apply full obfuscation pipeline to Go source code.
    
    This is the main entry point for obfuscation, combining:
    1. String literal encryption
    2. Identifier randomization
    3. Junk code insertion
    
    Args:
        source: Go source code to obfuscate.
        key: Encryption key for string encryption.
        algorithm: Encryption algorithm ("xor" or "aes256").
        randomize_names: Whether to randomize identifiers.
        junk_ratio: Ratio of junk code to add (0.0-1.0).
        identifier_length: Length of randomized identifiers.
        preserve_identifiers: Set of identifiers to preserve.
    
    Returns:
        Fully obfuscated Go source code.
    
    Example:
        >>> key = os.urandom(16)
        >>> obfuscated = obfuscate_source(source, key, algorithm="xor")
    """
    # Apply transformations in order
    result = source
    
    # 1. Randomize identifiers first (before string encryption adds new ones)
    if randomize_names:
        result = randomize_identifiers(
            result,
            identifier_length=identifier_length,
            preserve=preserve_identifiers,
        )
    
    # 2. Encrypt string literals
    result = encrypt_strings_in_source(result, key, algorithm)
    
    # 3. Insert junk code last
    if junk_ratio > 0:
        result = insert_junk_code(result, junk_ratio)
    
    return result
