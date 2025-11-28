# Quick Start - Deploy Teams

## One-Line Deployment

```bash
# Deploy 3 teams (builds image + deploys containers)
./infrastructure/quick_deploy.sh 3
```

## Manual Deployment

```bash
# 1. Build the vulnerable service
cd services/test_vuln_web
docker build -t test_vuln_web:latest .

# 2. Deploy teams
cd ../../infrastructure
python deploy_teams.py 5
```

## Example Output

When you run `python deploy_teams.py 3`, you'll see:

```
🚀 Deploying 3 team(s)...

[*] Creating network: ctf_network
[*] Deploying team1_vuln...
✅ Team 1 deployed successfully
[*] Deploying team2_vuln...
✅ Team 2 deployed successfully
[*] Deploying team3_vuln...
✅ Team 3 deployed successfully

================================================================================
🎯 CTF TEAM DEPLOYMENT COMPLETE
================================================================================

Deployed at: 2025-11-28 22:20:15
Total Teams: 3

────────────────────────────────────────────────────────────────────────────────
📦 TEAM 1
────────────────────────────────────────────────────────────────────────────────
Container Name:  team1_vuln
Container ID:    a1b2c3d4
IP Address:      10.60.0.10

🔑 SSH Access:
   ssh cyberfox42@localhost -p 2223
   Password: xK9mL3nP7qR2

🌐 Service Ports:
   Vulnerable Web: http://localhost:8002
   SSH Port:       2223

📍 Flags Location:
   User Flag:  /home/ctf/flag1.txt  (chmod 644)
   Root Flag:  /root/flag2.txt      (chmod 600)

────────────────────────────────────────────────────────────────────────────────
📦 TEAM 2
────────────────────────────────────────────────────────────────────────────────
Container Name:  team2_vuln
Container ID:    e5f6g7h8
IP Address:      10.60.0.11

🔑 SSH Access:
   ssh darkwolf87@localhost -p 2224
   Password: aZ8bY6cX4vW2

🌐 Service Ports:
   Vulnerable Web: http://localhost:8003
   SSH Port:       2224

📍 Flags Location:
   User Flag:  /home/ctf/flag1.txt  (chmod 644)
   Root Flag:  /root/flag2.txt      (chmod 600)

────────────────────────────────────────────────────────────────────────────────
📦 TEAM 3
────────────────────────────────────────────────────────────────────────────────
Container Name:  team3_vuln
Container ID:    i9j0k1l2
IP Address:      10.60.0.12

🔑 SSH Access:
   ssh shadoweagle25@localhost -p 2225
   Password: mN5oP3qR7sT9

🌐 Service Ports:
   Vulnerable Web: http://localhost:8004
   SSH Port:       2225

📍 Flags Location:
   User Flag:  /home/ctf/flag1.txt  (chmod 644)
   Root Flag:  /root/flag2.txt      (chmod 600)

================================================================================

💡 Quick Test Commands:
────────────────────────────────────────────────────────────────────────────────
# SSH into Team 1:
ssh cyberfox42@localhost -p 2223

# Test path traversal (user flag):
curl 'http://localhost:8002/read?file=/home/ctf/flag1.txt'

# Test command injection (root flag):
curl 'http://localhost:8002/ping?host=127.0.0.1;cat%20/root/flag2.txt'
================================================================================

📝 Credentials saved to: team_credentials.txt
```

## What You Get

For each team:
- ✅ Isolated Docker container
- ✅ Random username (e.g., `cyberfox42`, `darkwolf87`)
- ✅ Random 12-character password
- ✅ SSH access on unique port
- ✅ Vulnerable web service on unique port
- ✅ Unique IP address (10.60.0.X)
- ✅ Limited sudo privileges (can patch service)
- ✅ Two flags at standard locations

## Testing

```bash
# Team 1 - SSH login
ssh cyberfox42@localhost -p 2223
# Enter password when prompted

# Team 1 - Path traversal exploit
curl "http://localhost:8002/read?file=/home/ctf/flag1.txt"
# Returns: FLAG{...}

# Team 1 - Command injection
curl "http://localhost:8002/ping?host=127.0.0.1;whoami"
# Returns: ctf

# Inject real flags as gameserver
python << 'EOF'
from gameserver.checker import FlagInjector
from gameserver.flags import generate_flag_pair

flags = generate_flag_pair(1, 1, 1)
injector = FlagInjector()
injector.inject_both_flags('team1_vuln', flags['user'], flags['root'])
EOF
```

## Cleanup

```bash
# Stop all teams
docker stop $(docker ps -q --filter "name=team*_vuln")

# Remove all teams
docker rm $(docker ps -aq --filter "name=team*_vuln")

# Remove network
docker network rm ctf_network
```

## Features

- **Automatic user creation**: Random usernames and passwords
- **Network isolation**: Each team on separate IP
- **Port mapping**: Unique SSH and service ports
- **Credential tracking**: Saved to file for reference
- **Ready for CTF**: Flags pre-placed, vulnerabilities active
- **Patchable**: Teams can fix vulnerabilities with limited sudo
