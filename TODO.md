# TODO - Sliver C2 Payload Generator

> Progress tracker for implementation. See `PLAN.md` for full architecture.

## Legend

- ✅ Complete
- 🔄 In Progress
- ⏳ Not Started

---

## Phase 1: Project Foundation

### 1.1 Project Structure
| Task | Status | Notes |
|------|--------|-------|
| Create directory structure | ✅ | `lib/`, `templates/`, `snippets/`, `tests/`, `output/` |
| Initialize Python modules | ✅ | Headers only - skeleton phase |
| Create `config.yaml` | ✅ | Full configuration structure |
| Create `requirements.txt` | ✅ | Dependencies listed |
| Create `README.md` | ✅ | Basic documentation |
| Create `PLAN.md` | ✅ | Full architecture plan |

### 1.2 Go Templates
| Task | Status | Notes |
|------|--------|-------|
| `implant_go_basic.go` | ✅ | Basic HTTP(S) implant with template vars |
| `implant_go_syscalls.go` | ✅ | AMSI/ETW bypass, sandbox detection |
| `implant_c_minimal.c` | ⏳ | Minimal C implant (optional) skip now - do later|
| `loader_windows.c` | ⏳ | PE loader (optional) skip now - do later|

---

## Phase 2: Core Python Modules

### 2.1 Template Engine (`lib/template_engine.py`)
| Task | Status | Notes |
|------|--------|-------|
| Load template files | ✅ | Read `.go` files from `templates/` |
| Variable substitution | ✅ | Replace `{{VAR}}` placeholders |
| Template validation | ✅ | Check required vars exist |
| Random identifier generation | ✅ | For `{{MAIN_FUNC}}`, `{{CONNECT_FUNC}}`, etc. |

**Subtasks:**
- [x] `load_template(name: str) -> str`
- [x] `substitute_variables(template: str, vars: dict) -> str`
- [x] `generate_random_identifier(length: int) -> str`
- [x] `validate_template(template: str) -> list[str]` (missing vars)

### 2.2 Obfuscator (`lib/obfuscator.py`)
| Task | Status | Notes |
|------|--------|-------|
| String encryption (XOR) | ✅ | Basic XOR encryption |
| String encryption (AES-256) | ✅ | AES-GCM encryption |
| Identifier randomization | ✅ | Rename functions/variables |
| Junk code insertion | ✅ | Add dead code |
| Control flow flattening | ⏳ | Deferred (low priority, not implemented yet) |

**Subtasks:**
- [x] `encrypt_string_xor(plaintext: str, key: bytes) -> tuple[str, str]` (encrypted, decryption stub)
- [x] `encrypt_string_aes(plaintext: str, key: bytes) -> tuple[str, str]`
- [x] `generate_decryption_stub_go(algorithm: str) -> str`
- [x] `randomize_identifiers(source: str) -> str`
- [x] `insert_junk_code(source: str, ratio: float) -> str`

### 2.3 Compiler (`lib/compiler.py`)
| Task | Status | Notes |
|------|--------|-------|
| Go compiler wrapper | ⏳ | `go build` with flags |
| Cross-compilation support | ⏳ | `GOOS=windows GOARCH=amd64` |
| Strip debug symbols | ⏳ | `-ldflags="-s -w"` |
| Build artifact cleanup | ⏳ | Remove temp files |
| Error handling | ⏳ | Parse compiler errors |

**Subtasks:**
- [ ] `compile_go(source_path: str, output_path: str, target_os: str, arch: str) -> bool`
- [ ] `get_compiler_path() -> str` (from config)
- [ ] `build_ldflags() -> str`
- [ ] `cleanup_artifacts(build_dir: str) -> None`

### 2.4 Evasion (`lib/evasion.py`)
| Task | Status | Notes |
|------|--------|-------|
| AMSI bypass snippet injection | ⏳ | Insert into template |
| ETW bypass snippet injection | ⏳ | Insert into template |
| Sandbox detection injection | ⏳ | Insert into template |
| Syscall stub generation | ⏳ | Direct/indirect syscalls |
| Import management | ⏳ | Handle `{{EVASION_IMPORTS}}` |

