Lenme — Lending Platform (Django REST)

A small Django REST project implementing a peer-to-peer lending flow:
borrower creates a loan request → lenders make offers (reserve funds) → borrower accepts an offer → lender funds the loan → scheduled monthly payments → borrower pays monthly until the loan is COMPLETED.

This README documents how to configure, run, test, and use the APIs included in your codebase.

Table of contents

Features / Flow

Models (short summary)

API endpoints

Environment & configuration

Run locally (dev)

Run tests

Example usage (curl)

Notes & implementation details

Suggested improvements / next steps

CI (GitHub Actions) example

Features / Flow

Borrower submits a loan request (amount, term_months, optional interest_rate).

Lenders list available loans (loans without a lender and in OFFERED state) and submit offers.

Offers reserve the lender’s funds (uses Profile.reserve_funds).

Borrower can accept the best offer (lowest interest rate).

Accepting triggers fund transfer logic (profiles updated, other offers rejected and reserved funds released).

Lender can fund an accepted loan (or funding may already have moved balances during acceptance depending on your flow).

Funding sets loan.status = FUNDED and creates payment schedule (monthly payments).

Borrower pays scheduled payments. When all payments marked paid, loan.status should be set to COMPLETED.

This repository already includes basic models, serializers, and views for these actions.

Models (short summary)

Profile

user (OneToOne -> User)

balance (Decimal)

reserved_balance (Decimal)

Methods: available_balance(), has_sufficient_funds(amount), reserve_funds(amount), release_funds(amount), transfer_funds(amount, to_profile)

Loan

borrower (FK -> User)

lender (FK -> User, nullable)

amount, term_months, interest_rate

lenme_fee (fee paid by lender)

status (DRAFT, OPEN, OFFERED, ACCEPTED, FUNDED, COMPLETED)

created_at, funded_at

Helper methods: total_loan_amount(), monthly_payment_amount()

Offer

loan (FK)

lender (FK)

interest_rate, reserved_amount, status (OPEN, ACCEPTED, REJECTED, EXPIRED, PENDING)

created_at

Payment

loan (FK)

due_date, amount, paid (bool), paid_at

Transaction

from_user, to_user, amount, note, created_at

API endpoints

Note: replace <BASE_URL> with your local server (e.g. http://localhost:8000)

POST /api/loans/ — Create loan (authenticated borrower)
Serializer: CreateLoanSerializer
Required body: { "amount": "5000.00", "term_months": 6, "interest_rate": "15.00" }
Default status: DRAFT (your view uses CreateAPIView with IsAuthenticated)

GET /api/loans/available/ — Available loans for lenders (list loans with lender IS NULL and status='OFFERED')

View: AvailableLoansView (ListAPIView)

POST /api/loans/{loan_id}/offers/ — Submit offer (authenticated lender)

Reserves lender funds (Profile.reserve_funds(total_needed)) and creates Offer with reserved_amount.

Example payload in your current SubmitOfferView uses fixed rate of 15.00 and status 'PENDING'.

GET /api/loans/{loan_id}/offers/ — List offers for a loan (excludes REJECTED).

POST /api/loans/{loan_id}/accept/ — Accept best offer (borrower only)

Accepts the best pending offer, transfers funds, sets loan ACCEPTED, rejects other offers and releases their reserved funds.

POST /api/loans/{loan_id}/reject/{offer_id}/ — Reject offer (borrower only)

Releases reserved funds and sets offer REJECTED. If no pending offers remain, loan returns to OPEN.

POST /api/loans/{loan_id}/fund/ — Fund loan (lender only; used if not already fully transferred during accept flow)

Transfers funds, sets FUNDED, creates payment schedule (Payment objects).

POST /api/loans/{loan_id}/payments/{payment_id}/pay/ — Make payment (borrower only)

Validates borrower balance, transfers to lender, marks Payment.paid = True, creates a Transaction.

Environment & configuration

Create a .env (or use environment variables):

DEBUG=True
SECRET_KEY=replace-this-with-a-secure-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/lenme_db
# or for SQLite:
# DATABASE_URL=sqlite:///db.sqlite3


Example settings.py snippet (using dj-database-url):

import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
}


Dependencies (example):

