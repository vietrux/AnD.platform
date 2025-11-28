# Automated Team Deployment

Quick deployment script to spawn CTF team containers.

## Usage

```bash
# Build the vulnerable service image first
cd services/test_vuln_web
docker build -t test_vuln_web:latest .

# Deploy N teams
cd ../../infrastructure
python deploy_teams.py <number_of_teams>

# Examples:
python deploy_teams.py 3    # Deploy 3 teams
python deploy_teams.py 10   # Deploy 10 teams
```

## What It Does

1. **Creates Docker network** (`ctf_network`) with subnet `10.60.0.0/24`
2. **Spawns containers** for each team:
   - Random username and password
   - SSH access on unique port (2223, 2224, 2225, ...)
   - Vulnerable web service on unique port (8002, 8003, 8004, ...)
   - Isolated IP addresses (10.60.0.10, 10.60.0.11, ...)
3. **Prints all credentials** in formatted table
4. **Saves credentials** to `team_credentials.txt`

## Output Example

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

Deployed at: 2025-11-28 22:20:00
Total Teams: 3

────────────────────────────────────────────────────────────────────────────────
📦 TEAM 1
────────────────────────────────────────────────────────────────────────────────
Container Name:  team1_vuln
Container ID:    abc123
IP Address:      10.60.0.10

🔑 SSH Access:
   ssh cyberFox42@localhost -p 2223
   Password: aB3dE5fG7hJ9

🌐 Service Ports:
   Vulnerable Web: http://localhost:8002
   SSH Port:       2223

📍 Flags Location:
   User Flag:  /home/ctf/flag1.txt  (chmod 644)
   Root Flag:  /root/flag2.txt      (chmod 600)

[... Team 2, Team 3 info ...]
```

## Team Container Features

Each container includes:
- **Random user account** with limited sudo privileges
- **SSH server** for remote access
- **Vulnerable web service** (Flask)
  - Path traversal vulnerability
  - Command injection vulnerability
- **Two flags** with proper permissions
- **Isolated network** with unique IP

## User Permissions

Each random user can:
- ✅ Patch vulnerabilities in the service
- ✅ Use `sudo apt` to install packages
- ✅ Restart services with `sudo systemctl restart`
- ❌ Cannot read `/root/flag2.txt` (requires RCE + privesc)

## Quick Commands

```bash
# SSH into a team
ssh <username>@localhost -p <ssh_port>

# Test path traversal
curl "http://localhost:<service_port>/read?file=/home/ctf/flag1.txt"

# Test command injection
curl "http://localhost:<service_port>/ping?host=127.0.0.1;whoami"

# View all containers
docker ps | grep team

# Stop all teams
docker stop $(docker ps -q --filter "name=team*_vuln")

# Remove all teams
docker rm $(docker ps -aq --filter "name=team*_vuln")
```

## Network Configuration

- **Network Name**: `ctf_network`
- **Subnet**: `10.60.0.0/24`
- **Gateway**: `10.60.0.1`
- **Team IPs**: `10.60.0.10`, `10.60.0.11`, `10.60.0.12`, ...
- **SSH Ports**: `2223`, `2224`, `2225`, ...
- **Web Ports**: `8002`, `8003`, `8004`, ...

## Credential File

After deployment, credentials are saved to `team_credentials.txt`:

```
CTF Team Credentials
================================================================================

Team 1
  SSH: ssh cyberFox42@localhost -p 2223
  Password: aB3dE5fG7hJ9
  Service: http://localhost:8002
  IP: 10.60.0.10

Team 2
  SSH: ssh darkWolf87@localhost -p 2224
  Password: xY9zW2vU5tS8
  Service: http://localhost:8003
  IP: 10.60.0.11
...
```

## Cleanup

```bash
# Stop and remove all team containers
docker stop $(docker ps -q --filter "name=team*_vuln")
docker rm $(docker ps -aq --filter "name=team*_vuln")

# Remove network
docker network rm ctf_network

# Remove credentials file
rm team_credentials.txt
```
