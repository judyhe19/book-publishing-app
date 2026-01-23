# Book Publishing App

# Rules
* Only run `./deploy.sh` on `main` branch to deploy to VM (production)
* Only run `./dev.sh` on `dev` branch to deploy to local (development)

# Setup Guide

## 1. Local Development Setup
Use this workflow to run the application on your own machine (Mac/Windows/Linux) for testing and development.

### Prerequisites
* **Docker Desktop** installed and running.
* **Git** installed.

### Step 1: Configuration
Create a `.env` file in the project root directory. This file holds your secrets and configuration.

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
DJANGO_ALLOWED_HOSTS=vcm-51984.vm.duke.edu,localhost,127.0.0.1,backend # change the VM host to your own Duke VM host
```

### Step 2: Start the Environment

We use the `dev.sh` helper script to automate the Docker commands. This script uses `docker-compose.dev.yml`, which mounts your code as volumes (so changes happen instantly) and enables hot-reloading.

**Make the script executable (first time only):**

```bash
chmod +x dev.sh

```

**Run the server:**

```bash
./dev.sh

```

* **Frontend:** [http://localhost](https://www.google.com/search?q=http://localhost)
* **Backend Admin:** [http://localhost:8000/admin/](https://www.google.com/search?q=http://localhost:8000/admin/)

### Step 3: Database Management

When you modify `models.py`, you must update the database schema.

**Make Migrations (create the SQL files):**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations

```

**Run Migrations (apply to database):**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

```

**Create a Superuser (to log into Admin):**

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

```

### Troubleshooting Local Dev

* **Database connection errors?** If you changed the DB name or user recently, you may need to wipe the old volume:
```bash
docker compose -f docker-compose.dev.yml down -v

```


* **Docker command not found?** Ensure Docker Desktop is running.

---

## 2. Remote Deployment Setup

Use this workflow to deploy your application to the Duke VM.

### Prerequisites

* **SSH Access** to your Duke VM (`vcm-xxxxx.vm.duke.edu`).
* **Docker Hub Account** (to store your images).
* **Docker** installed on the VM and your user added to the `docker` group.

### Step 1: Configure Deployment Script

Open `deploy.sh` and ensure the variables at the top match your setup:

```bash
HUB_USER="judyhe19"              # Your Docker Hub username
NETID="yh381"                    # Your Duke NetID
VM_HOST="vcm-51984.vm.duke.edu"  # Your VM Address

```

### Step 2: Deploy

The `deploy.sh` script handles the entire pipeline:

1. **Builds** your images (specifically for Linux/AMD64 architecture).
2. **Pushes** them to Docker Hub.
3. **Copies** your config (`docker-compose.yml` and `.env`) to the VM.
4. **Restarts** the containers on the VM.

**Run the deployment:**

```bash
# Ensure you are logged in to Docker Hub first
docker login

# Run the script
./deploy.sh

```

### Step 3: Verification

* **Public URL:** `http://vcm-51984.vm.duke.edu`
* **Admin Panel:** `http://vcm-51984.vm.duke.edu/admin/`

### Step 4: Remote Database Management

To run commands on the **production** database, you use SSH.

**SSH into the VM:**

```bash
ssh yh381@vcm-51984.vm.duke.edu

```

**Run Migrations (Remote):**

```bash
cd ~/book-app-deployment
# Note: Use the production container name (check with 'docker ps')
docker exec -it book-app-deployment-backend-1 python manage.py migrate

```

**Create Remote Superuser:**

```bash
docker exec -it book-app-deployment-backend-1 python manage.py createsuperuser

```

### Key Differences in Production

* **Static Files:** In production (`docker-compose.yml`), Django uses `collectstatic` and WhiteNoise to serve CSS/JS files efficiently, whereas local dev serves them on the fly.
* **Volumes:** Code changes in production require a re-deploy (running `./deploy.sh`) to take effect. They do not hot-reload.