**Subtasks:**
- [ ] `get_amsi_bypass_code() -> str`
- [ ] `get_etw_bypass_code() -> str`
- [ ] `get_sandbox_detection_code() -> str`
- [ ] `get_evasion_imports() -> str`
- [ ] `inject_evasion(template: str, config: dict) -> str`

### 2.5 Persistence (`lib/persistence.py`)
| Task | Status | Notes |
|------|--------|-------|
| Registry persistence | ⏳ | Run key snippets |
| Scheduled tasks | ⏳ | `schtasks` snippets |
| WMI event subscription | ⏳ | WMI persistence |
| COM hijacking | ⏳ | CLSID redirection |

**Subtasks:**
- [ ] `get_registry_persistence_code(key_path: str) -> str`
- [ ] `get_schtasks_persistence_code(task_name: str) -> str`
- [ ] `get_wmi_persistence_code() -> str`
- [ ] `get_com_hijack_code(clsid: str) -> str`
- [ ] `inject_persistence(template: str, methods: list) -> str`

### 2.6 Forensics Evasion (`lib/forensics_evasion.py`)
| Task | Status | Notes |
|------|--------|-------|
| Event log clearing | ⏳ | Clear Security/System logs |
| Timestamp stomping | ⏳ | Modify MACB times |
| Prefetch clearing | ⏳ | Delete `.pf` files |
| USN journal manipulation | ⏳ | Advanced - lower priority |

**Subtasks:**
- [ ] `get_eventlog_clear_code() -> str`
- [ ] `get_timestamp_stomp_code() -> str`
- [ ] `get_prefetch_clear_code() -> str`
- [ ] `inject_forensics_evasion(template: str, config: dict) -> str`

### 2.7 Packer (`lib/packer.py`)
| Task | Status | Notes |
|------|--------|-------|
| PE section encryption | ⏳ | Encrypt .text/.data |
| Custom loader stub | ⏳ | Decryption at runtime |
| Entropy manipulation | ⏳ | Reduce entropy score |
| Certificate signing | ⏳ | Self-signed/custom certs |

**Subtasks:**
- [ ] `encrypt_pe_sections(pe_path: str, key: bytes) -> bytes`
- [ ] `generate_loader_stub(key: bytes) -> bytes`
- [ ] `manipulate_entropy(pe_path: str) -> None`
- [ ] `sign_binary(pe_path: str, cert_path: str, password: str) -> bool`
- [ ] `generate_selfsigned_cert() -> tuple[str, str]` (cert, key paths)

---

## Phase 3: CLI & Integration

### 3.1 Generator CLI (`generator.py`)
| Task | Status | Notes |
|------|--------|-------|
| Click CLI setup | ⏳ | Argument parsing |
| Config file loading | ⏳ | `config.yaml` parser |
| Pipeline orchestration | ⏳ | Connect all modules |
| Output handling | ⏳ | Save to `output/` |
| Verbose/debug mode | ⏳ | Logging |

**Subtasks:**
- [ ] Add Click decorators (`--target`, `--arch`, `--c2`, `--output`, etc.)
- [ ] `load_config(path: str) -> dict`
- [ ] `generate_payload(config: dict) -> str` (output path)
- [ ] Setup logging with verbosity levels

### 3.2 Integration
| Task | Status | Notes |
|------|--------|-------|
| Template → Obfuscator flow | ⏳ | Chain modules |
| Obfuscator → Compiler flow | ⏳ | Chain modules |
| Compiler → Packer flow | ⏳ | Chain modules |
| End-to-end test | ⏳ | Full payload generation |

---

## Phase 4: Snippets Library

### 4.1 Evasion Snippets (`snippets/`)
| Task | Status | Notes |
|------|--------|-------|
| `amsi_bypass.go` | ⏳ | AmsiScanBuffer patch |
| `etw_bypass.go` | ⏳ | EtwEventWrite patch |
| `sandbox_detect.go` | ⏳ | VM/debugger detection |
| `syscalls_windows.asm` | ⏳ | Assembly syscall stubs |

### 4.2 Persistence Snippets
| Task | Status | Notes |
|------|--------|-------|
| `persistence_registry.go` | ⏳ | Registry Run keys |
| `persistence_schtasks.go` | ⏳ | Scheduled tasks |
| `persistence_wmi.go` | ⏳ | WMI subscriptions |
| `persistence_com_hijack.go` | ⏳ | COM hijacking |

