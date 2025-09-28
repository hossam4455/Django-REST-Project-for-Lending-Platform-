# Lenme Lending Platform - Django REST API

A peer-to-peer lending platform built with **Django REST Framework** that facilitates **loan applications, lender offers, funding, repayments, and automated financial tracking**.

---

## 📑 Table of Contents
- [Features](#-features)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [API Flow](#-api-flow)
- [Celery Tasks](#-celery-tasks)
- [Financial Logic](#-financial-logic)
- [Testing](#-testing)
- [Database Models](#-database-models)
- [Status Transitions](#-status-transitions)
- [Deployment Notes](#-deployment-notes)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Features
- **Loan Management**: Create, view, and manage loan requests.
- **Offer System**: Lenders submit offers on available loans.
- **Fund Reservation**: Secure fund reservation during offer process.
- **Payment Scheduling**: Automated monthly payment scheduling.
- **Balance Management**: User profiles with available and reserved balances.
- **Transaction Tracking**: Complete audit trail for all financial transactions.
- **Celery Tasks**: Automated payment processing, overdue detection, and loan completion.

---

## 🏗️ Project Structure
### Models
- **Profile**: User financial profile with balance management.  
- **Loan**: Loan requests with status tracking.  
- **Offer**: Lender offers with fund reservation.  
- **Payment**: Scheduled monthly payments.  
- **Transaction**: Financial transaction records.  

---

## 🔄 API Endpoints

### Loan Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/loans/` | Create loan request | Borrower |
| `GET`  | `/api/loans/available/` | List loans available for funding | Lender |

### Offer System
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/loans/{id}/offers/` | Submit an offer | Lender |
| `POST` | `/api/loans/{id}/accept/` | Accept an offer | Borrower |
| `POST` | `/api/loans/{id}/reject/{offer_id}/` | Reject an offer | Borrower |

### Funding & Payments
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/loans/{id}/fund/` | Fund loan | Lender |
| `POST` | `/api/loans/{id}/payments/{payment_id}/pay/` | Make payment | Borrower |

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Django 4.0+
- Django REST Framework
- PostgreSQL (recommended) or SQLite
- Redis (for Celery)

### Quick Start
```bash
# Clone and setup environment
git clone <repository-url>
cd lending-platform
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Celery worker & beat
celery -A your_project worker --loglevel=info
celery -A your_project beat --loglevel=info

# Run development server
python manage.py runserver
1. Borrower creates loan → DRAFT → OPEN
2. Lender submits offer → funds reserved → OFFERED
3. Borrower accepts best offer → funds transferred → ACCEPTED
4. Lender funds loan → schedule created → FUNDED
5. Celery auto-processes monthly payments
6. When all payments are complete → COMPLETED
   If overdue → DEFAULTED
Celery Tasks

process_due_payments: Runs hourly, deducts payments automatically.

check_overdue_payments: Runs daily, applies late fees, sends reminders.

update_loan_statuses: Runs hourly, updates loans to COMPLETED or DEFAULTED.

💰 Financial Logic

Principal: Example $5,000

Lenme Fee: $3.75 (paid by lender)

Interest: 15% APR fixed

Monthly Payment: Calculated via amortization formula.

def monthly_payment_amount(self):
    r = (self.interest_rate / Decimal('100')) / Decimal('12')
    n = Decimal(self.term_months)
    numerator = self.amount * r * (1 + r) ** n
    denominator = (1 + r) ** n - 1
    return (numerator / denominator).quantize(Decimal('0.01'))

🧪 Testing
pip install pytest pytest-django

# Run tests
pytest

# Run with coverage
pytest --cov=lending


Example coverage includes:

Loan creation and validation

Fund reservation during offers

Balance transfers during funding

Payment processing

Status transitions

Celery task functionality

📊 Database Models

Profile: user, balance, reserved_balance

Loan: borrower, lender, amount, term_months, interest_rate, status

Offer: loan, lender, interest_rate, reserved_amount, status

Payment: loan, due_date, amount, paid

Transaction: from_user, to_user, amount, note

🔒 Status Transitions
DRAFT → OPEN → OFFERED → ACCEPTED → FUNDED → COMPLETED
                                    ↓
                                DEFAULTED

🚀 Deployment Notes

Use PostgreSQL in production.

Configure Redis for Celery broker.

Store secrets in environment variables (DATABASE_URL, REDIS_URL, SECRET_KEY).

Disable DEBUG.

Configure logging and email for notifications.

🆘 Troubleshooting

Celery not running → ensure worker & beat are started.

Payments not processed → check logs for process_due_payments.

Insufficient funds → borrower may not have enough balance.
<img width="1190" height="621" alt="erd" src="https://github.com/user-attachments/assets/8a04c07f-db5d-4b1e-a21b-8d0e0262d406" />

Redis connection refused → check if Redis is running.

✅ Optional Features Implemented

Hourly payment processing with Celery

Automatic payment collection

Late fee management

Loan status automation

Email notifications
