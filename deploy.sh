#!/bin/bash

# ==========================================
# CONFIGURATION
# ==========================================
HUB_USER="judyhe19" 
NETID="yh381"                  
VM_HOST="vcm-51984.vm.duke.edu"
PROJECT_DIR="~/book-app-deployment"       # Directory on VM to store config

# Image Names
IMG_BACKEND="$HUB_USER/book-app-backend:latest"
IMG_FRONTEND="$HUB_USER/book-app-frontend:latest"

# Colors for pretty output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Starting Deployment Pipeline...${NC}"

# ==========================================
# 1. BUILD
# ==========================================
echo -e "${GREEN}[1/4] Building Docker Images...${NC}"

# Build Backend (Force AMD64 for the server)
echo "Building Backend..."
docker build --platform linux/amd64 -t $IMG_BACKEND ./src/django-backend
if [ $? -ne 0 ]; then echo "Backend build failed"; exit 1; fi

# Build Frontend (Force AMD64 for the server)
echo "Building Frontend..."
docker build --platform linux/amd64 -t $IMG_FRONTEND ./src/react-frontend
if [ $? -ne 0 ]; then echo "Frontend build failed"; exit 1; fi

# ==========================================
# 2. PUSH
# ==========================================
echo -e "${GREEN}[2/4] Pushing Images to Docker Hub...${NC}"

echo "Pushing Backend..."
docker push $IMG_BACKEND
if [ $? -ne 0 ]; then echo "Backend push failed. Did you run 'docker login'?"; exit 1; fi

echo "Pushing Frontend..."
docker push $IMG_FRONTEND
if [ $? -ne 0 ]; then echo "Frontend push failed"; exit 1; fi

# ==========================================
# 3. CONFIGURE REMOTE SERVER
# ==========================================
echo -e "${GREEN}[3/4] Updating Configuration on Remote Server...${NC}"

# Create directory on VM if it doesn't exist
ssh $NETID@$VM_HOST "mkdir -p $PROJECT_DIR"

# Copy BOTH the compose file and the .env file
scp docker-compose.yml .env $NETID@$VM_HOST:$PROJECT_DIR/

# ==========================================
# 4. DEPLOY
# ==========================================
echo -e "${GREEN}[4/4] Restarting Containers on Remote Server...${NC}"

# Run docker-compose on the VM
ssh $NETID@$VM_HOST "cd $PROJECT_DIR && docker-compose down && docker-compose up -d --pull always"

echo -e "${CYAN}Deployment Complete!${NC}"
echo -e "Visit: http://$VM_HOST"