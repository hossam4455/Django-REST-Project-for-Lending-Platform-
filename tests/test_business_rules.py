import pytest
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from lending.models import Loan, Profile, Offer, Payment
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestBusinessRules:
    """Test specific business rules and constraints"""
    
    def test_interest_calculation_accuracy(self):
        """Test that interest calculations are mathematically accurate"""
        print("\n=== Testing Interest Calculation Accuracy ===")
        
        # Create a user for the loan
        user = User.objects.create_user('testuser', 'test@test.com', 'password')
        
        # Test case 1: 0% interest (simple division)
        loan1 = Loan(borrower=user, amount=Decimal('1200.00'), term_months=12, interest_rate=None)
        monthly1 = loan1.monthly_payment_amount()
        assert monthly1 == Decimal('100.00')  # 1200 / 12 = 100
        print(f"✓ 0% interest: {monthly1}")
        
        # Test case 2: 12% APR (standard calculation)
        loan2 = Loan(borrower=user, amount=Decimal('1000.00'), term_months=12, interest_rate=Decimal('12.00'))
        monthly2 = loan2.monthly_payment_amount()
        # Standard formula: P * r * (1+r)^n / ((1+r)^n - 1)
        expected = Decimal('88.85')  # Verified with financial calculator
        assert abs(monthly2 - expected) < Decimal('0.10')  # Allow small rounding difference
        print(f"✓ 12% APR: {monthly2} (expected ~{expected})")
        
        # Test case 3: 24% APR for 36 months
        loan3 = Loan(borrower=user, amount=Decimal('5000.00'), term_months=36, interest_rate=Decimal('24.00'))
        monthly3 = loan3.monthly_payment_amount()
        assert monthly3 > Decimal('150.00')  # Should be reasonable
        assert monthly3 * 36 > Decimal('5000.00')  # Total should exceed principal
        print(f"✓ 24% APR 36mo: {monthly3}")
    
    def test_loan_to_value_ratios(self):
        """Test implied LTV ratios (if you add borrower credit limits)"""
        print("\n=== Testing Loan-to-Value Considerations ===")
        
        # This would test if you add credit limits for borrowers
        borrower = User.objects.create_user('testborrower', 'test@test.com', 'pass')
        profile = Profile.objects.create(user=borrower, balance=Decimal('5000.00'))
        
        # Example: Maximum loan amount based on borrower profile
        # You could implement this as a business rule
        max_loan_amount = profile.balance * Decimal('2.00')  # Example: 2x balance
        
        reasonable_loan = Loan(borrower=borrower, amount=Decimal('8000.00'), term_months=12)
        excessive_loan = Loan(borrower=borrower, amount=Decimal('20000.00'), term_months=12)
        
        # This would fail if you implement LTV checks
        # assert reasonable_loan.amount <= max_loan_amount
        # assert excessive_loan.amount > max_loan_amount
        
        print("✓ LTV considerations noted for future implementation")
    
    def test_payment_scheduling(self):
        """Test payment schedule generation"""
        print("\n=== Testing Payment Scheduling ===")
        
        # Create a user for the loan
        user = User.objects.create_user('testuser', 'test@test.com', 'password')
        
        loan = Loan.objects.create(
            borrower=user,  # Add the required borrower field
            amount=Decimal('6000.00'),
            term_months=6,
            interest_rate=Decimal('10.00'),
            status='FUNDED'
        )
        
        # Generate payment schedule
        monthly_payment = loan.monthly_payment_amount()
        
        # Create payments (as your FundLoanView does)
        for i in range(loan.term_months):
            Payment.objects.create(
                loan=loan,
                due_date=date.today() + timedelta(days=30 * (i + 1)),
                amount=monthly_payment
            )
        
        payments = Payment.objects.filter(loan=loan)
        assert payments.count() == 6
        
        # Verify payment amounts are consistent
        for payment in payments:
            assert payment.amount == monthly_payment
        
        total_payments = sum(p.amount for p in payments)
        # Total should be more than principal due to interest
        assert total_payments > loan.amount
        
        print(f"✓ Payment schedule: {payments.count()} payments of {monthly_payment}")
        print(f"✓ Total repayment: {total_payments} vs principal: {loan.amount}")