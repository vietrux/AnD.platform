#!/usr/bin/env python3
"""
Setup CTF teams in database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gameserver.config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from gameserver.models import Team, Service, Score
import secrets

def create_teams(num_teams=5):
    """Create teams in database"""
    teams = []
    
    for i in range(1, num_teams + 1):
        # Generate team token
        token = secrets.token_urlsafe(32)
        
        team, created = Team.objects.get_or_create(
            name=f"Team{i}",
            defaults={
                'token': token,
                'ip_address': f'10.60.0.{10 + i}',
                'email': f'team{i}@ctf.local',
                'is_active': True,
                'is_nop_team': False,
            }
        )
        
        if created:
            team.set_password(f'team{i}password')
            team.save()
            
            # Create score entry
            Score.objects.get_or_create(team=team)
            
            print(f"✅ Created Team {i}")
            print(f"   Name: {team.name}")
            print(f"   Token: {token}")
            print(f"   IP: {team.ip_address}")
        else:
            print(f"⚠️  Team {i} already exists")
        
        teams.append(team)
    
    return teams


def create_service():
    """Create test service in database"""
    service, created = Service.objects.get_or_create(
        name='test_vuln_web',
        defaults={
            'description': 'Test vulnerable web service',
            'port': 8001,
            'checker_script': 'checkers.test_checker',
            'docker_image': 'test_vuln_web:latest',
            'container_name_template': 'team{team_id}_vuln',
            'supports_two_flags': True,
            'user_flag_points': 50,
            'root_flag_points': 150,
            'sla_points_per_tick': 100,
            'is_active': True,
        }
    )
    
    if created:
        print(f"\n✅ Created Service: {service.name}")
    else:
        print(f"\n⚠️  Service already exists: {service.name}")
    
    return service


def main():
    print("🚀 Setting up CTF system database...\n")
    
    # Create teams
    teams = create_teams(5)
    
    # Create service
    service = create_service()
    
    print(f"\n{'='*80}")
    print("✅ Database setup complete!")
    print(f"{'='*80}\n")
    print(f"Teams created: {len(teams)}")
    print(f"Service created: {service.name}")
    print("\nNext steps:")
    print("1. Start tick manager: python -m gameserver.controller.tick_manager")
    print("2. Start submission server: python -m gameserver.submission.submission_server")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
