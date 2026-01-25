# Book Publishing App - Setup Guide

## 1. Local Development Setup
Use this workflow to run the application on your own machine for testing and development.

### Prerequisites
* **Docker Desktop** installed and running.
* **Git** installed.

### Step 1: Configuration
Create a `.env` file in the project root directory.

```bash
# .env
# Database Credentials
POSTGRES_DB=book-app
POSTGRES_USER=judy (change this to your username)
POSTGRES_PASSWORD=12345 (change this to your password)
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django Settings
DJANGO_SECRET_KEY=django-insecure-8+2^ikp4y+1u6@&70=f@mekqy-dmfa(4ia@4mhw$1mvqm!-0h8
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend

```

### Step 2: Start the Environment

We use the `dev.sh` helper script to automate the Docker commands. This script uses `docker-compose.dev.yml` with hot-reloading enabled.

**Make the script executable (first time only):**

```bash
chmod +x dev.sh

```

**Run the server:**

```bash
./dev.sh

```

* **Frontend:** [http://localhost](https://www.google.com/search?q=http://localhost) (Updates instantly when you save files)
* **Backend Admin:** [http://localhost:8000/admin/](https://www.google.com/search?q=http://localhost:8000/admin/)

### Step 3: Database Management (Local)

Run these commands inside the Docker container to manage your local database.

**Make Migrations:**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations

```

**Run Migrations:**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

```

**Create Superuser:**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

```

---

## 2. Remote Deployment Setup (with SSL)

Use this workflow to deploy your application to the Duke VM with HTTPS enabled.

### Prerequisites

* **SSH Access** to your Duke VM (`vcm-xxxxx.vm.duke.edu`).
* **Docker Hub Account**.
* **Docker** installed on the VM.

### Step 1: Configure Deployment Script

Open `deploy.sh` and ensure the variables match your setup:

```bash
HUB_USER="judyhe19"              # Your Docker Hub username
NETID="yh381"                    # Your Duke NetID
VM_HOST="vcm-51984.vm.duke.edu"  # Your VM Address

```

### Step 2: One-Time SSL Setup

You must perform this setup **once** to generate the initial certificates.

1. **Create the Init Script:**
Create a file named `init-letsencrypt.sh` in your project root (content provided in the implementation guide).
2. **Copy Script to Server:**
```bash
scp init-letsencrypt.sh yh381@vcm-51984.vm.duke.edu:~/book-app-deployment/

```


3. **Run Initialization on Server:**
SSH into the VM and run the script. This will start Nginx, request certificates from Let's Encrypt, and reload the server.
```bash
ssh yh381@vcm-51984.vm.duke.edu
cd ~/book-app-deployment
chmod +x init-letsencrypt.sh
sudo ./init-letsencrypt.sh

```



### Step 3: Routine Deployment

For all future code updates, simply use the deployment script. It handles building, pushing, and restarting the containers.

```bash
# Ensure you are logged in to Docker Hub
docker login

# Deploy updates
./deploy.sh

```

### Step 4: Remote Database Management

To run commands on the **production** database, use SSH.

**SSH into the VM:**

```bash
ssh yh381@vcm-51984.vm.duke.edu

```

**Run Migrations (Remote):**

```bash
cd ~/book-app-deployment
# Use the production container name (check 'docker ps' if unsure)
docker exec -it book-app-deployment-backend-1 python manage.py migrate

```

**Create Remote Superuser:**

```bash
docker exec -it book-app-deployment-backend-1 python manage.py createsuperuser

```

### Verification

* **Secure URL:** [https://vcm-51984.vm.duke.edu](https://www.google.com/search?q=https://vcm-51984.vm.duke.edu)
* You should see the padlock icon 🔒.


* **HTTP Redirect:** Visiting `http://vcm-51984.vm.duke.edu` should automatically redirect you to HTTPS.
