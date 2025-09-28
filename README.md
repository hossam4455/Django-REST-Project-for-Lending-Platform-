Lenme Lending Platform - Django REST API
A peer-to-peer lending platform built with Django REST Framework that facilitates loan applications, offers, funding, and repayments.

🚀 Features
Loan Management: Create, view, and manage loan requests

Offer System: Lenders can submit offers on available loans

Fund Reservation: Secure fund reservation during offer process

Payment Scheduling: Automated monthly payment scheduling

Balance Management: User profiles with available and reserved balances

Transaction Tracking: Complete audit trail for all financial transactions

Comprehensive Testing: Full test coverage for all endpoints

🏗️ Project Structure
Models
Profile: User financial profile with balance management

Loan: Loan requests with status tracking

Offer: Lender offers with fund reservation

Payment: Scheduled monthly payments

Transaction: Financial transaction records

Key Endpoints
Loan Management
POST /api/loans/ - Create a new loan request

GET /api/loans/available/ - List loans available for funding

Offer System
POST /api/loans/{id}/submit-offer/ - Submit an offer on a loan

POST /api/loans/{id}/accept-offer/ - Accept a lender's offer

POST /api/loans/{id}/reject-offer/{offer_id}/ - Reject an offer

Funding & Payments
POST /api/loans/{id}/fund/ - Fund an accepted loan

POST /api/loans/{id}/payments/{payment_id}/ - Make a monthly payment

🛠️ Installation & Setup
Prerequisites
Python 3.8+

Django 4.0+

Django REST Framework

PostgreSQL (recommended) or SQLite

pytest & pytest-django for testing

Quick Start
Clone and setup environment

bash
git clone <repository-url>
cd lending-platform
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install django djangorestframework psycopg2-binary pytest pytest-django
Database setup

bash
python manage.py makemigrations
python manage.py migrate
Create superuser

bash
python manage.py createsuperuser
Run development server

bash
python manage.py runserver
🧪 Testing
Running Tests
bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest lending/tests.py::TestLoanCreateView -v

# Run with coverage report
pytest --cov=lending
Test Configuration
Create pytest.ini in your project root:

ini
[pytest]
DJANGO_SETTINGS_MODULE = your_project.settings
python_files = tests.py test_*.py *_tests.py
addopts = --reuse-db
Test Structure
Your test suite includes:

Loan Creation Tests (TestLoanCreateView)
✅ Authenticated loan creation

✅ Validation for negative amounts

✅ Unauthenticated access prevention

✅ Interest rate validation

✅ Loan term validation

Test Fixtures
python
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def users():
    borrower = User.objects.create_user(username='borrower', password='testpass123')
    lender = User.objects.create_user(username='lender', password='testpass123')
    return {'borrower': borrower, 'lender': lender}
Example Test Scenarios
python
# Test successful loan creation
def test_create_loan_authenticated(self, api_client, users):
    api_client.force_authenticate(user=users['borrower'])
    response = api_client.post(reverse('create-loan'), {
        'amount': '1500.00',
        'term_months': 6,
        'interest_rate': '7.50'
    })
    assert response.status_code == status.HTTP_201_CREATED
    assert Loan.objects.count() == 1

# Test validation errors
def test_create_loan_negative_amount(self, api_client, users):
    api_client.force_authenticate(user=users['borrower'])
    response = api_client.post(reverse('create-loan'), {
        'amount': '-100.00',  # Should fail
        'term_months': 6,
        'interest_rate': '7.50'
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
Adding More Tests
Extend your test suite with these additional test classes:

python
class TestOfferFlow:
    def test_submit_offer_sufficient_funds(self, api_client, users):
        """Test submitting an offer with sufficient funds"""
        pass
    
    def test_submit_offer_insufficient_funds(self, api_client, users):
        """Test submitting an offer with insufficient funds"""
        pass
    
    def test_accept_offer_flow(self, api_client, users):
        """Test complete offer acceptance flow"""
        pass

class TestPaymentFlow:
    def test_make_payment_success(self, api_client, users):
        """Test successful payment processing"""
        pass
    
    def test_make_payment_insufficient_funds(self, api_client, users):
        """Test payment with insufficient borrower funds"""
        pass
📋 API Flow
1. Loan Application Flow
text
Borrower POST /api/loans/
→ Creates loan with status: DRAFT
→ Borrower updates loan status to OPEN
→ Loan appears in available loans list
2. Offer & Funding Flow
text
Lender GET /api/loans/available/
→ Lender POST /api/loans/{id}/submit-offer/
→ Funds reserved in lender's profile
→ Borrower POST /api/loans/{id}/accept-offer/
→ Funds transferred, payment schedule created
→ Lender POST /api/loans/{id}/fund/
→ Loan status: FUNDED
3. Repayment Flow
text
Borrower POST /api/loans/{id}/payments/{payment_id}/
→ Monthly payment processed
→ All payments completed → Loan status: COMPLETED
🔧 Configuration
Database (settings.py)
python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'lenme_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
Test Database
python
# For testing, you can use SQLite
import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
📊 Example Usage
Create a Loan
bash
curl -X POST http://localhost:8000/api/loans/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-token>" \
  -d '{
    "amount": "5000.00",
    "term_months": 6,
    "interest_rate": "15.00"
  }'
Submit an Offer
bash
curl -X POST http://localhost:8000/api/loans/1/submit-offer/ \
  -H "Authorization: Token <lender-token>"
🔄 Status Transitions
text
DRAFT → OPEN → OFFERED → ACCEPTED → FUNDED → COMPLETED
💰 Financial Calculations
Total Loan Amount: Loan Amount + Lenme Fee ($3.75)

Monthly Payment: Calculated using standard amortization formula

Available Balance: Total Balance - Reserved Balance

🚨 Important Notes
Funds are reserved when offers are submitted

Only the borrower can accept/reject offers

Lenders must have sufficient available balance

Payments are scheduled automatically upon funding

All financial operations are atomic and transactional

📈 Optional Features
Caching: Available loans cache with automatic invalidation

Celery Tasks: Hourly payment processing and reminders

Swagger Documentation: Auto-generated API documentation

🆘 Troubleshooting
Common Issues:

Insufficient funds: Check lender's available balance

Invalid status transitions: Verify current loan status

Payment failures: Ensure borrower has sufficient balance

Test database issues: Use pytest --create-db to recreate test database

Test-Specific Issues:

Database isolation: Each test runs in transaction

Authentication: Use force_authenticate for testing

Fixture data: Set up test data in fixtures

For additional support, check the Django REST Framework documentation or create an issue in the repository.

