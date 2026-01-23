#!/bin/bash

# ==========================================
# LOCAL DEVELOPMENT AUTOMATION
# ==========================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Starting Local Development Environment...${NC}"

# 1. PRE-FLIGHT CHECKS
# --------------------
# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your local secrets."
    exit 1
fi

# Check if docker-compose.dev.yml exists
if [ ! -f "docker-compose.dev.yml" ]; then
    echo -e "${RED}Error: docker-compose.dev.yml not found!${NC}"
    echo "Please ensure you have created the development compose file."
    exit 1
fi

# 2. CLEANUP (Optional)
# ---------------------
# Stops any currently running containers to avoid port conflicts
echo -e "${GREEN}[1/2] Stopping any existing containers...${NC}"
docker compose -f docker-compose.dev.yml down --remove-orphans

# 3. BUILD & RUN
# --------------
echo -e "${GREEN}[2/2] Building and Starting Containers...${NC}"
echo -e "Backend will run at: http://localhost:8000"
echo -e "Frontend will run at: http://localhost:80"
echo -e "${CYAN}Press Ctrl+C to stop the server.${NC}"

# Run with --build to force a rebuild of images (ensures changes are picked up)
# We do NOT use -d (detached) so you can see the logs in your terminal.
docker compose -f docker-compose.dev.yml up -d --build