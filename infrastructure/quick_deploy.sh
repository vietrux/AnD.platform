#!/bin/bash
# Quick deployment script wrapper

if [ "$#" -ne 1 ]; then
    echo "Usage: ./quick_deploy.sh <number_of_teams>"
    echo "Example: ./quick_deploy.sh 5"
    exit 1
fi

NUM_TEAMS=$1

echo "🔨 Building vulnerable service image..."
cd ../services/test_vuln_web
docker build -t test_vuln_web:latest . || exit 1

echo ""
echo "🚀 Deploying $NUM_TEAMS team(s)..."
cd ../../infrastructure
python3 deploy_teams.py $NUM_TEAMS

echo ""
echo "✅ Deployment complete!"
echo "📝 Check team_credentials.txt for all credentials"
