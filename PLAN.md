# Custom Sliver C2 Payload Generator

A Python-based tool that generates custom, obfuscated malware payloads compatible with Sliver C2 infrastructure. Creates implants from scratch with advanced AV/EDR evasion techniques.

> [!CAUTION]
> **Legal and Ethical Use Only**
> This tool creates malicious payloads for authorized penetration testing only. Unauthorized use is illegal.

## User Requirements - CONFIRMED ✓

**Implant Language**: Go (cross-platform, easier syscalls, compatible with Sliver C2)

**Target Platform**: Windows (primary focus)

**Evasion Strategy**: Comprehensive approach
- Static AV evasion (signature bypass)
- Dynamic/behavioral evasion (EDR bypass)
- **Persistence** (multiple techniques for maintaining access)
- **Forensics evasion** (anti-forensics, log manipulation)

> [!IMPORTANT]
> **Enhanced Focus Areas**
> 
> 1. **AV/EDR Bypass**: Direct/indirect syscalls, AMSI/ETW patching, userland hook bypass
> 2. **Persistence**: Registry, scheduled tasks, WMI, COM hijacking, DLL proxying
> 3. **Forensics Evasion**: Event log clearing, timestamp stomping, prefetch manipulation, memory-only execution

## Proposed Changes

### Core Generator (Python)

#### [NEW] [generator.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/generator.py)
Main CLI tool for payload generation
- Argument parsing for payload configuration
- Template selection and variable injection
- Orchestrates obfuscation pipeline
- Triggers compilation process
- Output: compiled payload binary

**Features**:
```python
# Usage example
python generator.py \
  --target windows \
  --arch x64 \
  --c2 https://192.168.1.100:443 \
  --obfuscation high \
  --evasion syscalls,amsi-bypass \
  --persistence registry,schtasks \
  --output payload.exe
```

#### [NEW] [lib/template_engine.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/template_engine.py)
Template management and code generation
- Load implant templates (Go/C source code)
- Variable substitution (C2 address, ports, keys)
- Random function/variable name generation
- Junk code insertion

#### [NEW] [lib/obfuscator.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/obfuscator.py)
Source code obfuscation engine
- String encryption (XOR, AES, custom algorithms)
- Control flow flattening
- Dead code insertion
- Identifier randomization
- Function call indirection

#### [NEW] [lib/compiler.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/compiler.py)
Automated compilation wrapper
- Go compiler integration (`go build` with custom flags)
- C/C++ compiler support (MinGW, gcc)
- Strip symbols and debug info
- Linker flag customization
- Build artifact cleanup

#### [NEW] [lib/packer.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/packer.py)
Post-compilation binary packing
- Custom PE packer implementation (no UPX)
- PE section encryption/compression
- Custom loader stub generation
- Entropy manipulation
- Certificate signing (MANDATORY - code signing with self-signed/stolen certs)

#### [NEW] [lib/evasion.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/evasion.py)
AV/EDR evasion technique library
- Syscall stub generation (direct/indirect)
- AMSI/ETW patching code templates
- Sandbox detection routines
- Anti-debugging checks
- Sleep obfuscation patterns

---

### Implant Templates

#### [NEW] [templates/implant_go_basic.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/templates/implant_go_basic.go)
Basic Go implant template
- HTTP/HTTPS C2 communication
- Command execution functionality
- Basic encryption (AES-GCM)
- Configurable variables: `{{C2_ADDRESS}}`, `{{C2_PORT}}`, `{{ENCRYPTION_KEY}}`

**Core features**:
- Reverse HTTPS connection to Sliver server
- TLS certificate pinning (optional)
- Sleep/jitter configurable
- Minimal imports to reduce signature

#### [NEW] [templates/implant_go_syscalls.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/templates/implant_go_syscalls.go)
Advanced Go implant with direct syscalls (Windows)
- Direct syscalls via `GetProcAddress` replacement
- Indirect syscalls using ROP gadgets
- AMSI/ETW bypass techniques
- Process injection capabilities
- Uses libraries: SysWhispers-style implementation

#### [NEW] [templates/implant_c_minimal.c](file:///home/dev/Workspaces/CanisWare/sliverpayload/templates/implant_c_minimal.c)
Minimal C implant for maximum size reduction
- Raw socket communication
- No CRT dependencies
- Manual syscalls (NtCreateFile, NtReadFile, etc.)
- Position-independent code (PIC) for shellcode generation

#### [NEW] [templates/loader_windows.c](file:///home/dev/Workspaces/CanisWare/sliverpayload/templates/loader_windows.c)
Custom PE loader for encrypted payloads
- Reflective DLL loading
- Process hollowing implementation
- Memory-only execution (no disk writes)
- Self-decryption at runtime

---

### Evasion Snippets

#### [NEW] [snippets/syscalls_windows.asm](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/syscalls_windows.asm)
Assembly stubs for Windows syscalls
- NtAllocateVirtualMemory
- NtProtectVirtualMemory
- NtCreateThread
- Dynamic SSN (System Service Number) resolution

