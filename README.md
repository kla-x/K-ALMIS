# K-ALMIS
## Kenya Asset & Liability Management Information System

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Free_with_Attribution-green?style=for-the-badge)](LICENSE)

**A comprehensive Asset and Liability Management Information System tailored specifically for the Kenyan public sector**

[Features](#-key-features) • [Installation](#-installation) • [Documentation](#-api-documentation) • [Contributing](#-contributing) • [Support](#-support)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Database Setup](#-database-setup)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Security Features](#-security-features)
- [Modules & Endpoints](#-modules--endpoints)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 🎯 Overview

K-ALMIS is designed to help Kenyan public sector entities efficiently manage their assets and liabilities in compliance with:

- **Public Finance Management (PFM) Act, 2012**
- **Public Procurement and Asset Disposal (PPAD) Act, 2015**
- **International Public Sector Accounting Standards (IPSAS)**
- **Kenya's National Treasury Guidelines** - [View Guidelines](https://newsite.treasury.go.ke/sites/default/files/NALM/General-Guidelines-on-asset-and-liability-management-2020-Final.pdf)

The system provides complete lifecycle management for assets from acquisition through disposal, with robust tracking, reporting, and compliance features.

---

## ✨ Key Features

### Asset Management

- **Complete Asset Lifecycle Management**: Planning, acquisition, operation, maintenance, and disposal
- **Asset Categorization**: Buildings, land, vehicles, ICT equipment, furniture, infrastructure (roads, railways), intangible assets, heritage assets, and more
- **Real-time Tracking**: QR code generation, barcode scanning, tag number tracking
- **Location Intelligence**: Integration with OpenStreetMap Nominatim for geocoding and reverse geocoding
- **Assignment Management**: Assign/reassign assets to users and departments with full history tracking
- **Transfer Workflow**: Multi-step approval process for asset transfers between departments/entities

### Maintenance Management

- **Maintenance Scheduling**: Plan preventive and corrective maintenance
- **Issue Tracking**: Categorize issues by severity and priority
- **Maintenance History**: Complete audit trail of all maintenance activities
- **Cost Analysis**: Track maintenance costs and analyze trends

### Disposal Management

- **Disposal Workflow**: Initiate, schedule, approve, and execute disposal processes
- **Compliance**: Follow PPAD Act 2015 disposal requirements
- **Disposal Methods**: Support for various disposal methods (public tender, auction, trade-in, transfer, etc.)
- **Audit Trail**: Complete history of disposal activities

### Security & Authentication

- **Advanced Authentication System**: Two authentication modules (basic + enhanced security)
- **Multi-Factor Authentication (MFA)**: 6-digit code with configurable expiry (20 minutes)
- **Device Fingerprinting**: Track and manage trusted devices
- **Rate Limiting**:
  - Known devices: 5 failed attempts before lock
  - Unknown devices: 2 failed attempts before lock
- **IP Whitelisting**: Automatic whitelisting after threshold (2 attempts)
- **Account Protection**:
  - Temporary account disabling (24 hours)
  - Password expiry (90 days)
  - Inactive account detection (60 days)
  - Fraud score monitoring (limit: 70)
- **Session Management**: Temporary sessions with 30-minute expiry
- **Working Hours Validation**: Monitor login attempts during business hours (8 AM - 5 PM EAT)
- **Login History**: Complete audit trail of authentication events

### User & Role Management

- **Role-Based Access Control (RBAC)**: Define roles with specific permissions
- **Attribute-Based Access Control (ABAC)**: Fine-grained permission control
- **Multi-Tenancy**: Support for multiple government entities (counties, departments)
- **Department Hierarchy**: Manage organizational structures
- **User Profiles**: Comprehensive user management with status controls

### Geographic Integration

- **Kenya Administrative Units**: Pre-loaded with 47 counties, constituencies, and wards
- **Location Search**: Search across counties, constituencies, and wards
- **Geocoding Services**: Forward and reverse geocoding via OpenStreetMap
- **Coordinate-based Search**: Reverse geocode coordinates to addresses

### Reporting & Analytics

- **Executive Dashboard**: High-level summary for decision-makers
- **Asset Reports**:
  - Summary dashboard
  - Depreciation reports
  - Status and condition analysis
  - Category-specific reports
  - Age analysis
  - Utilization metrics
- **Department Reports**: Asset distribution and comparison across departments
- **Maintenance Reports**: Summary, upcoming tasks, backlogs, cost analysis
- **Compliance Reports**: Missing data, geographic distribution
- **Security Reports**: Activity logs, failed login attempts, data modifications
- **Transfer & Disposal Reports**: Pending approvals, historical data

### Notifications & Communication

- **Email Notifications**: Automated notifications via Sendinblue/Brevo API
- **Activity Triggers**:
  - Asset assignments/transfers
  - Maintenance schedules
  - Disposal approvals
  - Password resets
  - Security alerts
  - Account unlock requests

### System Logging

- **Comprehensive Audit Trail**: All system activities logged
- **User Activity Tracking**: Monitor user actions across the system
- **Security Event Logging**: Failed logins, suspicious activities
- **Data Modification History**: Track all changes to assets and records

---

## 🛠 Technology Stack

### Backend Framework

- **FastAPI 0.116.1**: Modern, fast web framework for building APIs
- **Python 3.8+**: Core programming language
- **Uvicorn**: ASGI server with standard support

### Database & ORM

- **PostgreSQL**: Primary database
- **SQLAlchemy 2.0.43**: SQL toolkit and ORM
- **Alembic 1.16.4**: Database migration tool

### Authentication & Security

- **python-jose 3.5.0**: JWT token handling
- **passlib 1.7.4**: Password hashing
- **bcrypt 4.3.0**: Secure password hashing algorithm
- **Redis 6.4.0**: Session management and caching

### Background Jobs

- **APScheduler**: Task scheduling for maintenance reminders, depreciation calculations
- **RQ 2.5.0**: Python job queue for async tasks
- **Croniter 6.0.0**: Cron expression parser

### External Services

- **Sendinblue (Brevo) API**: Email notifications
- **Cloudinary**: File storage (documents, images, QR codes)
- **OpenStreetMap Nominatim**: Geocoding services
- **AbuseIPDB**: IP reputation checking

### Other Libraries

- **Pydantic 2.11.7**: Data validation
- **QRCode**: QR code generation
- **Python-multipart**: File upload handling
- **Requests**: HTTP client for external APIs
- **Pytz 2025.2**: Timezone support (East Africa Time)

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                       │
│              (Web, Mobile, Desktop Clients)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication Layer (MFA, Device Fingerprinting)    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │  Authorization (RBAC + ABAC)                          │  │
│  └──────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │           Business Logic Layer                        │  │
│  │  • Asset Management    • Transfer Management          │  │
│  │  • Maintenance         • Disposal Management          │  │
│  │  • Department Mgmt     • Reporting & Analytics        │  │
│  └──────────────────────┬───────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐    ┌──────────┐
   │PostgreSQL│    │  Redis   │    │Cloudinary│
   │Database  │    │  Cache   │    │  Storage │
   └─────────┘    └──────────┘    └──────────┘
         │
         ▼
   ┌──────────┐
   │ Scheduled│
   │  Jobs    │
   │(APScheduler)│
   └──────────┘
```

---

## 📦 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+
- Redis Server (for session management and caching)
- Cloudinary Account (for file storage)
- Sendinblue/Brevo Account (for email notifications)
- Git

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kla-x/K-ALMIS.git
cd K-ALMIS
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### Requirements.txt

```txt
alembic==1.16.4
annotated-types==0.7.0
anyio==4.10.0
bcrypt==4.3.0
click==8.2.1
croniter==6.0.0
dotenv==0.9.9
ecdsa==0.19.1
fastapi==0.116.1
greenlet==3.2.4
idna==3.10
Mako==1.3.10
MarkupSafe==3.0.2
passlib==1.7.4
psycopg2-binary==2.9.10
pyasn1==0.6.1
pydantic==2.11.7
uvicorn[standard]
pydantic[email]
python-multipart
pydantic_core==2.33.2
python-dateutil==2.9.0.post0
python-dotenv==1.1.1
python-jose==3.5.0
pytz==2025.2
redis==6.4.0
rq==2.5.0
rsa==4.9.1
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.43
starlette==0.47.2
typing-inspection==0.4.1
qrcode
typing_extensions==4.14.1
requests
sib_api_v3_sdk
apscheduler
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=kalmis_db

# Email Configuration (Sendinblue/Brevo)
SENDINBLUE_API_KEY=xkeysib-your-api-key-here
SENDER_EMAIL=noreply@yourdomain.com
SENDER_NAME=K-ALMIS System

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:5173

# Security Keys
SECRET_KEY=your-secret-key-here-min-32-chars
SECRET_KEY_FP=your-fingerprint-secret-key-here

# IP Reputation Service
ABUSEDB_KEY=your-abuseipdb-api-key

# Redis Configuration (optional, defaults to localhost)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Security Settings (optional - these are defaults)
KNOWN_DEVICE_MAX_ATTEMPTS=5
UNKNOWN_DEVICE_MAX_ATTEMPTS=2
UNLOCK_ACCOUNT_TOKEN_EXPIRY_MINUTES=60
TEMP_DISABLE_DURATION_HOURS=24
FINAL_ATTEMPTS_BEFORE_LOCK=2
PASSWORD_EXPIRY_DAYS=90
FRAUD_SCORE_LIMIT=70
WORKING_HOURS_START=8
WORKING_HOURS_END=17
EXPECTED_TIMEZONE=EAT
EXPECTED_LANGUAGE=en
IP_WHITELIST_THRESHOLD=2
MFA_CODE_EXPIRY_MINUTES=20
TEMP_SESSION_TOKEN_EXPIRY_MINUTES=30
INACTIVE_ACCOUNT_DAYS=60
MFA_CODE_LENGTH=6
```

### Configuration Notes

- **Database**: Ensure PostgreSQL is running and create the database specified in `DB_NAME`
- **Email Service**: Sign up for Sendinblue/Brevo to get an API key
- **Cloudinary**: Create account at Cloudinary for file storage
- **AbuseIPDB**: Optional but recommended for IP reputation checks
- **Secret Keys**: Generate secure random strings (32+ characters) for `SECRET_KEY` and `SECRET_KEY_FP`

### Generate Secret Keys

```bash
# Python one-liner to generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄 Database Setup

### 1. Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE kalmis_db;

# Create user (if needed)
CREATE USER kalmis_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE kalmis_db TO kalmis_user;

# Exit
\q
```

### 2. Initialize Alembic (First Time Setup)

If migrations folder doesn't exist:

```bash
alembic init alembic
```

### 3. Run Migrations

```bash
# Create initial migration (if not exists)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Load Initial Data

The system will automatically load:

- **Counties Data**: 47 Kenyan counties with constituencies and wards from `counties.json`
- **Asset Categories**: Pre-defined asset categories coded in the backend
- **System Roles**: Default roles and permissions

```bash
# Run the data seeding script
python scripts/seed_data.py
```

---

## 🏃 Running the Application

### Development Mode

```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With custom workers (production-like)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Background Workers

Start Redis and the job queue worker:

```bash
# Start Redis (in separate terminal)
redis-server

# Start RQ worker (in separate terminal)
rq worker
```

### Access Points

- **API Base URL**: http://localhost:8000
- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 📚 API Documentation

The system provides comprehensive auto-generated API documentation accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### API Structure

All API endpoints are versioned and prefixed with `/api/v1/`

### Authentication

Most endpoints require authentication via JWT Bearer token:

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token in subsequent requests
curl -X GET "http://localhost:8000/api/v1/assets/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔒 Security Features

### Authentication System

K-ALMIS implements a dual authentication system:

- **Basic Authentication** (`/api/v1/auth/`): Standard JWT-based authentication
- **Enhanced Authentication** (`/api/v1/auth/2/`): Advanced security features

### Enhanced Security Features

- **Device Fingerprinting**: Track and manage trusted devices
- **Rate Limiting**: Progressive lockout based on device trust
- **MFA (Multi-Factor Authentication)**: 6-digit codes sent via email
- **IP Whitelisting**: Automatic trust for frequently used IPs
- **Fraud Detection**: Score-based monitoring of suspicious activities
- **Working Hours Monitoring**: Track out-of-hours access attempts
- **Session Management**: Short-lived sessions with automatic expiry
- **Password Policies**:
  - Minimum complexity requirements
  - 90-day expiration
  - Force password change on first login
  - Secure reset via email tokens

### Security Configuration

All security parameters are configurable via environment variables. Default values provide a good balance between security and usability.

---

## 📂 Modules & Endpoints

### Authentication & User Management

#### Authentication (`/api/v1/auth/`)

- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /refresh` - Refresh access token
- `POST /change-password` - Change password
- `POST /request-password-reset` - Request password reset email
- `POST /password-reset` - Reset password with token
- `GET /me` - Get current user profile

#### Enhanced Authentication (`/api/v1/auth/2/`)

- `POST /login` - Enhanced login with device fingerprinting
- `POST /verify-mfa` - Verify MFA code
- `POST /force-password-change` - Force password change
- `POST /whitelist-ip` - Whitelist current IP
- `GET /devices` - List trusted devices
- `DELETE /devices/{fingerprint_hash}` - Forget device
- `GET /login-history` - Get login history
- `POST /unlock-account` - Request account unlock

#### Users (`/api/v1/users/`)

- `GET /` - List all users (admin)
- `POST /` - Create new user (admin)
- `GET /me` - Get my profile
- `PUT /me` - Update my profile
- `GET /me/permissions` - Get my permissions
- `GET /me/permissions/{resource}` - Get my actions for resource
- `GET /{user_id}` - Get user details
- `PUT /{user_id}` - Update user (admin)
- `DELETE /{user_id}` - Delete user (admin)
- `PUT /{user_id}/status` - Update user status (admin)
- `GET /{user_id}/permissions` - Get user permissions (admin)
- `PUT /{user_id}/permissions` - Update user permissions (admin)

#### Roles (`/api/v1/roles/`)

- `GET /` - List all roles
- `POST /` - Create role
- `GET /{role_id}` - Get role details
- `PUT /{role_id}` - Update role
- `DELETE /{role_id}` - Delete role
- `GET /{role_id}/permissions` - Get role permissions
- `POST /{role_id}/permissions/add` - Add permission to role
- `POST /{role_id}/permissions/remove` - Remove permission from role
- `GET /user/{role_id}` - Get users with role

#### Department Management (`/api/v1/departments/`)

- `GET /` - List all departments
- `POST /` - Create department
- `GET /simple` - List departments (simplified)
- `GET /public` - List departments (public view)
- `GET /heads` - List department heads
- `GET /{dep_id}` - Get department details
- `PUT /{dep_id}` - Update department
- `DELETE /{dep_id}` - Delete department
- `GET /{dep_id}/users` - Get department members
- `GET /{dep_id}/hierarchy` - Get department hierarchy
- `POST /{dep_id}/status` - Change department status

### Asset Management

#### Assets CRUD (`/api/v1/assets/`)

- `POST /` - Create new asset
- `GET /` - List assets with search
- `GET /categories` - List asset categories
- `GET /{asset_id}` - Get asset details
- `PUT /{asset_id}` - Update asset
- `DELETE /{asset_id}` - Delete asset
- `PATCH /{asset_id}/status` - Update asset status
- `GET /a/search/advanced` - Advanced asset search (admin)

#### Asset Tracking

- `POST /{asset_id}/generate-qr` - Generate QR code
- `PUT /{asset_id}/location` - Update asset location
- `GET /by-tag/{tag_number}` - Get asset by tag number
- `GET /by-barcode/{barcode}` - Get asset by barcode
- `GET /by-serial/{serial_number}` - Get asset by serial number

#### Asset Lifecycle (`/api/v1/assets/life/`)

- `POST /{asset_id}/activate` - Activate asset
- `POST /{asset_id}/deactivate` - Deactivate asset
- `POST /{asset_id}/mark-disposal` - Mark for disposal
- `GET /{asset_id}/lifecycle` - Get lifecycle history

#### Asset Assignment (`/api/v1/assets/`)

- `POST /{asset_id}/assign` - Assign asset to user
- `DELETE /{asset_id}/unassign` - Unassign asset
- `PUT /{asset_id}/reassign` - Reassign asset
- `GET /{asset_id}/assignment-history` - Get assignment history
- `GET /m/myassets` - List my assigned assets
- `GET /m/MyDepAssets` - List my department's assets
- `GET /assignments/all` - List all assignments (admin)
- `GET /assignments/unassigned` - List unassigned assets

#### Asset Transfers (`/api/v1/transfers/`)

- `POST /initiate` - Initiate asset transfer
- `GET /` - List transfers with filters
- `GET /{trans_id}` - Get transfer details
- `POST /{trans_id}/approve` - Approve transfer
- `POST /{trans_id}/complete` - Complete transfer
- `POST /{trans_id}/reject` - Reject transfer
- `POST /{trans_id}/cancel` - Cancel transfer
- `POST /{asset_id}/history` - Get asset transfer history
- `GET /pending` - List pending transfers
- `GET /by-user/{user_id}` - List user's transfers

#### Maintenance Management (`/api/v1/assets/`)

- `POST /{asset_id}/maintenance/initiate` - Initiate maintenance request
- `POST /{asset_id}/maintenance/schedule` - Schedule maintenance
- `POST /{asset_id}/maintenance/approve` - Approve maintenance
- `POST /{asset_id}/maintenance/start` - Start maintenance
- `POST /{asset_id}/maintenance/complete` - Complete maintenance
- `GET /{asset_id}/maintenance/history` - Get maintenance history
- `GET /maintenance/upcoming` - Get upcoming maintenance

#### Disposal Management (`/api/v1/assets/`)

- `POST /{asset_id}/disposal/initiate` - Initiate disposal
- `POST /{asset_id}/disposal/schedule` - Schedule disposal
- `POST /{asset_id}/disposal/approve` - Approve disposal
- `POST /{asset_id}/disposal/execute` - Execute disposal
- `POST /{asset_id}/disposal/undo` - Undo disposal
- `GET /disposals` - List all disposals
- `GET /{asset_id}/disposal/history` - Get disposal history

### Location Services (`/api/v1/locations/`)

- `GET /counties/` - Get all counties
- `GET /counties/{county_identifier}/` - Get county constituencies
- `GET /counties/{county_identifier}/constituencies/{constituency_name}/` - Get constituency wards
- `GET /counties/{county_identifier}/tree/` - Get county hierarchy tree
- `GET /search/` - Search locations
- `GET /coordinates/reverse/` - Reverse geocode coordinates
- `GET /search/geocode/` - Forward geocode address

### Reporting & Analytics

#### Basic Reports (`/api/v1/r/reports/`)

- `GET /asset-summary-dashboard` - Asset summary dashboard
- `GET /depreciation` - Depreciation report
- `GET /asset-status-condition` - Status & condition report
- `GET /category-specific/{category}` - Category-specific report
- `GET /unassigned-assets` - Unassigned assets report

#### Department Reports

- `GET /department-assets/{dept_id}` - Department asset report
- `GET /user-responsibility` - User responsibility report
- `GET /department-comparison` - Department comparison

#### Maintenance Reports

- `GET /maintenance-summary` - Maintenance summary
- `GET /upcoming-maintenance` - Upcoming maintenance
- `GET /maintenance-backlog` - Maintenance backlog
- `GET /maintenance-cost-analysis` - Cost analysis

#### Transfer & Disposal Reports

- `GET /pending-transfers-disposals` - Pending approvals
- `GET /transfer-disposal-history` - Historical data

#### Executive Reports

- `GET /executive-summary` - Executive summary dashboard

#### Compliance Reports

- `GET /missing-data` - Missing data report
- `GET /geographic-distribution` - Geographic distribution

#### Security Reports

- `GET /activity-log` - Activity log
- `GET /failed-login-attempts` - Failed login attempts
- `GET /data-modifications` - Data modification audit

#### Utility Reports

- `GET /asset-age-analysis` - Asset age analysis
- `GET /asset-utilization` - Asset utilization
- `GET /available-reports` - List available reports

### Supporting Routes

#### General (`/api/v1/user/supp/`)

- `GET /entitytype` - List entity types
- `GET /govlevel` - List government levels

#### Assets (`/api/v1/assets/supp/`)

- `GET /assetstatus` - List asset statuses
- `GET /assetcondition` - List asset conditions
- `GET /categories/newlist` - List categories by name
- `GET /categories/detailed` - List categories (detailed)
- `GET /categories/info` - Get category information
- `GET /maintain/MaintenanceType` - List maintenance types
- `GET /maintain/IssueCategory` - List issue categories
- `GET /maintain/PriorityLevel` - List priority levels
- `GET /maintain/SeverityLevel` - List severity levels
- `GET /maintain/maintainanceoutcome` - List maintenance outcomes

---

## 🚀 Deployment

K-ALMIS can be deployed to any platform that supports Python applications. Below are general guidelines:

### Deployment Checklist

- [ ] Set all environment variables securely
- [ ] Use strong `SECRET_KEY` and `SECRET_KEY_FP`
- [ ] Configure PostgreSQL with SSL
- [ ] Set up Redis with authentication
- [ ] Configure Cloudinary for production
- [ ] Set up email service (Sendinblue/Brevo)
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up backup strategy for database
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts

### Production Configuration

```bash
# Use production-grade ASGI server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info

# Or with Uvicorn (production mode)
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --workers 4 \
  --no-access-log \
  --proxy-headers \
  --forwarded-allow-ips='*'
```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/static/files;
    }
    
    client_max_body_size 100M;  # For file uploads
}
```

### Docker Support

Docker and Docker Compose configurations are currently in development and will be available soon. This will simplify deployment across different environments.

**Coming Soon:**

- Dockerfile for containerized deployment
- docker-compose.yml for multi-container orchestration (API, PostgreSQL, Redis)
- Environment-specific configurations (dev, staging, production)

### Recommended Deployment Platforms

- **On-Premise Servers**: Full control, suitable for government requirements
- **Cloud Platforms**: AWS, Google Cloud, Azure, DigitalOcean
- **PaaS**: Heroku, Railway, Render (with PostgreSQL add-on)

---

## 🤝 Contributing

We welcome contributions from the community! K-ALMIS is open for contributions to help improve asset management for the Kenyan public sector.

### How to Contribute

1. **Fork the Repository**

```bash
git clone https://github.com/kla-x/K-ALMIS.git
```

2. **Create a Feature Branch**

```bash
git checkout -b feature/your-feature-name
```

3. **Make Your Changes**
   - Write clean, documented code
   - Follow existing code style and patterns
   - Add comments where necessary

4. **Test Your Changes**
   - Ensure all existing functionality works
   - Test new features thoroughly
   - Check for edge cases

5. **Commit Your Changes**

```bash
git add .
git commit -m "Add: Brief description of your changes"
```

6. **Push to Your Fork**

```bash
git push origin feature/your-feature-name
```

7. **Create Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Wait for review and feedback

### Contribution Guidelines

- **Code Style**: Follow PEP 8 Python style guidelines
- **Documentation**: Update README and code comments
- **Testing**: Add tests for new features (test framework coming soon)
- **Commits**: Use clear, descriptive commit messages
- **Issues**: Report bugs and suggest features via GitHub Issues

---

## 📄 License

K-ALMIS is free to use with attribution.

### Terms

- ✅ Free for use in public and private sectors
- ✅ Modification and distribution allowed
- ✅ Commercial use permitted
- ⚠️ Attribution required: Must credit "K-ALMIS - Kenya Asset & Liability Management Information System"
- ⚠️ No warranty: Software provided "as is"

### Recommended Attribution

When using K-ALMIS, please include:

```
Powered by K-ALMIS - Kenya Asset & Liability Management Information System
https://github.com/kla-x/K-ALMIS
```

For detailed license terms, see [LICENSE](LICENSE) file.

---

## 📞 Support

### Contact Information

- **Primary Contact**: musauem98@gmail.com
- **GitHub Issues**: [Report bugs or request features](https://github.com/kla-x/K-ALMIS/issues)

### Getting Help

- **Documentation**: Check this README and API documentation at `/docs`
- **Issues**: Search existing GitHub issues or create a new one
- **Email**: For urgent matters or partnership inquiries, email directly

### Reporting Issues

When reporting bugs, please include:

- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Error messages or logs
- Screenshots (if applicable)

### Feature Requests

We welcome feature suggestions! Please:

- Check if the feature already exists or is planned
- Describe the use case clearly
- Explain why it would benefit K-ALMIS users
- Provide examples if possible

---

## 📖 Additional Documentation

### Asset Categories

K-ALMIS supports the following asset categories as per National Treasury Guidelines:

#### Non-Financial Assets

- **Land** - All land parcels with GPS coordinates
- **Buildings** - Permanent, semi-permanent, temporary structures
- **Investment Property** - Properties held for rental income
- **Road Infrastructure** - Roads, seal coat, gravel, asphalt, concrete surfaces
- **Railway Infrastructure** - Railway lines and wagons
- **Other Infrastructure**:
  - Electricity generation & supply
  - Water infrastructure
  - Drainage systems
  - Solid waste disposal
  - Aerodromes and airstrips
  - Sea walls and jetties
- **Motor Vehicles** - Saloon cars, utility vehicles, lorries
- **ICT Equipment** - Computers, servers, networking equipment
- **Furniture & Equipment** - Office furniture and fittings
- **Plant & Machinery** - Industrial equipment
- **Heritage Assets** - Cultural and historical items
- **Biological Assets** - Livestock, plantations
- **Intangible Assets** - Software, patents, copyrights, licenses
- **Work in Progress** - Assets under construction

#### Financial Assets

- **Cash & Bank** - Bank accounts and petty cash
- **Investments** - Treasury bills, bonds, shares
- **Receivables** - Accounts receivable, loans receivable
- **Other Receivables** - Imprest, advances

### Depreciation & Useful Lives

The system automatically calculates depreciation based on National Treasury guidelines:

| Asset Category | Useful Life | Depreciation Rate |
|---------------|-------------|-------------------|
| Buildings - Permanent | 50 years | 2% |
| Buildings - Semi-permanent | 20 years | 5% |
| Buildings - Temporary | 10 years | 10% |
| Roads - Seal Coat | 5 years | 20% |
| Roads - Asphalt | 10-30 years | 2.5-10% |
| Roads - Concrete | 30-40 years | 2.5-3.3% |
| Railway Infrastructure | 50 years | 2% |
| Motor Vehicles - Saloon | 6 years | 16.67% |
| Motor Vehicles - Heavy Duty | 8 years | 12.5% |
| ICT Equipment | 3.33 years | 30% |
| Furniture & Equipment | 8 years | 12.5% |
| Software | 5-8 years | 12.5-20% |

### Disposal Methods

As per PPAD Act 2015, supported disposal methods include:

- **Transfer** - To another public entity (with or without financial adjustment)
- **Public Tender** - Competitive bidding process
- **Public Auction** - Open auction
- **Trade-in** - Exchange for new asset
- **Waste Disposal Management** - For hazardous or unusable items
- **Other Methods** - As prescribed by legislation

### User Roles & Permissions

The system supports flexible RBAC and ABAC:

#### Default Roles

- **System Administrator** - Full system access
- **Entity Administrator** - Manage entity-level operations
- **Department Head** - Manage department assets and users
- **Asset Manager** - Asset CRUD and lifecycle management
- **Finance Officer** - Financial reports and depreciation
- **Store Keeper** - Receive, issue, and track assets
- **Regular User** - View assigned assets, request transfers

#### Permission Structure

Permissions follow the format: `resource.action`

Examples:

- `assets.read` - View assets
- `assets.create` - Create new assets
- `assets.update` - Modify asset details
- `assets.delete` - Delete assets
- `transfers.approve` - Approve transfer requests
- `maintenance.schedule` - Schedule maintenance
- `reports.executive` - View executive reports

### Compliance & Standards

K-ALMIS is built to comply with:

- **Public Finance Management Act, 2012**
  - Asset recording and reporting requirements
  - Liability management provisions
  - Internal controls and accountability
- **Public Procurement and Asset Disposal Act, 2015**
  - Procurement procedures
  - Disposal methods and approvals
  - Asset registers maintenance
- **International Public Sector Accounting Standards (IPSAS)**
  - IPSAS 12 - Inventories
  - IPSAS 13 - Leases
  - IPSAS 16 - Investment Property
  - IPSAS 17 - Property, Plant & Equipment
  - IPSAS 21 & 26 - Impairment of Assets
  - IPSAS 31 - Intangible Assets
- **Kenya National Treasury Guidelines (March 2020)**
  - Complete asset lifecycle management
  - Standardized categorization and valuation
  - Reporting templates and formats

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Error

```bash
# Error: could not connect to server
# Solution: Check PostgreSQL is running
sudo systemctl status postgresql
sudo systemctl start postgresql

