#!/bin/bash
# CodeBreak Deployment Script
# This script pulls latest code, updates dependencies, and restarts the service

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}CodeBreak Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Navigate to project directory
cd /home/ubuntu/codebreak

# Pull latest code
echo -e "${YELLOW}→ Pulling latest code from GitHub...${NC}"
git pull origin master
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}→ Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Update dependencies
echo -e "${YELLOW}→ Updating Python dependencies...${NC}"
pip install -r backend/requirements.txt --upgrade --quiet
echo -e "${GREEN}✓ Dependencies updated${NC}"
echo ""

# Run database migrations
echo -e "${YELLOW}→ Running database migrations...${NC}"
cd backend
python migrate_database.py
cd ..
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Restart service
echo -e "${YELLOW}→ Restarting CodeBreak service...${NC}"
sudo systemctl restart codebreak
echo -e "${GREEN}✓ Service restart initiated${NC}"
echo ""

# Wait for service to start
echo -e "${YELLOW}→ Waiting for service to start...${NC}"
sleep 3

# Check service status
if sudo systemctl is-active --quiet codebreak; then
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${YELLOW}Service Status:${NC}"
    sudo systemctl status codebreak --no-pager --lines=5
    echo ""
    echo -e "${YELLOW}Recent logs (last 15 lines):${NC}"
    sudo tail -n 15 /var/log/codebreak-error.log
else
    echo -e "${RED}================================${NC}"
    echo -e "${RED}✗ DEPLOYMENT FAILED!${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo -e "${YELLOW}Error logs:${NC}"
    sudo tail -n 30 /var/log/codebreak-error.log
    exit 1
fi

echo ""
echo -e "${YELLOW}To view live logs, run:${NC}"
echo "sudo tail -f /var/log/codebreak-error.log"
echo ""
