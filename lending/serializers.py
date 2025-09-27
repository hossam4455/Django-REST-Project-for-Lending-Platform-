from rest_framework import serializers
from decimal import Decimal
from .models import Loan, Offer, Payment

class CreateLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['amount', 'term_months', 'interest_rate']
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than zero.")
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError("Amount cannot exceed 1,000,000.00")
        return value
    
    def validate_term_months(self, value):
        if value <= 0:
            raise serializers.ValidationError("Term must be at least 1 month.")
        if value > 360:
            raise serializers.ValidationError("Term cannot exceed 360 months.")
        return value
    
    def validate_interest_rate(self, value):
        if value is not None:
            if value < Decimal('0.00'):
                raise serializers.ValidationError("Interest rate cannot be negative.")
            if value > Decimal('50.00'):
                raise serializers.ValidationError("Interest rate cannot exceed 50%.")
        return value
    
    def create(self, validated_data):
        # Set the borrower from the authenticated user
        validated_data['borrower'] = self.context['request'].user
        return super().create(validated_data)

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'
        read_only_fields = ['id', 'loan', 'lender', 'status', 'created_at']
    
    def validate_interest_rate(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Interest rate must be greater than zero.")
        if value > Decimal('50.00'):
            raise serializers.ValidationError("Interest rate cannot exceed 50%.")
        return value

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'