# Verify connection details in .env
psql -h localhost -U your_db_user -d kalmis_db
```

#### Alembic Migration Errors

```bash
# Error: Can't locate revision identified by 'xxxx'
# Solution: Reset and regenerate migrations
alembic stamp head
alembic revision --autogenerate -m "Fresh migration"
alembic upgrade head
```

#### Redis Connection Error

```bash
# Error: Error 111 connecting to localhost:6379
# Solution: Start Redis server
redis-server

# Or check if Redis is installed
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS
```

#### Import Error - Module Not Found

```bash
# Error: ModuleNotFoundError: No module named 'xxx'
# Solution: Reinstall dependencies
pip install -r requirements.txt

# Or update pip
pip install --upgrade pip
pip install -r requirements.txt
```

#### Email Not Sending

```bash
# Check Sendinblue configuration
# 1. Verify API key is correct
# 2. Check sender email is verified in Sendinblue dashboard
# 3. Review email logs in Sendinblue console
# 4. Ensure SENDER_EMAIL and SENDER_NAME are set in .env
```

#### File Upload Errors

```bash
# Error: Cloudinary upload failed
# Solution: Verify Cloudinary credentials
# 1. Check CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
# 2. Test credentials in Cloudinary dashboard
# 3. Check file size limits (default: 100MB)
```

#### Authentication Issues

```bash
# Issue: Token expired or invalid
# Solution: Request new token via /refresh endpoint

