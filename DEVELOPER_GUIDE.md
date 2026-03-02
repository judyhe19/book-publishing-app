# Developer Guide

## 1. High-Level System Construction

- **Frontend**: We built the frontend using React. It handles the user interface and interacts with the backend via a REST API. It is served using Vite for development and built for production.
- **Backend**: A Django application using the Django REST Framework (DRF) to provide API endpoints. It manages data validation, business logic, database interactions, and authentication.
- **Database**: PostgreSQL is used as the relational database.
- **Infrastructure**: The application is containerized using Docker and Docker Compose. Nginx is used as a reverse proxy in production to serve static files and proxy API requests.

### Architecture Outline (Conceptual)

```mermaid
graph TD
    Client[Browser] -->|HTTP/HTTPS| Nginx[Nginx Reverse Proxy]
    Nginx -->|/api| Backend[Django Backend]
    Nginx -->|/| Frontend[React Frontend]
    Backend -->|Read/Write| DB[(PostgreSQL)]
```

## 2. Technologies Used

### Frontend

- **Framework**: React 19
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **Routing**: React Router 7
- **State/UI Libraries**: React Select, React Datepicker
- **Linting**: ESLint

### Backend

- **Framework**: Django 5.2
- **API Framework**: Django REST Framework (DRF)
- **Language**: Python 3
- **Database Interface**: psycopg2-binary
- **Server**: Gunicorn (Production), Django Development Server (Local)
- **Static Files**: WhiteNoise
- **Testing**: pytest, pytest-django

### Infrastructure & Tools

- **Containerization**: Docker, Docker Compose
- **Production Server**: Nginx
- **Database**: PostgreSQL

## 3. Development Environment Setup

We use Docker Compose to create a consistent development environment.

### Prerequisites

- **Docker Desktop** (or Docker Engine + Compose)
- **Git**

### Quick Start (Local Development)

1.  **Configure Environment**:
    Create a `.env` file in the root directory (see `README.md` for template).

2.  **Start the Application**:
    Use the helper script to start the development environment:

    ```bash
    ./dev.sh
    ```

    This script runs `docker-compose -f docker-compose.dev.yml up --build`.

3.  **Access the App**:
    - Frontend: `http://localhost`
    - Backend Admin: `http://localhost:8000/admin/`

### Common Commands

- **Run Backend Tests**:
  ```bash
  docker compose -f docker-compose.dev.yml exec backend pytest
  ```
- **Make Migrations**:
  ```bash
  docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations
  ```
- **Apply Migrations**:
  ```bash
  docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
  ```
- **Create Superuser**:
  ```bash
  docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
  ```

For detailed setup and deployment instructions, please examine the `README.md` file in the project root.

## 4. Database Schema

The core data model revolves around Books, Authors, and Sales. The schema is defined in `src/django-backend/bookapp/models.py`.

Each book has exactly **one** author (a direct foreign key). Royalty rates are stored on the book, not on a join table.

### Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    AUTHOR ||--o{ BOOK : writes
    BOOK ||--o{ SALE : generates

    AUTHOR {
        int id PK
        string name
        string email
    }

    BOOK {
        int id PK
        int author_id FK
        string title
        date publication_date
        string isbn_13
        string isbn_10
        decimal cover_price
        decimal print_cost
        decimal distributor_author_royalty_rate
        decimal hand_sold_author_royalty_rate
        string series_name
        int series_position
        string cover_image_path
    }

    SALE {
        int id PK
        int book_id FK
        date date
        int quantity
        string sale_source
        decimal publisher_revenue
        decimal author_royalty
        boolean author_paid
        string comment
    }
```

### Table Details

1.  **Author**
    - Represents a book author.
    - `name`: Unique.
    - `email`: Optional.

2.  **Book**
    - Represents a published book. Each book belongs to exactly one author.
    - `isbn_13`: 13-digit ISBN (unique, validated).
    - `isbn_10`: 10-digit ISBN (optional, validated).
    - `cover_price` / `print_cost`: Used to compute publisher revenue for handsold sales.
    - `distributor_author_royalty_rate`: Royalty rate applied to distributor sales.
    - `hand_sold_author_royalty_rate`: Royalty rate applied to handsold sales.
    - `series_name` / `series_position`: Optional. When set, both must be present and `(series_name, series_position)` must be unique. Series positions are automatically compacted on insert and delete.
    - `cover_image_path`: Optional path to the cover image file.
    - `total_sales_to_date`: Not a stored column — computed at query time via a `Sum` annotation on related `Sale.quantity` records. Returned as a read-only field by the API.

3.  **Sale**
    - Represents a single sales record for a book.
    - `sale_source`: Either `"distributor"` or `"handsold"`.
    - `publisher_revenue`: For distributor sales, provided by the user. For handsold sales, computed as `(cover_price − print_cost) × quantity`.
    - `author_royalty`: Computed at write time as `publisher_revenue × royalty_rate` (rate chosen based on `sale_source`). Stored as a snapshot — unaffected by future rate changes on the book.
    - `author_paid`: Boolean, tracks whether the author has been paid for this specific sale.
    - `comment`: Optional free-text field (max 256 characters). Populated automatically on Ingram CSV imports.

### Key Logic Flow

- Each `Book` stores two royalty rates (distributor and handsold) directly — there is no join table.
- When a `Sale` is created or updated, `author_royalty` is computed and stored as `publisher_revenue × royalty_rate`. This snapshot means historical royalty figures are unaffected if rates are later changed.
- For handsold sales, `publisher_revenue` is computed server-side from `(cover_price − print_cost) × quantity`; the client-provided value is ignored.
- Payment status is tracked per-sale via `author_paid`. Authors can be batch-paid (all unpaid sales marked paid at once) or individually.

## 5. Production Deployment

The application is deployed to a Duke VM using Docker Compose and Nginx with SSL (Let's Encrypt).

### Prerequisites

- **Access**: SSH access to the target VM.
- **Docker Hub**: Account to push images (configured in `deploy.sh`).
- **VM Setup**: Docker and Docker Compose must be installed on the VM.

### Deployment Process

We use the `deploy.sh` script to automate the pipeline. This script:

1.  **Builds** the Docker images (specifically for `linux/amd64` architecture).
2.  **Pushes** the images to Docker Hub.
3.  **Copies** configuration files (`docker-compose.yml`, `.env`) to the VM via SCP.
4.  **Restarts** the application on the VM.

### Routine Deployment

To deploy the latest code from your local machine:

1.  Ensure you are logged into Docker Hub: `docker login`
2.  Run the deployment script:
    ```bash
    ./deploy.sh
    ```

### Production Database Management

To perform administrative tasks on the production database, you must SSH into the VM and execute commands inside the running container.

**Example: Running Migrations**

```bash
# 1. SSH into the VM
ssh <your-netid>@<vm-host>

# 2. Run migrate command inside the backend container
# Note: The container name usually tracks the folder name, e.g., 'book-publishing-app-backend-1'
# Use 'docker ps' to confirm the exact name.
docker exec -it book-app-deployment-backend-1 python manage.py migrate
```

**Example: creating a Superuser**

```bash
docker exec -it book-app-deployment-backend-1 python manage.py createsuperuser
```

For information on the one-time SSL setup using `init-letsencrypt.sh`, refer to the `README.md`.
