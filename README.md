# Tax Billing Application

A simple accounting and billing software for small businesses in Canada. The primary focus is tracking client billing, creating invoices and calculating tax holdbacks (HST and Income Tax).

## Features

- **Client Management**: Add, edit, and manage client information
- **Invoice Creation**: Create and edit invoices with automatic tax calculation
- **PDF Invoice Generation**: Generate clean, printable PDF invoices
- **Payment Tracking**: Record and track payments against invoices
- **Tax Reserve Dashboard**: See how much to set aside for HST and income tax
- **Editable Tax Brackets**: Configure federal and provincial tax rates in Settings
- **SQL Database Backup**: Full PostgreSQL backup with restore capability

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| PDF Generation | WeasyPrint |
| Frontend | Flet (Python) |
| Containerization | Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### 1. Clone and Start

```bash
# Clone the repository
git clone <repository-url>
cd tax-billing

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d
```

### 2. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Initial Setup

1. Go to **Settings** in the frontend
2. Configure your business information:
   - Business name
   - Address
   - Province (determines your tax rates)
   - HST/GST number
   - Payment terms and instructions
3. Configure tax brackets for your province

## Project Structure

```
tax-billing/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   └── templates/           # Invoice HTML template
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── main.py                  # Flet application
│   ├── views/                   # UI views
│   ├── services/                # API client
│   ├── requirements.txt
│   └── Dockerfile
├── database/
│   ├── schema.sql               # Database schema
│   └── seed_data.sql            # Tax rates seed data
├── docker-compose.yml
└── README.md
```

## API Endpoints

All endpoints follow GC (Government of Canada) API Standards:
- RESTful resource paths (nouns, not verbs)
- JSON responses
- Standard HTTP status codes

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Clients** |||
| GET | `/v1/clients` | List all clients |
| POST | `/v1/clients` | Create client |
| GET | `/v1/clients/{id}` | Get client |
| PUT | `/v1/clients/{id}` | Update client |
| DELETE | `/v1/clients/{id}` | Soft delete client |
| **Invoices** |||
| GET | `/v1/invoices` | List invoices |
| POST | `/v1/invoices` | Create invoice |
| GET | `/v1/invoices/{id}` | Get invoice |
| PUT | `/v1/invoices/{id}` | Update invoice |
| PATCH | `/v1/invoices/{id}/status` | Update status |
| GET | `/v1/invoices/{id}/pdf` | Download PDF |
| **Payments** |||
| GET | `/v1/payments` | List payments |
| POST | `/v1/payments` | Record payment |
| DELETE | `/v1/payments/{id}` | Delete payment |
| **Tax** |||
| GET | `/v1/tax/summary` | Tax Reserve Dashboard |
| GET | `/v1/tax/rates/{year}` | Get tax rates |
| PUT | `/v1/tax/year-settings/{year}` | Update presumed income |
| POST | `/v1/tax/federal-brackets` | Create federal bracket |
| PUT | `/v1/tax/federal-brackets/{id}` | Update federal bracket |
| DELETE | `/v1/tax/federal-brackets/{id}` | Delete federal bracket |
| POST | `/v1/tax/provincial-brackets` | Create provincial bracket |
| PUT | `/v1/tax/provincial-brackets/{id}` | Update provincial bracket |
| DELETE | `/v1/tax/provincial-brackets/{id}` | Delete provincial bracket |
| **Settings** |||
| GET | `/v1/settings` | Get business settings |
| PUT | `/v1/settings` | Update settings |
| GET | `/v1/settings/provinces` | List provinces |
| **Backup** |||
| GET | `/v1/backup/download` | Download SQL backup |
| POST | `/v1/backup/restore` | Restore from SQL file |

## Tax Calculation Logic

### HST/GST Holdback
- **100%** of all HST/GST collected on **paid** invoices
- This is the full amount you need to remit to CRA

### Income Tax Holdback
Based on progressive tax brackets (federal + provincial):

1. **Presumed Annual Income**: Set this at the start of the year as your expected income
2. **Year-to-Date Income**: Actual paid revenue
3. **Projected Annual Income**: MAX(presumed income, annualized YTD)
4. **Tax Calculation**: Apply federal + provincial brackets to projected income
5. **Holdback**: Proportional share based on YTD income

### 2026 Federal Tax Brackets (Default)
| Income Range | Rate |
|-------------|------|
| $0 - $58,523 | 14.0% |
| $58,523 - $117,045 | 20.5% |
| $117,045 - $181,440 | 26.0% |
| $181,440 - $258,482 | 29.0% |
| Over $258,482 | 33.0% |

*Tax brackets are editable in Settings.*

## Backup & Restore

Backups use PostgreSQL's native `pg_dump` format for complete database portability.

### Create a Backup
1. Go to **Settings** → **Database Backup & Restore**
2. Click **Download Backup**
3. A `.sql` file will be downloaded to your computer

### Restore from Backup
1. Go to **Settings** → **Database Backup & Restore**
2. Click **Restore from Backup**
3. Select your `.sql` backup file
4. ⚠️ This will **replace all current data** with the backup

### Manual Backup via CLI
```bash
docker compose exec db pg_dump -U postgres -d tax_billing > backup.sql
```

### Manual Restore via CLI
```bash
docker compose exec -T db psql -U postgres -d tax_billing < backup.sql
```

## Development

### Running Locally Without Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
pip install -r requirements.txt
flet run main.py --port 8080
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### Rebuilding After Changes

```bash
docker compose build
docker compose up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@db:5432/tax_billing` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `change-this-secret-in-production` |
| `DEBUG` | Enable debug mode | `false` |
| `API_URL` | Backend URL for frontend | `http://backend:8000` |

## Invoice PDF Template

The invoice template is located at `backend/app/templates/invoice.html`. You can customize:
- Colors and fonts
- Layout and spacing
- Footer text

The template uses Jinja2 templating with WeasyPrint for PDF generation.

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Database not ready: Wait for PostgreSQL to initialize
# - Missing dependencies: Rebuild with `docker compose build backend`
```

### Frontend can't connect to backend
```bash
# Ensure backend is running
docker compose ps

# Check API is accessible
curl http://localhost:8000/health
```

### Database reset
```bash
# Remove all data and start fresh
docker compose down -v
docker compose up -d
```

## License

MIT License - See LICENSE file for details.