# Issue: Account locked
# Solution: Use /auth/2/unlock-account endpoint with email
```

---

## 🧪 Testing

Testing framework is currently under development. Planned test coverage includes:

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

### Future Test Setup

```bash
# Install testing dependencies (coming soon)
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests (structure in development)
pytest tests/ -v --cov=app

# Generate coverage report
pytest --cov=app --cov-report=html
```

**Note**: Contributors are welcome to help establish comprehensive test coverage!

---

## 📊 Database Schema Overview

### Core Tables

#### Users & Authentication

- `users` - User accounts and profiles
- `roles` - System roles
- `permissions` - Granular permissions
- `user_roles` - User-role assignments
- `role_permissions` - Role-permission mappings
- `login_history` - Authentication audit trail
- `trusted_devices` - Device fingerprints
- `ip_whitelist` - Whitelisted IP addresses

#### Organization

- `departments` - Organizational departments
- `entity_types` - Types of government entities
- `government_levels` - National, county, sub-county

#### Assets

- `assets` - Main asset table
- `asset_categories` - Asset categorization
- `asset_assignments` - Current asset assignments
- `assignment_history` - Assignment audit trail
- `asset_locations` - Geographic tracking
- `asset_lifecycle_events` - Status changes

#### Operations

- `transfers` - Asset transfer requests
- `maintenance_records` - Maintenance tracking
- `disposal_records` - Disposal tracking
- `qr_codes` - Generated QR codes

#### Geography

- `counties` - 47 Kenyan counties
- `constituencies` - Electoral constituencies
- `wards` - Administrative wards

---

## 🔄 System Workflows

### Asset Acquisition Workflow

```
1. Request Asset → 2. Budget Approval → 3. Procurement
→ 4. Receipt & Inspection → 5. Recording → 6. Tagging
→ 7. Assignment → 8. Activation
```

### Transfer Workflow

```
1. Initiate Transfer → 2. Approval (Source Department)
→ 3. Approval (Receiving Department) → 4. Complete Transfer
→ 5. Update Records → 6. Notify Parties
```

### Maintenance Workflow

```
1. Identify Issue → 2. Create Request → 3. Approval
→ 4. Schedule → 5. Execute Maintenance → 6. Complete
→ 7. Update Records → 8. Calculate Costs
```

### Disposal Workflow

```
1. Mark for Disposal → 2. Evaluation → 3. Approval (Finance)
→ 4. Approval (Management) → 5. Schedule Disposal
→ 6. Execute Disposal → 7. Record Outcome → 8. Update Registers
```

---

## 📈 Performance Optimization

### Database Optimization

- Indexed columns for faster queries
- Efficient JOIN operations
- Query result caching with Redis
- Connection pooling

### API Optimization

- Response compression
- Lazy loading for large datasets
- Pagination for list endpoints
- Selective field returns

### Caching Strategy

Redis caching for:

- Session data
- Frequently accessed lookups (counties, categories)
- Computed reports
- User permissions

---

## 🔐 Security Best Practices

### For Administrators

#### Strong Authentication

- Enable MFA for all privileged accounts
- Use strong, unique passwords
- Rotate passwords every 90 days

#### Access Control

- Follow principle of least privilege
- Regular audit of user permissions
- Remove inactive accounts promptly

#### Monitoring

- Review login history regularly
- Monitor failed authentication attempts
- Check system logs for anomalies

#### Network Security

- Use HTTPS in production
- Implement firewall rules
- Restrict database access
- Keep Redis password-protected

#### Data Protection

- Regular database backups
- Secure storage of environment variables
- Encrypt sensitive data at rest
- Secure file uploads on Cloudinary

### For Developers

#### Code Security

- Never commit secrets to Git
- Validate all user inputs
- Use parameterized queries
- Implement rate limiting

#### Dependency Management

- Regularly update dependencies
- Monitor for security vulnerabilities
- Use virtual environments

#### API Security

- Implement proper CORS policies
- Use JWT with short expiry
- Validate all tokens
- Log security events

---

## 🌍 Internationalization

**Currently supported**: English (en)

**Planned**: Swahili (sw) translation

The system is built with i18n support in mind. Contributions for Swahili translation are welcome!

---

## 📱 Mobile Integration

K-ALMIS API is designed to support mobile applications:

- RESTful API architecture
- JSON responses
- JWT authentication (mobile-friendly)
- QR code scanning endpoints
- Location services integration
- Offline-first considerations (planned)

Mobile app development is open for collaboration!

---

## 🎯 Roadmap

### Short Term (Q1-Q2 2025)

- ✅ Core asset management
- ✅ Enhanced security features
- ✅ Basic reporting
- 🔄 Docker containerization
- 🔄 Comprehensive testing suite
- 📋 Swahili translation

### Medium Term (Q3-Q4 2025)

- 📋 Mobile application (Android/iOS)
- 📋 Advanced analytics dashboard
- 📋 Automated depreciation calculations
- 📋 Bulk import/export features
- 📋 Integration with IFMIS
- 📋 Barcode/RFID scanning

### Long Term (2026+)

- 📋 AI-powered asset predictions
- 📋 Blockchain for asset transfers
- 📋 IoT device integration
- 📋 Predictive maintenance
- 📋 Multi-language support expansion
- 📋 ERP system integrations

---

## 🙏 Acknowledgments

- **National Treasury of Kenya** - For comprehensive asset management guidelines
- **FastAPI Team** - For the excellent web framework
- **OpenStreetMap** - For geocoding services
- **Public Sector Accounting Standards Board (PSASB)** - For accounting standards
- **All Contributors** - For improving K-ALMIS

---

## 📚 References

- [Guidelines on Asset and Liability Management in the Public Sector (March 2020)](https://newsite.treasury.go.ke/sites/default/files/NALM/General-Guidelines-on-asset-and-liability-management-2020-Final.pdf)
- [Public Finance Management Act, 2012](http://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/PublicFinanceManagementAct_No18of2012.pdf)
- [Public Procurement and Asset Disposal Act, 2015](http://ppra.go.ke/images/PPADA2015.pdf)
- [IPSAS - International Public Sector Accounting Standards](https://www.ipsasb.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OpenStreetMap Nominatim](https://nominatim.org/)

---

## 📝 Changelog

### Version 1.0.0 (Current)

- Initial release
- Complete asset lifecycle management
- Enhanced security with MFA and device fingerprinting
- Comprehensive reporting system
- Department and user management
- Transfer and disposal workflows
- Maintenance tracking
- Geographic integration for Kenya
- Email notifications
- QR code generation

---

## 🚀 Quick Start Summary

```bash
# 1. Clone and setup
git clone https://github.com/kla-x/K-ALMIS.git
cd K-ALMIS
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Setup database
createdb kalmis_db
alembic upgrade head
python scripts/seed_data.py

# 5. Start Redis
redis-server

# 6. Run application
uvicorn main:app --reload

# 7. Access API docs
# Open http://localhost:8000/docs
```

---

## 💡 Need Help?

- 📖 **Documentation**: Start with this README and `/docs` endpoint
- 🐛 **Bug Report**: [Open an issue](https://github.com/kla-x/K-ALMIS/issues)
- 💬 **Questions**: Email support
- 🤝 **Contribute**: Check [Contributing](#-contributing) section

---

<div align="center">

### K-ALMIS - Modernizing Asset Management for Kenya's Public Sector

**Made with ❤️ for Kenya's Public Sector**

[Report Bug](https://github.com/kla-x/K-ALMIS/issues) • [Request Feature](https://github.com/kla-x/K-ALMIS/issues) • [Documentation](http://localhost:8000/docs)

</div>