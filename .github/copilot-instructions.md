# Sliver C2 Payload Generator - AI Instructions

> Python-based generator creating obfuscated Go implants for Sliver C2 with AV/EDR evasion, persistence, and anti-forensics.

## Project Status

**Early skeleton phase** - Python modules contain only headers; Go templates have working code. See `PLAN.md` for implementation roadmap.

## Architecture Overview

```
generator.py          → CLI entry point (Click framework)
    ↓
lib/template_engine.py → Load Go templates, substitute {{VARIABLES}}
lib/obfuscator.py      → String encryption, identifier randomization
lib/evasion.py         → Inject AMSI/ETW bypass, syscall stubs
lib/persistence.py     → Registry/schtasks/WMI persistence code
lib/forensics_evasion.py → Anti-forensics snippets
    ↓
lib/compiler.py        → go build with cross-compilation flags
lib/packer.py          → PE section encryption, signing
    ↓
output/*.exe           → Final payload (gitignored)
```

**Data flow**: `config.yaml` + CLI args → template selection → variable injection → obfuscation → compilation → packing → signed binary

## Key Patterns

### Python Module Headers
Every `lib/*.py` file starts with: `# module_name module`

### Go Template Variables
Use `{{UPPER_SNAKE_CASE}}` placeholders in `templates/*.go`:
- `{{C2_URL}}`, `{{ENCRYPTION_KEY}}` - Config values
- `{{MAIN_FUNC}}`, `{{CONNECT_FUNC}}`, `{{EXECUTE_FUNC}}` - Randomized function names
- `{{EVASION_FUNCTIONS}}`, `{{PERSISTENCE_FUNCTIONS}}`, `{{FORENSICS_FUNCTIONS}}` - Injected code blocks
- `{{EVASION_IMPORTS}}` - Dynamic imports

### Evasion Code Style (Go)
Silent failures for evasion functions - don't alert defenders:
```go
func bypassAMSI() error {
    amsi, err := syscall.LoadDLL("amsi.dll")
    if err != nil {
        return err  // Silent failure, continue execution
    }
    // ...
}
```

### Windows API Pattern
```go
kernel32 := syscall.MustLoadDLL("kernel32.dll")
VirtualProtect := kernel32.MustFindProc("VirtualProtect")
VirtualProtect.Call(addr, uintptr(len(patch)), 0x40, uintptr(unsafe.Pointer(&oldProtect)))
```

## Configuration

All settings in `config.yaml` with nested structure:
- `compiler_paths.go`, `compiler_paths.mingw`
- `obfuscation.string_encryption` (aes256/xor), `identifier_length`, `junk_code_ratio`
- `evasion.syscalls` (direct/indirect/hybrid), `amsi_bypass`, `etw_bypass`
- `persistence.methods[]` (registry/schtasks/wmi/com_hijack)
- `signing.enabled` (MANDATORY for production payloads)

## Developer Workflow

```bash
# Setup
pip3 install -r requirements.txt
go version  # Requires Go 1.21+

# Run tests
pytest tests/

# Generate payload (once implemented)
python3 generator.py --target windows --arch x64 --c2 https://IP:443 --output payload.exe
```

## Code Style Summary

| Element | Convention |
|---------|------------|
| Python functions | `snake_case` with type hints |
| Python classes | `PascalCase` |
| Go templates | `gofmt` style |
| Template vars | `{{UPPER_SNAKE_CASE}}` |
| YAML | 2-space indent |
| Docstrings | Google-style |

## Security Rules

1. **Never hardcode secrets** - Use `{{TEMPLATE_VARS}}` for keys/URLs
2. **Reference MITRE ATT&CK** in evasion code comments (e.g., T1562.001)
3. **Silent failures** for all evasion functions
4. **No UPX** - Use custom packer in `lib/packer.py`

## File Reference

| File | Purpose |
|------|---------|
| `templates/implant_go_basic.go` | Simple HTTP(S) implant |
| `templates/implant_go_syscalls.go` | Advanced with AMSI/ETW bypass, sandbox detection |
| `snippets/*.go` | Reusable code blocks for injection |
| `PLAN.md` | Full implementation plan with all proposed files |
