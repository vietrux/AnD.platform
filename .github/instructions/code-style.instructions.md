---
applyTo: '**'
---
# Code Style Guidelines - Sliver C2 Payload Generator

## Python Code Style (lib/*.py, generator.py, tests/)

### File Headers
Every Python module starts with a single-line header comment:
```python
# module_name module
```

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case` | `template_engine.py`, `forensics_evasion.py` |
| Classes | `PascalCase` | `PayloadGenerator`, `TemplateEngine` |
| Functions | `snake_case` | `generate_payload()`, `encrypt_strings()` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_KEY`, `C2_TIMEOUT` |
| Private | `_prefix` | `_parse_config()`, `_internal_state` |

### Type Hints
Required for all function signatures:
```python
def load_template(template_name: str, variables: dict[str, str]) -> str:
    """Load and render a Go template with variable substitution."""
    ...
```

### Docstrings
Use Google-style docstrings:
```python
def encrypt_strings(source: str, key: bytes, algorithm: str = "aes256") -> str:
    """Encrypt string literals in Go source code.
    
    Args:
        source: Go source code containing string literals.
        key: Encryption key (32 bytes for AES-256).
        algorithm: Encryption algorithm ('aes256' or 'xor').
        
    Returns:
        Modified source with encrypted strings and decryption stubs.
        
    Raises:
        ValueError: If key length doesn't match algorithm requirements.
    """
```

### Imports
Order: stdlib → third-party → local, alphabetically within groups:
```python
import os
import sys
from pathlib import Path

import click
import jinja2
import yaml

from lib.compiler import compile_payload
from lib.obfuscator import obfuscate_source
```

### Error Handling
Use specific exceptions, never bare `except:`:
```python
try:
    binary = compile_go_source(source_path)
except CompilationError as e:
    logger.error(f"Build failed: {e}")
    raise click.ClickException(str(e))
```

---

## Go Code Style (templates/*.go, snippets/*.go)

### Template Variables
Use `{{UPPER_SNAKE_CASE}}` placeholders:
```go
const (
    C2_URL         = "{{C2_URL}}"
    ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
)

func {{MAIN_FUNC}}() {
    {{EVASION_FUNCTIONS}}
    {{PERSISTENCE_FUNCTIONS}}
}
```

### Standard Template Variables
| Variable | Purpose |
|----------|---------|
| `{{C2_URL}}` | C2 server URL |
| `{{ENCRYPTION_KEY}}` | Payload encryption key |
| `{{MAIN_FUNC}}` | Randomized main function name |
| `{{CONNECT_FUNC}}` | Randomized C2 connection function |
| `{{EXECUTE_FUNC}}` | Randomized command execution function |
| `{{EVASION_IMPORTS}}` | Dynamic import block |
| `{{EVASION_FUNCTIONS}}` | Injected evasion code |
| `{{PERSISTENCE_FUNCTIONS}}` | Injected persistence code |
| `{{FORENSICS_FUNCTIONS}}` | Injected anti-forensics code |

### Import Organization
```go
import (
    // Standard library
    "crypto/tls"
    "fmt"
    "net/http"
    "time"

    // Syscall/unsafe
    "syscall"
    "unsafe"

    // Dynamic imports
    {{EVASION_IMPORTS}}
)
```

### Function Comments
Document every function with purpose and MITRE ATT&CK reference where applicable:
```go
// bypassAMSI patches AmsiScanBuffer to disable AMSI scanning.
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
func bypassAMSI() error {
    // ...
}
```

### Error Handling - Silent Failures
Evasion functions must fail silently (don't alert defenders):
```go
func bypassAMSI() error {
    amsi, err := syscall.LoadDLL("amsi.dll")
    if err != nil {
        return err  // Silent return, execution continues
    }
    defer amsi.Release()
    // ...
}
```

### Windows API Pattern
Standard pattern for Windows syscalls:
```go
kernel32 := syscall.MustLoadDLL("kernel32.dll")
VirtualProtect := kernel32.MustFindProc("VirtualProtect")

var oldProtect uint32
VirtualProtect.Call(
    addr,
    uintptr(len(patch)),
    0x40,  // PAGE_EXECUTE_READWRITE
    uintptr(unsafe.Pointer(&oldProtect)),
)
```

---

## YAML Configuration (config.yaml)

### Structure
- 2-space indentation
- Group related settings
- Comment non-obvious values

```yaml
# Compiler paths
compiler_paths:
  go: /usr/local/go/bin/go
  mingw: /usr/bin/x86_64-w64-mingw32-gcc

# Obfuscation settings
obfuscation:
  string_encryption: aes256  # aes256, xor
  identifier_length: 12
  junk_code_ratio: 0.2       # 0.0-1.0

# Evasion techniques
evasion:
  syscalls: indirect  # direct, indirect, hybrid
  amsi_bypass: true
  etw_bypass: true
```

### Booleans
Use lowercase `true`/`false`:
```yaml
signing:
  enabled: true
  generate_selfsigned: true
```

### Lists
Use YAML list syntax:
```yaml
persistence:
  methods:
    - registry
    - schtasks
    - wmi
```

---

## Security Rules

1. **Never hardcode secrets** - Use `{{TEMPLATE_VARS}}` for keys/URLs
2. **Silent failures** - Evasion code returns errors but doesn't panic/crash
3. **No UPX** - Use custom packer in `lib/packer.py`
4. **MITRE ATT&CK references** - Document technique IDs in evasion code
5. **Code signing mandatory** - `signing.enabled: true` for production

---

## Testing (tests/)

### File Naming
```
tests/
├── test_template_engine.py
├── test_obfuscator.py
├── test_compiler.py
└── conftest.py
```

### Test Function Naming
```python
def test_encrypt_strings_with_aes256():
    """Test AES-256 string encryption."""
    ...

def test_encrypt_strings_invalid_key_length():
    """Test error handling for invalid key length."""
    ...
```

### Test Organization
```python
import pytest
from lib.obfuscator import encrypt_strings


class TestStringEncryption:
    """Tests for string encryption functionality."""
    
    def test_basic_encryption(self):
        ...
    
    def test_key_validation(self):
        ...
```

---

## CLI Interface (Click)

Use Click decorators with short/long options:
```python
@click.command()
@click.option('--target', '-t', type=click.Choice(['windows', 'linux', 'macos']),
              required=True, help='Target OS')
@click.option('--arch', '-a', type=click.Choice(['x64', 'x86']),
              default='x64', help='Architecture')
@click.option('--c2', '-c', required=True, help='C2 URL (https://IP:PORT)')
@click.option('--output', '-O', type=click.Path(), required=True,
              help='Output file path')
def generate(target, arch, c2, output):
    """Generate obfuscated Sliver C2 payload."""
    ...
```

---

## Git Commits

Use conventional commit format:
```
feat(evasion): add indirect syscall support
fix(compiler): handle paths with spaces
docs(readme): update installation steps
refactor(obfuscator): extract string encryption
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`