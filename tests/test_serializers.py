import pytest
from django.contrib.auth.models import User
from lending.serializers import CreateLoanSerializer, OfferSerializer
from lending.models import Loan, Offer

@pytest.mark.django_db
class TestCreateLoanSerializer:
    def test_valid_serializer(self):
        data = {
            'amount': '1000.00',
            'term_months': 12,
            'interest_rate': '5.00'
        }
        serializer = CreateLoanSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_negative_amount(self):
        data = {
            'amount': '-100.00',  # Negative amount
            'term_months': 12,
            'interest_rate': '5.00'
        }
        serializer = CreateLoanSerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors
        assert "greater than zero" in str(serializer.errors['amount'])

    def test_invalid_zero_amount(self):
        data = {
            'amount': '0.00',  # Zero amount
            'term_months': 12,
            'interest_rate': '5.00'
        }
        serializer = CreateLoanSerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors

    def test_invalid_term_months(self):
        data = {
            'amount': '1000.00',
            'term_months': 0,  # Zero term
            'interest_rate': '5.00'
        }
        serializer = CreateLoanSerializer(data=data)
        assert not serializer.is_valid()
        assert 'term_months' in serializer.errors

    def test_invalid_high_interest_rate(self):
        data = {
            'amount': '1000.00',
            'term_months': 12,
            'interest_rate': '60.00'  # Too high rate
        }
        serializer = CreateLoanSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interest_rate' in serializer.errors

    def test_null_interest_rate(self):
        data = {
            'amount': '1000.00',
            'term_months': 12,
            'interest_rate': None  # Null interest rate (0% interest)
        }
        serializer = CreateLoanSerializer(data=data)
        assert serializer.is_valid()  # Should be valid as interest_rate can be null

@pytest.mark.django_db
class TestOfferSerializer:
    def test_valid_serializer(self):
        user = User.objects.create_user('testuser', 'test@test.com', 'password')
        loan = Loan.objects.create(
            borrower=user,
            amount=1000.00,
            term_months=12,
            status='OPEN'
        )
        data = {
            'interest_rate': '4.50'
        }
        serializer = OfferSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_negative_interest_rate(self):
        data = {
            'interest_rate': '-5.00'  # Negative rate
        }
        serializer = OfferSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interest_rate' in serializer.errors

    def test_invalid_high_interest_rate(self):
        data = {
            'interest_rate': '150.00'  # Too high rate
        }
        serializer = OfferSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interest_rate' in serializer.errors
        assert "cannot exceed 50%" in str(serializer.errors['interest_rate'])

    def test_invalid_zero_interest_rate(self):
        data = {
            'interest_rate': '0.00'  # Zero rate
        }
        serializer = OfferSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interest_rate' in serializer.errors