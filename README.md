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

* **Frontend:** [http://localhost](https://www.google.com/search?q=http://localhost) (Updates instantly when you save files)
* **Backend Admin:** [http://localhost:8000/admin/](https://www.google.com/search?q=http://localhost:8000/admin/)

### Step 3: Database Management (Local)

Run these commands inside the Docker container to manage your local database.

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

## 2. Remote Deployment Setup (with SSL)

Use this workflow to deploy your application to the Duke VM with HTTPS enabled.

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

The `deploy.sh` script handles the entire pipeline:

1. **Builds** your images (specifically for Linux/AMD64 architecture).
2. **Pushes** them to Docker Hub.
3. **Copies** your config (`docker-compose.yml` and `.env`) to the VM.
4. **Restarts** the containers on the VM.

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

### View DB
Local: `docker compose -f docker-compose.dev.yml exec backend python manage.py inspectdb`
Remote: `docker exec -it book-app-deployment-backend-1 python manage.py inspectdb`
### View Logs
Local: `docker compose -f docker-compose.dev.yml logs -f backend` (can also view frontend)
Remote: `docker logs -f book-app-deployment-backend-1` (can also view frontend)

### Verification

* **Public URL:** `https://vcm-51984.vm.duke.edu`
* **Admin Panel:** `https://vcm-51984.vm.duke.edu/admin/`

* **Secure URL:** [https://vcm-51984.vm.duke.edu](https://www.google.com/search?q=https://vcm-51984.vm.duke.edu)
* You should see the padlock icon 🔒.

* **HTTP Redirect:** Visiting `http://vcm-51984.vm.duke.edu` should automatically redirect you to HTTPS.

### Key Differences in Production

* **Static Files:** In production (`docker-compose.yml`), Django uses `collectstatic` and WhiteNoise to serve CSS/JS files efficiently, whereas local dev serves them on the fly.
* **Volumes:** Code changes in production require a re-deploy (running `./deploy.sh`) to take effect. They do not hot-reload.


## 3. Running Tests (Backend)

The backend uses pytest + pytest-django to run automated tests for API endpoints and application logic. Tests are executed inside the Docker backend container to ensure the environment matches production dependencies.

---

### Prerequisites

Make sure your local development environment is running:

./dev.sh

Verify the backend container is running:

docker compose -f docker-compose.dev.yml ps

You should see a running `backend` service.

---

### Run All Tests

To run the entire test suite:

docker compose -f docker-compose.dev.yml exec backend pytest

For quieter output:

docker compose -f docker-compose.dev.yml exec backend pytest -q

---

### Run Tests From a Specific File

To run only one test file (example: Books API tests):

docker compose -f docker-compose.dev.yml exec backend pytest bookapp/tests/test_books_api.py

---

### Run a Single Test Function

To run one specific test:

docker compose -f docker-compose.dev.yml exec backend pytest -k test_post_duplicate_isbn_13_returns_400

The `-k` flag filters tests by name.

---

### Important Notes About Testing

- Tests use a temporary test database that is automatically created and destroyed.
- Your real development or production data is never modified.
- Database migrations are applied automatically to the test database.
- Each test runs in isolation using database transactions.
- Authentication is mocked internally using DRF’s APIClient.force_authenticate.

---

### Common Issues

pytest command not found

Make sure pytest and pytest-django are installed in the backend image:

pip install pytest pytest-django

Then rebuild:

docker compose -f docker-compose.dev.yml build backend

---

Permission denied creating test database

If Postgres permissions fail, reset local volumes:

docker compose -f docker-compose.dev.yml down -v
./dev.sh

---

### Example Successful Output

When tests pass, you should see:

........
8 passed in 2.8s

---
    