### 4.3 Forensics Snippets
| Task | Status | Notes |
|------|--------|-------|
| `forensics_eventlog_clear.go` | ⏳ | Event log clearing |
| `forensics_timestamp_stomp.go` | ⏳ | Timestamp stomping |
| `forensics_prefetch_clear.go` | ⏳ | Prefetch deletion |
| `forensics_usn_journal.go` | ⏳ | USN journal manipulation |

---

## Phase 5: Testing

### 5.1 Unit Tests (`tests/`)
| Task | Status | Notes |
|------|--------|-------|
| `test_template_engine.py` | ✅ | Template loading/substitution |
| `test_obfuscator.py` | ✅ | String encryption tests |
| `test_compiler.py` | ⏳ | Compilation tests |
| `test_evasion.py` | ⏳ | Evasion injection tests |
| `test_persistence.py` | ⏳ | Persistence injection tests |
| `test_packer.py` | ⏳ | PE manipulation tests |
| `conftest.py` | ⏳ | Pytest fixtures |

### 5.2 Integration Tests
| Task | Status | Notes |
|------|--------|-------|
| End-to-end generation | ⏳ | Full pipeline test |
| Binary validation | ⏳ | PE structure checks |
| No hardcoded strings check | ⏳ | `strings` analysis |

---

## Phase 6: Documentation

| Task | Status | Notes |
|------|--------|-------|
| `README.md` updates | ⏳ | Usage examples |
| `TECHNIQUES.md` | ⏳ | Evasion technique docs |
| Code comments | ⏳ | MITRE ATT&CK references |
| API documentation | ⏳ | Module docstrings |

---

## Recommended Implementation Order

### Sprint 1: Core Engine
1. ✅ `lib/template_engine.py` - Load and substitute templates
2. ⏳ `lib/compiler.py` - Go compilation wrapper
3. ⏳ `generator.py` - Basic CLI with `--c2` and `--output`
4. ⏳ First working payload (basic template, no obfuscation)

### Sprint 2: Obfuscation
1. ✅ `lib/obfuscator.py` - String encryption (XOR first, then AES)
2. ✅ `lib/obfuscator.py` - Identifier randomization
3. ⏳ Update `generator.py` with `--obfuscation` flag

### Sprint 3: Evasion
1. ⏳ `snippets/amsi_bypass.go`
2. ⏳ `snippets/etw_bypass.go`
3. ⏳ `snippets/sandbox_detect.go`
4. ⏳ `lib/evasion.py` - Inject snippets into templates
5. ⏳ Update `generator.py` with `--evasion` flag

### Sprint 4: Persistence & Forensics
1. ⏳ Persistence snippets (registry, schtasks)
2. ⏳ `lib/persistence.py` - Inject persistence code
3. ⏳ Forensics snippets (eventlog, timestamp)
4. ⏳ `lib/forensics_evasion.py` - Inject forensics evasion

### Sprint 5: Packing & Signing
1. ⏳ `lib/packer.py` - PE section encryption
2. ⏳ `lib/packer.py` - Certificate signing
3. ⏳ End-to-end pipeline integration

### Sprint 6: Testing & Polish
1. ⏳ Unit tests for all modules
2. ⏳ Integration tests
3. ⏳ Documentation updates
4. ⏳ AV/EDR testing in lab environment

---

## Current Status Summary

| Component | Status | Progress |
|-----------|--------|----------|
| Project Structure | ✅ | 100% |
| Go Templates | ✅ | 100% (basic + syscalls) |
| Configuration | ✅ | 100% |
| Python Modules | 🔄 | 25% (template_engine + obfuscator complete) |
| Snippets | ⏳ | 0% |
| Tests | 🔄 | 25% (template_engine + obfuscator tests) |
| CLI Integration | ⏳ | 0% |

**Next Action:** Start Sprint 1 - Implement `lib/compiler.py`

---

## Notes

- Go templates have working evasion code (AMSI/ETW bypass, sandbox detection)
- Python modules: `template_engine.py` fully implemented, others are skeleton only
- Focus on Go implants first; C templates are optional/future
- Code signing is MANDATORY for production payloads
- Always reference MITRE ATT&CK techniques in evasion code
