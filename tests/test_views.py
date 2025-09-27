import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from lending.models import Loan, Profile

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def users():
    borrower = User.objects.create_user(
        username='borrower', 
        email='borrower@test.com', 
        password='testpass123'
    )
    lender = User.objects.create_user(
        username='lender', 
        email='lender@test.com', 
        password='testpass123'
    )
    return {'borrower': borrower, 'lender': lender}

@pytest.mark.django_db
class TestLoanCreateView:
    def test_create_loan_authenticated(self, api_client, users):
        """Test creating a loan as authenticated user"""
        api_client.force_authenticate(user=users['borrower'])
        url = reverse('create-loan')
        data = {
            'amount': '1500.00',
            'term_months': 6,
            'interest_rate': '7.50'
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Loan.objects.count() == 1
        
        loan = Loan.objects.first()
        assert loan.borrower == users['borrower']
        assert loan.amount == Decimal('1500.00')
        assert loan.term_months == 6
        assert loan.interest_rate == Decimal('7.50')
        assert loan.status == 'DRAFT'  # Default status

    def test_create_loan_negative_amount(self, api_client, users):
        """Test creating a loan with negative amount (should fail)"""
        api_client.force_authenticate(user=users['borrower'])
        url = reverse('create-loan')
        data = {
            'amount': '-100.00',  # Negative amount
            'term_months': 6,
            'interest_rate': '7.50'
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amount' in response.data

    def test_create_loan_unauthenticated(self, api_client):
        """Test creating a loan without authentication"""
        url = reverse('create-loan')
        data = {
            'amount': '1500.00',
            'term_months': 6,
            'interest_rate': '7.50'
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_loan_high_interest_rate(self, api_client, users):
        """Test creating a loan with too high interest rate (should fail)"""
        api_client.force_authenticate(user=users['borrower'])
        url = reverse('create-loan')
        data = {
            'amount': '1000.00',
            'term_months': 12,
            'interest_rate': '60.00'  # Too high
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'interest_rate' in response.data

    def test_create_loan_zero_term(self, api_client, users):
        """Test creating a loan with zero term (should fail)"""
        api_client.force_authenticate(user=users['borrower'])
        url = reverse('create-loan')
        data = {
            'amount': '1000.00',
            'term_months': 0,  # Zero term
            'interest_rate': '5.00'
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'term_months' in response.data