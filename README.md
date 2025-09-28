# 💸 Lenme Lending Platform - Django REST API

A **peer-to-peer lending platform** built with **Django REST Framework** that enables borrowers and lenders to seamlessly manage **loan applications, offers, funding, and repayments**.
     DEFAULTED<img width="1190" height="621" alt="erd" src="https://github.com/user-attachments/assets/32c4cf99-965f-4b35-b427-e0b8e0f008d4" />
---

## 🚀 Features

- **Loan Management** – Create, view, and manage loan requests  
- **Offer System** – Lenders can submit offers on available loans  
- **Fund Reservation** – Secure reservation of lender funds during offer process  
- **Payment Scheduling** – Automated monthly payment scheduling  
- **Balance Management** – User profiles with available & reserved balances  
- **Transaction Tracking** – Complete audit trail for all financial transactions  
- **Celery Tasks** – Automated payment processing & loan status updates  

---

## 🏗️ Project Structure

### **Models**
- `Profile` – User financial profile with balance management  
- `Loan` – Loan requests with lifecycle/status tracking  
- `Offer` – Lender offers with reserved funds  
- `Payment` – Scheduled monthly payments  
- `Transaction` – Records of all financial transactions  

### **Key Endpoints**

#### Loan Management
- `POST /api/loans/` – Create a loan request *(Borrower)*  
- `GET /api/loans/available/` – List open loans for funding *(Lender)*  

#### Offer System
- `POST /api/loans/{id}/submit-offer/` – Submit loan offer *(Lender)*  
- `POST /api/loans/{id}/accept-offer/` – Accept an offer *(Borrower)*  
- `POST /api/loans/{id}/reject-offer/{offer_id}/` – Reject an offer *(Borrower)*  

#### Funding & Payments
- `POST /api/loans/{id}/fund/` – Fund an accepted loan *(Lender)*  
- `POST /api/loans/{id}/payments/{payment_id}/` – Make a payment *(Borrower)*  

---

## ⚙️ Installation & Setup

### **Prerequisites**
- Python 3.8+  
- Django 4.0+  
- Django REST Framework  
- PostgreSQL (recommended) or SQLite  
- Redis (for Celery)  

### **Quick Start**

```bash
# Clone repository
git clone <repository-url>
cd lending-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
Create Superuser
python manage.py createsuperuser

Run Celery Workers
celery -A your_project worker --loglevel=info
celery -A your_project beat --loglevel=info

Run Development Server
python manage.py runserver

📋 Lending Flow
1. Borrower creates loan      → Status: DRAFT → OPEN
2. Lender submits offer       → Funds reserved → Status: OFFERED
3. Borrower accepts offer     → Funds transferred → Status: ACCEPTED
4. Lender funds loan          → Payment schedule created → Status: FUNDED
5. Automated payments (Celery) → Auto-deduct borrower balance → Transfer to lender
6. Loan completion            → Status: COMPLETED / DEFAULTED

🤖 Celery Tasks

process_due_payments (hourly) → Deduct due payments automatically

check_overdue_payments (daily) → Apply late fees & notify users

update_loan_statuses (hourly) → Auto-update loan lifecycle

process_single_payment → Manual retry for failed payments

💰 Financial Logic

Loan Example:

Amount: $5,000

Interest Rate: 15% APR (fixed)

Term: 6 months

Platform Fee: $3.75 (paid by lender)

Monthly Payment Calculation: (Amortization Formula)

def monthly_payment_amount(self):
    r = (self.interest_rate / Decimal('100.0')) / Decimal('12.0')  # Monthly rate
    n = Decimal(self.term_months)
    numerator = self.amount * r * (1 + r) ** n
    denominator = ((1 + r) ** n) - 1
    return (numerator / denominator).quantize(Decimal('0.01'))

🧪 Testing
# Install test dependencies
pip install pytest pytest-django

# Run tests
pytest

# Run with coverage
pytest --cov=lending


Coverage Includes:

Loan creation & validation

Offer fund reservation

Balance transfers & funding

Payment processing

Status transitions

Celery task execution

🚀 Deployment Notes

Use PostgreSQL in production

Configure Redis for Celery broker

Set up logging and email notifications

Manage secrets via environment variables

Example Environment Variables

DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEBUG=False

🆘 Troubleshooting

Celery not running? Ensure both worker & beat are started

DB Issues? Confirm PostgreSQL service is active

Redis errors? Ensure Redis server is running

Payments failing? Borrower may have insufficient balance

✅ Implemented Features

 Hourly payment processing (Celery)

 Automatic payment collection

 Late fee management

 Loan status automation (Completed / Defaulted)

 Email notifications (reminders & overdue alerts)

📊 Status Lifecycle
DRAFT → OPEN → OFFERED → ACCEPTED → FUNDED → COMPLETED
                                   ↓
                          



📌 This project demonstrates end-to-end lending workflows with automated payment processing, real-time balance tracking, and fault-tolerant Celery tasks.
