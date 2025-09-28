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

# In lending/views.py - Temporary fix for SubmitOfferView

class SubmitOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)
        
        if loan.status != 'OPEN':
            return Response(
                {'detail': 'Loan not open for offers'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

        total_needed = loan.amount + loan.lenme_fee
        

        try:
            lender_profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {'detail': 'Lender profile not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
 
        if not lender_profile.has_sufficient_funds(total_needed):
            return Response(
                {'detail': f'Insufficient funds. Available: ${lender_profile.available_balance()}, Needed: ${total_needed}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        existing_offer = Offer.objects.filter(
            loan=loan, 
            lender=request.user, 
            status__in=['PENDING', 'ACCEPTED']
        ).first()
        
        if existing_offer:
            return Response(
                {'detail': 'You already have an active offer for this loan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        try:
            with transaction.atomic():
              
                if not lender_profile.reserve_funds(total_needed):
                    return Response(
                        {'detail': 'Failed to reserve funds'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
               
                offer = Offer.objects.create(
                    loan=loan,
                    lender=request.user,
                    interest_rate=Decimal('15.00'),  
                    reserved_amount=total_needed,
                    status='PENDING'
                )
                
           
                loan.status = 'OFFERED'
                loan.interest_rate = Decimal('15.00')
                loan.save()
                
                return Response({
                    'detail': 'Offer submitted successfully. Funds reserved.',
                    'offer_id': offer.id,
                    'reserved_amount': str(total_needed),
                    'available_balance': str(lender_profile.available_balance())
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'detail': f'Error creating offer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)
        offers = Offer.objects.filter(loan=loan).exclude(status='REJECTED')
        serializer = OfferSerializer(offers, many=True)
        return Response(serializer.data)

# In lending/views.py - Fix the AcceptOfferView
class AcceptOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)
        
        if loan.status != 'OFFERED':
            return Response(
                {'detail': 'Loan not in offered state'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the best pending offer (lowest interest rate, earliest created)
        offer = Offer.objects.filter(
            loan=loan, 
            status='PENDING'
        ).order_by('interest_rate', 'created_at').first()
        
        if not offer:
            return Response(
                {'detail': 'No pending offers found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            with transaction.atomic():
                # Get profiles
                lender_profile = Profile.objects.get(user=offer.lender)
                borrower_profile = Profile.objects.get(user=loan.borrower)
                
                total_needed = loan.amount + loan.lenme_fee
                

               
                
                # Check if lender has sufficient funds
                if lender_profile.balance < total_needed:
                    return Response(
                        {'detail': f'Lender has insufficient funds. Available: ${lender_profile.balance}, Needed: ${total_needed}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Transfer funds directly 
                lender_profile.balance -= total_needed
                lender_profile.save()
                
                borrower_profile.balance += loan.amount  
                
            
                offer.status = 'ACCEPTED'
                offer.save()
                
               
                loan.status = 'ACCEPTED'
                loan.lender = offer.lender
                loan.save()
                
               
                other_offers = Offer.objects.filter(
                    loan=loan, 
                    status='PENDING'
                ).exclude(id=offer.id)
                
                for other_offer in other_offers:
                    # Release any reserved funds for rejected offers
                    try:
                        other_lender_profile = Profile.objects.get(user=other_offer.lender)
                        if other_lender_profile.reserved_balance >= other_offer.reserved_amount:
                            other_lender_profile.reserved_balance -= other_offer.reserved_amount
                            other_lender_profile.save()
                    except Profile.DoesNotExist:
                        pass
                    
                    other_offer.status = 'REJECTED'
                    other_offer.save()
                
               
                lender_profile.refresh_from_db()
                borrower_profile.refresh_from_db()
             
                
                return Response({
                    'detail': 'Offer accepted successfully. Funds transferred.',
                    'loan_id': loan.id,
                    'accepted_offer_id': offer.id,
                    'lender': offer.lender.username,
                    'amount_transferred': str(loan.amount),
                    'fee_paid': str(loan.lenme_fee),
                    'lender_new_balance': str(lender_profile.balance),
                    'borrower_new_balance': str(borrower_profile.balance)
                })
                
        except Exception as e:
            print(f"DEBUG: Error in AcceptOfferView: {str(e)}")
            return Response(
                {'detail': f'Error accepting offer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 # In lending/views.py - Add RejectOfferView
class RejectOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id, offer_id):
        loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)
        offer = get_object_or_404(Offer, pk=offer_id, loan=loan, status='PENDING')
        
        try:
            with transaction.atomic():
                # Release reserved funds back to lender
                lender_profile = Profile.objects.get(user=offer.lender)
                if lender_profile.release_funds(offer.reserved_amount):
                    offer.status = 'REJECTED'
                    offer.save()
                    
                    # If this was the only offer, set loan back to OPEN
                    pending_offers = Offer.objects.filter(loan=loan, status='PENDING')
                    if not pending_offers.exists():
                        loan.status = 'OPEN'
                        loan.save()
                    
                    return Response({
                        'detail': 'Offer rejected. Funds released back to lender.',
                        'released_amount': str(offer.reserved_amount)
                    })
                else:
                    return Response(
                        {'detail': 'Failed to release funds'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        except Exception as e:
            return Response(
                {'detail': f'Error rejecting offer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class FundLoanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id, lender=request.user, status='ACCEPTED')
        
        # Check if lender has sufficient funds
        lender_profile = Profile.objects.get(user=request.user)
        total_needed = loan.amount + loan.lenme_fee
        
        if lender_profile.balance < total_needed:
            return Response(
                {'detail': f'Insufficient funds. Available: ${lender_profile.balance}, Needed: ${total_needed}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Transfer funds (if not already done in acceptance)
                if lender_profile.balance >= total_needed:
                    lender_profile.balance -= total_needed
                    lender_profile.save()
                    
                    borrower_profile = Profile.objects.get(user=loan.borrower)
                    borrower_profile.balance += loan.amount
                    borrower_profile.save()
                
                loan.status = 'FUNDED'
                loan.funded_at = timezone.now()
                loan.save()

                # Create payment schedule
                monthly_amount = loan.monthly_payment_amount()
                start_date = loan.funded_at.date()
                for i in range(loan.term_months):
                    due_date = start_date + timedelta(days=30 * (i + 1))
                    Payment.objects.create(
                        loan=loan,
                        due_date=due_date,
                        amount=monthly_amount
                    )

                return Response({
                    'detail': 'Loan funded successfully. Payment schedule created.',
                    'loan_id': loan.id,
                    'monthly_payment': str(monthly_amount),
                    'total_payments': loan.term_months
                })
                
        except Exception as e:
            return Response(
                {'detail': f'Error funding loan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
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