#### [NEW] [snippets/amsi_bypass.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/amsi_bypass.go)
AMSI bypass techniques in Go
- AmsiScanBuffer patching
- Memory patch via WriteProcessMemory
- Alternative: Force AMSI initialization failure

#### [NEW] [snippets/etw_bypass.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/etw_bypass.go)
ETW evasion
- Patch EtwEventWrite
- Disable ETW providers
- Unhook ntdll.dll

#### [NEW] [snippets/sandbox_detect.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/sandbox_detect.go)
Sandbox detection heuristics
- Check running processes (analysis tools)
- Detect VM artifacts (registry keys, drivers)
- Time-based checks (accelerated time in sandboxes)
- User interaction detection

---

### Persistence Modules

#### [NEW] [lib/persistence.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/persistence.py)
Persistence mechanism generator
- Registry Run key templates
- Scheduled task XML generation
- WMI event subscription code
- COM hijacking implementation
- DLL proxy generation

#### [NEW] [snippets/persistence_registry.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/persistence_registry.go)
Registry-based persistence (Windows)
- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- AppInit_DLLs (legacy but effective)
- Boot verification program
- Winlogon Userinit modification

#### [NEW] [snippets/persistence_schtasks.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/persistence_schtasks.go)
Scheduled Tasks persistence
- Create task at system startup
- Task triggered on user logon
- Hidden task creation (no GUI visibility)
- Task executed with SYSTEM privileges
- Uses syscalls to avoid `schtasks.exe` detection

#### [NEW] [snippets/persistence_wmi.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/persistence_wmi.go)
WMI event subscription persistence
- EventFilter creation (trigger on events)
- CommandLineEventConsumer (execute payload)
- FilterToConsumerBinding linkage
- Fileless persistence (stored in WMI repository)

#### [NEW] [snippets/persistence_com_hijack.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/persistence_com_hijack.go)
COM hijacking persistence
- Enumerate hijackable COM objects
- Modify `HKCU\Software\Classes\CLSID`
- InProcServer32 redirection
- Triggered via scheduled task

---

### Forensics Evasion Modules

#### [NEW] [lib/forensics_evasion.py](file:///home/dev/Workspaces/CanisWare/sliverpayload/lib/forensics_evasion.py)
Anti-forensics utilities
- Event log manipulation templates
- Timestamp stomping logic
- Prefetch file handling
- USN journal manipulation
- Memory-only execution helpers

#### [NEW] [snippets/forensics_eventlog_clear.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/forensics_eventlog_clear.go)
Event log clearing (Windows)
- Clear Security, System, Application logs
- Uses syscalls (avoid `wevtutil.exe`)
- Selective log entry deletion (not full clear)
- Stop Event Log service temporarily
- Re-enable logging after operations

#### [NEW] [snippets/forensics_timestamp_stomp.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/forensics_timestamp_stomp.go)
Timestamp stomping
- Modify MACB times (Modified, Accessed, Changed, Birth)
- Match timestamps to legitimate system files
- Manipulate $STANDARD_INFORMATION in MFT
- Set creation time to past dates (pre-incident)

#### [NEW] [snippets/forensics_prefetch_clear.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/forensics_prefetch_clear.go)
Prefetch file manipulation
- Delete prefetch files for payload
- Clear `C:\Windows\Prefetch\*.pf` entries
- Disable Superfetch service temporarily
- Cover tracks of execution history

#### [NEW] [snippets/forensics_usn_journal.go](file:///home/dev/Workspaces/CanisWare/sliverpayload/snippets/forensics_usn_journal.go)
USN Journal manipulation
- Delete USN journal entries
- Query and manipulate $UsnJrnl
- Remove file creation/modification records
- Requires SYSTEM privileges

---

### Configuration

#### [NEW] [config.yaml](file:///home/dev/Workspaces/CanisWare/sliverpayload/config.yaml)
Generator configuration file
```yaml
compiler_paths:
  go: /usr/local/go/bin/go
  mingw: /usr/bin/x86_64-w64-mingw32-gcc
  
obfuscation:
  string_encryption: aes256
  identifier_length: 12
  junk_code_ratio: 0.2
  
evasion:
  syscalls: indirect  # direct, indirect, or hybrid
  amsi_bypass: true
  etw_bypass: true
  sandbox_checks: true
  
persistence:
  enabled: true
  methods:  # Select one or multiple
    - registry  # Run keys
    - schtasks  # Scheduled tasks
    - wmi       # WMI event subscriptions
    - com_hijack  # COM hijacking
    
forensics_evasion:
  enabled: true
  eventlog_clear: true  # Clear event logs after operations
  timestamp_stomp: true  # Stomp file timestamps
  prefetch_clear: true   # Delete prefetch files
  usn_journal: false     # Manipulate USN journal (requires SYSTEM)
```

#### [NEW] [requirements.txt](file:///home/dev/Workspaces/CanisWare/sliverpayload/requirements.txt)
Python dependencies
- `pycryptodome` - Encryption
- `jinja2` - Template engine
- `pefile` - PE file manipulation
- `lief` - Binary analysis/modification
- `click` - CLI framework

