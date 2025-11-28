#!/usr/bin/env python3
"""
Automated Team Deployment Script
Deploy N teams with isolated containers
"""

import docker
import secrets
import string
import sys
from datetime import datetime

# Configuration
SERVICE_IMAGE = "test_vuln_web:latest"
SERVICE_PORT = 8001
SSH_PORT_START = 2222
NETWORK_SUBNET = "10.60.0.0/24"
NETWORK_GATEWAY = "10.60.0.1"
IP_START = 10  # Start IPs at 10.60.0.10


def generate_username():
    """Generate random username"""
    adjectives = ['cyber', 'hack', 'red', 'blue', 'dark', 'shadow', 'ghost', 'crypt']
    nouns = ['fox', 'wolf', 'bear', 'tiger', 'eagle', 'shark', 'viper', 'raven']
    return f"{secrets.choice(adjectives)}{secrets.choice(nouns)}{secrets.randbelow(100)}"


def generate_password(length=12):
    """Generate secure random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def create_network(client, network_name):
    """Create or get Docker network"""
    try:
        network = client.networks.get(network_name)
        print(f"[*] Using existing network: {network_name}")
        return network
    except docker.errors.NotFound:
        print(f"[*] Creating network: {network_name}")
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[
                docker.types.IPAMPool(
                    subnet=NETWORK_SUBNET,
                    gateway=NETWORK_GATEWAY
                )
            ]
        )
        return client.networks.create(
            network_name,
            driver="bridge",
            ipam=ipam_config
        )


def deploy_team(client, team_number, network, username, password):
    """
    Deploy container for a team
    
    Returns:
        dict: Team information
    """
    container_name = f"team{team_number}_vuln"
    ip_address = f"10.60.0.{IP_START + team_number}"
    ssh_port = SSH_PORT_START + team_number
    
    # Stop and remove existing container if any
    try:
        old_container = client.containers.get(container_name)
        print(f"[*] Removing old container: {container_name}")
        old_container.stop()
        old_container.remove()
    except docker.errors.NotFound:
        pass
    
    print(f"[*] Deploying {container_name}...")
    
    # Create container
    container = client.containers.run(
        SERVICE_IMAGE,
        name=container_name,
        detach=True,
        environment={
            'CTF_USERNAME': username,
            'CTF_PASSWORD': password,
        },
        ports={
            f'{SERVICE_PORT}/tcp': SERVICE_PORT + team_number,
            '22/tcp': ssh_port
        },
        network=network.name,
        hostname=f"team{team_number}",
        cap_add=['NET_ADMIN'],  # For potential iptables rules
        restart_policy={"Name": "unless-stopped"}
    )
    
    # Connect to network with specific IP
    network.disconnect(container)
    network.connect(container, ipv4_address=ip_address)
    
    return {
        'team_number': team_number,
        'container_name': container_name,
        'container_id': container.short_id,
        'ip_address': ip_address,
        'ssh_port': ssh_port,
        'service_port': SERVICE_PORT + team_number,
        'username': username,
        'password': password,
    }


def print_team_info(teams_info):
    """Print formatted team information"""
    print("\n" + "="*80)
    print("🎯 CTF TEAM DEPLOYMENT COMPLETE")
    print("="*80)
    print(f"\nDeployed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Teams: {len(teams_info)}\n")
    
    for info in teams_info:
        print("─"*80)
        print(f"📦 TEAM {info['team_number']}")
        print("─"*80)
        print(f"Container Name:  {info['container_name']}")
        print(f"Container ID:    {info['container_id']}")
        print(f"IP Address:      {info['ip_address']}")
        print(f"\n🔑 SSH Access:")
        print(f"   ssh {info['username']}@localhost -p {info['ssh_port']}")
        print(f"   Password: {info['password']}")
        print(f"\n🌐 Service Ports:")
        print(f"   Vulnerable Web: http://localhost:{info['service_port']}")
        print(f"   SSH Port:       {info['ssh_port']}")
        print(f"\n📍 Flags Location:")
        print(f"   User Flag:  /home/ctf/flag1.txt  (chmod 644)")
        print(f"   Root Flag:  /root/flag2.txt      (chmod 600)")
        print()
    
    print("="*80)
    print("\n💡 Quick Test Commands:")
    print("─"*80)
    team1 = teams_info[0]
    print(f"# SSH into Team 1:")
    print(f"ssh {team1['username']}@localhost -p {team1['ssh_port']}")
    print(f"\n# Test path traversal (user flag):")
    print(f"curl 'http://localhost:{team1['service_port']}/read?file=/home/ctf/flag1.txt'")
    print(f"\n# Test command injection (root flag):")
    print(f"curl 'http://localhost:{team1['service_port']}/ping?host=127.0.0.1;cat%20/root/flag2.txt'")
    print("="*80 + "\n")


def main():
    """Main deployment function"""
    if len(sys.argv) != 2:
        print("Usage: python deploy_teams.py <number_of_teams>")
        print("Example: python deploy_teams.py 5")
        sys.exit(1)
    
    try:
        num_teams = int(sys.argv[1])
        if num_teams < 1 or num_teams > 50:
            print("Error: Number of teams must be between 1 and 50")
            sys.exit(1)
    except ValueError:
        print("Error: Invalid number")
        sys.exit(1)
    
    print(f"🚀 Deploying {num_teams} team(s)...\n")
    
    # Connect to Docker
    try:
        client = docker.from_env()
    except Exception as e:
        print(f"Error connecting to Docker: {e}")
        print("Make sure Docker is running and you have permissions.")
        sys.exit(1)
    
    # Create network
    network = create_network(client, "ctf_network")
    
    # Deploy teams
    teams_info = []
    for i in range(1, num_teams + 1):
        username = generate_username()
        password = generate_password()
        
        try:
            team_info = deploy_team(client, i, network, username, password)
            teams_info.append(team_info)
            print(f"✅ Team {i} deployed successfully")
        except Exception as e:
            print(f"❌ Error deploying team {i}: {e}")
    
    # Print summary
    if teams_info:
        print_team_info(teams_info)
        
        # Save credentials to file
        with open('team_credentials.txt', 'w') as f:
            f.write("CTF Team Credentials\n")
            f.write("="*80 + "\n\n")
            for info in teams_info:
                f.write(f"Team {info['team_number']}\n")
                f.write(f"  SSH: ssh {info['username']}@localhost -p {info['ssh_port']}\n")
                f.write(f"  Password: {info['password']}\n")
                f.write(f"  Service: http://localhost:{info['service_port']}\n")
                f.write(f"  IP: {info['ip_address']}\n")
                f.write("\n")
        
        print("📝 Credentials saved to: team_credentials.txt\n")


if __name__ == "__main__":
    main()