Django

djangorestframework

pytest

pytest-django

dj-database-url (optional)

psycopg2-binary (if using PostgreSQL)

Add to requirements.txt:

Django>=4.2
djangorestframework
pytest
pytest-django
dj-database-url
psycopg2-binary

Run locally (dev)

Create & activate virtualenv:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Configure .env (database, secret key).

Run migrations:

python manage.py migrate


Create superuser (optional):

python manage.py createsuperuser


Run development server:

python manage.py runserver

Run tests

Tests use pytest and pytest-django. Example command:

pytest -q


If using a database URL that points to Postgres, ensure the DB exists and credentials are correct. Otherwise use the default SQLite for tests.

Example test hints:

Use fixtures to create User and Profile instances if Profile is required.

Mark DB-using tests with @pytest.mark.django_db.

Example usage (curl)

Create loan (borrower):

curl -X POST http://localhost:8000/api/loans/ \
  -H "Authorization: Token <BORROWER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount":"5000.00","term_months":6,"interest_rate":"15.00"}'


Lender submits offer (reserves funds):

curl -X POST http://localhost:8000/api/loans/1/offers/ \
  -H "Authorization: Token <LENDER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"interest_rate":"15.00"}'


Borrower accepts best offer:

curl -X POST http://localhost:8000/api/loans/1/accept/ \
  -H "Authorization: Token <BORROWER_TOKEN>"


Lender funds loan (if required by flow):

curl -X POST http://localhost:8000/api/loans/1/fund/ \
  -H "Authorization: Token <LENDER_TOKEN>"


Borrower pays monthly payment:

curl -X POST http://localhost:8000/api/loans/1/payments/5/pay/ \
  -H "Authorization: Token <BORROWER_TOKEN>"

Notes & implementation details

Profile creation: Ensure a Profile is created for each User (via a post_save signal on User) or create it explicitly in fixtures. Many view flows expect Profile to exist.

Monetary math: Use decimal.Decimal throughout; avoid float arithmetic.

Date arithmetic: Current code creates payment schedule by adding timedelta(days=30 * n) — this is an approximation; consider using dateutil.relativedelta to add months correctly.

Atomicity: Key financial actions use transaction.atomic() — keep that to avoid partial updates.

Reserved funds: Offer.reserved_amount and Profile.reserved_balance are used to prevent double-funding; ensure all branches (accept/reject/timeout) release reserved funds.

Edge cases:

When accepting an offer, verify the lender still has reserved balance.

Consider race conditions if multiple offers accepted/funded nearly simultaneously (database-level locks or optimistic locking).

Validation: Serializers validate amount, term_months, and interest_rate (e.g., no negative amounts, max caps).

Status transitions: Validate permitted transitions (DRAFT → OPEN → OFFERED → ACCEPTED → FUNDED → COMPLETED).

Testing: Include tests for:

Borrower loan request (POST /api/loans/).

Lender offer submission and reserved funds logic.

Borrower acceptance and funds transfer.

Loan funding and creation of payment schedule.

Borrower making monthly payments and loan completion.

Suggested improvements / next steps

Add OpenAPI / Swagger docs (e.g., drf-spectacular or drf-yasg) and expose /swagger/ route.

Replace timedelta(days=30*n) with relativedelta(months=+1) from dateutil.

Add Celery + Celery Beat for scheduled tasks (e.g., reminder emails, automatic repayment attempts).

Add email/notifications for events (offer submitted, accepted, payment due).

Add automated CI to run tests on push (example below).

Add stronger concurrency control around fund reservation and transfer (select_for_update on Profile).

CI (GitHub Actions) example

.github/workflows/ci.yml (simple example):

name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_DB: lenme_test
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    env:
      DATABASE_URL: postgres://postgres:postgres@127.0.0.1:5432/lenme_test
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run migrations
        run: |
          python manage.py migrate --noinput
      - name: Run tests
        run: pytest -q


If you’d like, I can:

Generate a markdown README.md file and paste it ready for your repo (I already did above — you can copy it).

Add a post_save signal example to auto-create Profile for new Users.

Create example pytest test(s) demonstrating the 5k/6-month flow (borrower request → lender offer → accept → fund → payments).
