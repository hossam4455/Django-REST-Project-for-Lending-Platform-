from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )

    def __str__(self):
        return f"Profile({self.user.username})"

class Loan(models.Model):
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open'),
        ('OFFERED', 'Offered'),
        ('ACCEPTED', 'Accepted'),
        ('FUNDED', 'Funded'),
        ('COMPLETED', 'Completed'),
    ]
    borrower = models.ForeignKey(
        User, related_name='borrowed_loans', on_delete=models.CASCADE
    )
    lender = models.ForeignKey(
        User, related_name='funded_loans', on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term_months = models.PositiveIntegerField()
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Annual percent rate (APR)'
    )
    lenme_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    funded_at = models.DateTimeField(null=True, blank=True)

    def total_loan_amount(self):
        return (self.amount + self.lenme_fee)

    def monthly_payment_amount(self):
        if not self.interest_rate:
            return self.amount / self.term_months
        r = (self.interest_rate / Decimal('100.0')) / Decimal('12.0')
        n = Decimal(self.term_months)
        numerator = self.amount * r * (1 + r) ** n
        denominator = ((1 + r) ** n) - 1
        if denominator == 0:
            return self.amount / n
        return (numerator / denominator).quantize(Decimal('0.01'))

    def __str__(self):
        return f"Loan({self.pk}) {self.amount} by {self.borrower.username} status={self.status}"

class Offer(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    lender = models.ForeignKey(User, on_delete=models.CASCADE)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer({self.pk}) {self.interest_rate}% by {self.lender.username}"

class Payment(models.Model):
    loan = models.ForeignKey(
        Loan, related_name='payments', on_delete=models.CASCADE
    )
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment(loan={self.loan.pk}, due={self.due_date}, paid={self.paid})"

class Transaction(models.Model):
    from_user = models.ForeignKey(
        User, related_name='outgoing_tx', on_delete=models.SET_NULL, null=True, blank=True
    )
    to_user = models.ForeignKey(
        User, related_name='incoming_tx', on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tx {self.id}: {self.amount} from {self.from_user} to {self.to_user}"