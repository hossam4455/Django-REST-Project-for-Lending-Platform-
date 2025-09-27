from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.db import transaction

from .models import Loan, Profile, Payment, Transaction, Offer
from .serializers import LoanSerializer, CreateLoanSerializer, OfferSerializer, PaymentSerializer

class LoanCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateLoanSerializer

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user)
class SubmitOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)
        if loan.status not in ['OPEN', 'OFFERED']:  # Allow offers in OFFERED state too
            return Response({'detail': 'Loan not open for offers'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OfferSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user already has an open offer for this loan
            existing_offer = Offer.objects.filter(
                loan=loan, 
                lender=request.user, 
                status='OPEN'
            ).first()
            
            if existing_offer:
                # Update existing offer instead of creating new one
                existing_offer.interest_rate = serializer.validated_data['interest_rate']
                existing_offer.save()
                offer = existing_offer
                action = 'updated'
            else:
                # Create new offer
                offer = Offer.objects.create(
                    loan=loan,
                    lender=request.user,
                    interest_rate=serializer.validated_data['interest_rate']
                )
                action = 'submitted'
            
            # Update loan to OFFERED status if it was OPEN
            # Update interest rate if this offer has a better rate
            if loan.status == 'OPEN' or serializer.validated_data['interest_rate'] < loan.interest_rate:
                loan.status = 'OFFERED'
                loan.interest_rate = serializer.validated_data['interest_rate']
                loan.save()
            
            return Response({
                'detail': f'Offer {action}', 
                'offer_id': offer.id,
                'action': action
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)
        offers = Offer.objects.filter(loan=loan, status='OPEN')
        serializer = OfferSerializer(offers, many=True)
        return Response(serializer.data)
class AcceptOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)
        if loan.status != 'OFFERED':
            return Response({'detail': 'Loan not in offered state'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the specific offer to accept (from request data)
        offer_id = request.data.get('offer_id')
        if not offer_id:
            return Response({'detail': 'offer_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        offer = get_object_or_404(Offer, pk=offer_id, loan=loan, status='OPEN')
        
        loan.status = 'ACCEPTED'
        loan.lender = offer.lender
        loan.interest_rate = offer.interest_rate  # Use the offer's rate
        loan.save()
        
        # Update offer status
        offer.status = 'ACCEPTED'
        offer.save()
        
        # Reject all other open offers for this loan
        Offer.objects.filter(loan=loan, status='OPEN').exclude(id=offer.id).update(status='REJECTED')
        
        return Response({'detail': 'Offer accepted', 'loan_id': loan.id})
class FundLoanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id, lender=request.user, status='ACCEPTED')
        profile = Profile.objects.get(user=request.user)
        total_needed = loan.total_loan_amount()
        
        if profile.balance < total_needed:
            return Response({'detail': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        # Use atomic transaction for data consistency
        with transaction.atomic():
            profile.balance -= total_needed
            profile.save()

            borrower_profile, _ = Profile.objects.get_or_create(user=loan.borrower)
            borrower_profile.balance += loan.amount
            borrower_profile.save()

            Transaction.objects.create(from_user=request.user, to_user=loan.borrower, amount=loan.amount, note='Loan funded (principal)')
            Transaction.objects.create(from_user=request.user, to_user=None, amount=loan.lenme_fee, note='Lenme fee')

            loan.status = 'FUNDED'
            loan.funded_at = timezone.now()
            loan.save()

            # Create payment schedule
            monthly_amount = loan.monthly_payment_amount()
            start_date = loan.funded_at.date()
            for i in range(loan.term_months):
                due_date = start_date + timedelta(days=30 * (i + 1))
                Payment.objects.create(loan=loan, due_date=due_date, amount=monthly_amount)

        return Response({'detail': 'Loan funded', 'loan_id': loan.id})

class MakePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id, payment_id):
        loan = get_object_or_404(Loan, pk=loan_id)
        payment = get_object_or_404(Payment, pk=payment_id, loan=loan)
        
        if loan.borrower != request.user:
            return Response({'detail': 'Not borrower'}, status=status.HTTP_403_FORBIDDEN)
        if payment.paid:
            return Response({'detail': 'Already paid'}, status=status.HTTP_400_BAD_REQUEST)

        borrower_profile = Profile.objects.get(user=request.user)
        if borrower_profile.balance < payment.amount:
            return Response({'detail': 'Insufficient borrower balance'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                borrower_profile.balance -= payment.amount
                borrower_profile.save()

                lender_profile = Profile.objects.get(user=loan.lender)
                lender_profile.balance += payment.amount
                lender_profile.save()

                payment.paid = True
                payment.paid_at = timezone.now()
                payment.save()

                Transaction.objects.create(from_user=request.user, to_user=loan.lender, amount=payment.amount, note='Monthly payment')
        except Exception as e:
            return Response({'detail': 'Payment failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Payment successful', 'payment_id': payment.id})

class AvailableLoansView(generics.ListAPIView):
    """Get loans that don't have lenders (available for funding)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    
    def get_queryset(self):
        return Loan.objects.filter(lender__isnull=True, status='OFFERED')