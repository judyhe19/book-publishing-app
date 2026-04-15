# Deployment Guide

This document describes how to install and deploy the Book Publishing Application from scratch on a fresh server.

## 1. Platform Prerequisites

Before beginning, ensure you have a server environment ready.

- **Operating System**: Linux is recommended for production.
  - _Recommended Distribution_: Ubuntu 20.04 LTS or 22.04 LTS.
  - _Architecture_: x86_64 (amd64).
- **Hardware**:
  - Minimum: 1 vCPU, 2GB RAM.
  - Recommended: 2 vCPU, 4GB RAM or higher.
- **Network**:
  - Public IP address.
  - Ports 80 (HTTP) and 443 (HTTPS) open/allowed in the firewall.
  - Port 22 (SSH) for management.
- **Domain Name**:
  - A valid domain name configured with an `Address Record` pointing to your server's public IP.

## 2. Software Dependencies

The deployment model for this application involves a **Local Management Machine** (your laptop/dev machine) and a **Production Server** (the VM). You prepare requirements locally and use a script to deploy to the server.

### Part A: Server Preparation (One-Time)

Perform these steps on your remote server (VM).

1.  **Install Docker & Docker Compose**:
    The server needs Docker to run the application containers.

    ```bash
    # (Example for Ubuntu)
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose-v2
    sudo usermod -aG docker $USER
    # Log out and log back in for group changes to take effect
    ```

2.  **Create Deployment Directory**:
    Ensure the target directory exists (the deploy script will populate this).
    ```bash
    mkdir -p ~/book-app-deployment
    ```

### Part B: Local Setup

Perform these steps on your local machine.

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/judyhe19/book-publishing-app.git
    cd book-publishing-app
    ```

2.  **Configure Environment**:
    Create a `.env` file in the project root with your production secrets.

    ```bash
    cp .env.example .env
    nano .env
    ```

    _(See `README.md` for variable details. Ensure `DJANGO_DEBUG=False` for production.)_

3.  **Configure Deployment Script**:
    Edit `deploy.sh` to match your server details.

    ```bash
    nano deploy.sh
    ```

    Update the following variables at the top of the file:
    - `HUB_USER`: Your Docker Hub username.
    - `NETID`: Your username on the server (for SSH).
    - `VM_HOST`: The domain or IP of your server (e.g., `your-domain.com`).
    - `PROJECT_DIR`: Path where files should be copied (matches Part A, Step 2).

4.  **Login to Docker Hub**:
    You need to be authenticated to push the built images.
    ```bash
    docker login
    ```

## 3. Deployment

### Step 1: Run the Deployment Script

From your local machine, run the automated deployment script.

```bash
./deploy.sh
```

This script will automatically:

1.  **Build** the Backend and Frontend Docker images (platform `linux/amd64`).
2.  **Push** the images to Docker Hub.
3.  **Copy** configuration files (`docker-compose.yml`, `.env`) to the server via SCP.
4.  **Restart** the application on the server via SSH.

### Step 2: SSL Certificate Setup (First Deploy Only)

Because SSL setup requires specific one-time validation, you must run the initialization script manually on the server.

1.  **Copy the Init Script to Server**:

    ```bash
    # From local machine
    scp init-letsencrypt.sh <user>@<server-host>:~/book-app-deployment/
    ```

2.  **Run the Init Script on Server**:
    SSH into your server and run the script.

    ```bash
    ssh <user>@<server-host>
    cd ~/book-app-deployment

    # Edit script to set your domain and email
    nano init-letsencrypt.sh

    # Run it
    chmod +x init-letsencrypt.sh
    ./init-letsencrypt.sh
    ```

    _Note: The `deploy.sh` script does not perform this step to avoid accidental rate-limiting or overwriting of certificates._

## 4. System Verification

After `deploy.sh` completes:

1.  **Automatic Migrations & Admin User**:
    The backend container automatically applies database migrations and creates/updates the superuser (defined in `.env`) every time it starts. No manual action is needed.

2.  **Check Site**:
    Visit `https://your-domain.com`.

3.  **Check Admin**:
    Visit `https://your-domain.com/admin` to log in.

## 5. Maintenance

- **Logs**: `sudo docker compose logs -f` (Run on server)
- **Update**:
  Simply run `./deploy.sh` from your local machine again.

## 6. Disaster Recovery (Restore from Backup)

This section is for using previously backed up data instead of starting with empty/default data.

This should be used in scenarios such as:
- Server failure
- Data loss
- Migration to a new VM

### 6.1 Prerequisites

Before performing a restore, the system must already be deployed:

- Complete **Sections 1–5** of this guide
- Application must be running on the production server
- Backup system must be configured and accessible

### 6.2 Restore Procedure

To restore the system from a backup, follow the instructions in the [**Restore & Backup Validation Guide.**](./backups/restore_backup.md)

This includes:
- Selecting a snapshot
- Verifying backup integrity
- Restoring the database and static files
- Restarting the application
- Validating the restored system

## 7. Whitelabel

This application supports white-labeling via server-side configuration, allowing the publisher name, application title, logo, and favicon to be changed without modifying any source code.

### 7.1 Overview

Branding is controlled through:
- Environment variables in the `.env` file
- Image files placed in `~/book-app-deployment/branding/` on the VM

The `branding/` folder is mounted directly into the backend container, so files placed there are immediately available after a restart. The frontend fetches branding from the backend at runtime, so no frontend rebuild is needed.

### 7.2 Copy Your Logo to the VM

From your **local machine** (not SSH’d into the VM), run:

```bash
scp "C:\Users\YourName\Downloads\yourlogo.png" NETID@vcm-XXXXX.vm.duke.edu:~/book-app-deployment/branding/yourlogo.png
```

Replace `YourName`, `NETID`, `vcm-XXXXX`, and `yourlogo.png` with your actual values.

The `branding/` folder is created automatically when you run `deploy.sh`.

### 7.3 Update the .env File

SSH into the VM and edit the `.env` file:

```bash
ssh NETID@vcm-XXXXX.vm.duke.edu
nano ~/book-app-deployment/.env
```

Update the following fields to match your publisher name and logo filename:

```bash
PUBLISHER_NAME=Your Publisher Name
APP_TITLE=Your App Title
PUBLISHER_LOGO_PATH=/static/img/branding/yourlogo.png
PUBLISHER_FAVICON_PATH=/static/img/branding/yourlogo.png
```

### 7.4 Restart the Application

After updating the `.env` file and/or branding images, restart the application from the VM:

```bash
cd ~/book-app-deployment
docker compose down
docker compose up -d
```

### 7.5 Result

After restarting:
- The navbar will display the new publisher name and logo
- The browser tab title will update
- The favicon will update
- All branding will reflect the new publisher configuration

Branding images persist across restarts because `branding/` is a bind-mounted folder on the VM — not stored inside the container.