---

### Documentation

#### [NEW] [README.md](file:///home/dev/Workspaces/CanisWare/sliverpayload/README.md)
Project documentation
- Overview of custom payload generation
- Installation steps (Go, MinGW, Python deps)
- Usage examples
- Evasion techniques explained
- Legal disclaimer

#### [NEW] [TECHNIQUES.md](file:///home/dev/Workspaces/CanisWare/sliverpayload/TECHNIQUES.md)
Detailed evasion techniques documentation
- Direct vs indirect syscalls
- String obfuscation methods
- PE packing strategies
- Polymorphic code generation
- References to research papers

---

## Evasion Techniques Implemented

### Static Evasion
1. **String Encryption**: All C2 addresses, API names encrypted with AES/XOR
2. **Polymorphic Code**: Each payload compilation produces different binary
3. **Identifier Randomization**: Function/variable names randomized
4. **Import Obfuscation**: Dynamic API loading, no static imports
5. **Junk Code**: Random legitimate-looking code inserted

### Dynamic Evasion
1. **Direct Syscalls**: Bypass usermode hooks (ntdll.dll)
2. **Indirect Syscalls**: Further evade syscall monitoring
3. **AMSI Bypass**: Patch AmsiScanBuffer in memory
4. **ETW Bypass**: Disable Event Tracing
5. **Sandbox Detection**: Exit if analysis environment detected

### Binary Manipulation
1. **Custom Packer**: Proprietary PE packer, no reliance on UPX
2. **PE Section Encryption**: Encrypt .text and .data sections, decrypt at runtime
3. **Entropy Manipulation**: Add legitimate data to reduce entropy scores
4. **Timestamp Manipulation**: Forge compilation timestamps
5. **Certificate Signing**: MANDATORY - sign with self-signed or stolen certificates

### Persistence Mechanisms
1. **Registry Keys**: Multiple Run key locations for startup persistence
2. **Scheduled Tasks**: Hidden tasks with SYSTEM privileges
3. **WMI Event Subscriptions**: Fileless persistence via WMI repository
4. **COM Hijacking**: Redirect COM objects to malicious DLLs
5. **DLL Proxying**: Forward legitimate DLL calls while maintaining access

### Forensics Evasion
1. **Event Log Clearing**: Selective deletion of security/system logs
2. **Timestamp Stomping**: Match file times to legitimate system files
3. **Prefetch Manipulation**: Delete execution artifacts
4. **USN Journal**: Remove filesystem change records
5. **Memory-Only Execution**: No disk writes to avoid forensic recovery

---

## Verification Plan

### Automated Tests

1. **Generator Functionality**
   ```bash
   pytest tests/
   ```
   - Test template loading and substitution
   - Test obfuscation functions
   - Test compilation pipeline
   - Mock C2 connection tests

2. **Code Generation**
   ```bash
   python generator.py --test-mode
   ```
   - Generate payloads with all evasion combinations
   - Verify output files exist and are valid PE/ELF
   - Check for hardcoded strings in output

### Manual Verification

1. **Compilation Test**
   - Generate Windows payload: `python generator.py --target windows --arch x64 --c2 10.0.0.1:8443 --output test.exe`
   - Verify compilation succeeds
   - Check binary size, entropy, imports

2. **C2 Connectivity** (Requires Sliver server)
   - Start Sliver server with HTTPS listener
   - Execute generated payload in VM
   - Verify callback appears in Sliver console
   - Test basic commands (whoami, ls, etc.)

3. **AV Evasion Testing**
   - Test against Windows Defender (updated definitions)
   - Upload to VirusTotal (ONLY if acceptable to burn payload)
   - Test in sandbox (any.run, joe sandbox)
   - Monitor with EDR tools (if available)

4. **Static Analysis Resistance**
   ```bash
   strings test.exe | grep -i "http\|sliver\|c2"  # Should find nothing
   ```
   - No plaintext C2 URLs
   - No obvious malware strings
   - API imports should be minimal

> [!NOTE]
> **Realistic Expectations**
> 
> - Modern EDRs are sophisticated; expect detection on behavior eventually
> - Focus on initial execution bypass, then process injection to legitimate process
> - Static evasion is easier than dynamic/behavioral evasion
> - Frequent recompilation with different obfuscation helps

---

## Implementation Notes

**Architecture**:
- **Generator**: Python 3.10+
- **Implants**: Go 1.21+ (primary), C (optional)
- **Build System**: Native compilers (go, gcc/mingw)

**Development Order**:
1. Basic Go template + Python generator skeleton
2. Simple obfuscation (string encryption, name randomization)
3. Compilation automation
4. Advanced evasion (syscalls, AMSI/ETW bypass)
5. Packing/encryption layer
6. Polymorphic engine

**Dependencies on Host System**:
- Go compiler (for Go implants)
- MinGW-w64 (for Windows targets from Linux)
- Python 3.10+
- (Optional) UPX packer