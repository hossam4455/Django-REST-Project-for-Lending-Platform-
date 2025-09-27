from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import logging

from .models import Loan, Payment, Profile, Transaction
from .utils import send_payment_reminder, send_overdue_notification

logger = logging.getLogger(__name__)

@shared_task
def process_due_payments():
    """
    Process due payments automatically every hour.
    Attempts to automatically collect payments from borrower's balance.
    """
    logger.info("Starting due payments processing...")
    
    today = timezone.now().date()
    due_payments = Payment.objects.filter(
        due_date__lte=today,
        paid=False,
        loan__status='FUNDED'
    ).select_related('loan', 'loan__borrower', 'loan__lender')
    
    processed_count = 0
    successful_count = 0
    
    for payment in due_payments:
        processed_count += 1
        try:
            with transaction.atomic():
                borrower_profile = Profile.objects.get(user=payment.loan.borrower)
                lender_profile = Profile.objects.get(user=payment.loan.lender)
                
                # Check if borrower has sufficient balance
                if borrower_profile.balance >= payment.amount:
                    # Process payment automatically
                    borrower_profile.balance -= payment.amount
                    borrower_profile.save()
                    
                    lender_profile.balance += payment.amount
                    lender_profile.save()
                    
                    payment.paid = True
                    payment.paid_at = timezone.now()
                    payment.save()
                    
                    # Record transaction
                    Transaction.objects.create(
                        from_user=payment.loan.borrower,
                        to_user=payment.loan.lender,
                        amount=payment.amount,
                        note=f'Automatic monthly payment for loan {payment.loan.id}'
                    )
                    
                    logger.info(f"Successfully processed payment {payment.id} for loan {payment.loan.id}")
                    successful_count += 1
                    
                    # Send payment confirmation
                    send_payment_reminder(payment.loan.borrower.email, payment, automatic=True)
                    
                else:
                    logger.warning(f"Insufficient balance for automatic payment {payment.id}")
                    # Send reminder to borrower
                    send_payment_reminder(payment.loan.borrower.email, payment, due=True)
                    
        except Exception as e:
            logger.error(f"Error processing payment {payment.id}: {str(e)}")
            continue
    
    logger.info(f"Due payments processing completed. Processed: {processed_count}, Successful: {successful_count}")
    return {
        'processed': processed_count,
        'successful': successful_count,
        'timestamp': timezone.now().isoformat()
    }

@shared_task
def check_overdue_payments():
    """
    Check for overdue payments and send notifications.
    Also apply late fees if configured.
    """
    logger.info("Checking for overdue payments...")
    
    today = timezone.now().date()
    overdue_days = 7  # Consider payments overdue after 7 days
    
    overdue_date = today - timedelta(days=overdue_days)
    overdue_payments = Payment.objects.filter(
        due_date__lte=overdue_date,
        paid=False,
        loan__status='FUNDED'
    ).select_related('loan', 'loan__borrower')
    
    overdue_count = 0
    notified_count = 0
    
    for payment in overdue_payments:
        overdue_count += 1
        
        # Calculate late fee (5% of payment amount or $10, whichever is higher)
        late_fee = max(payment.amount * Decimal('0.05'), Decimal('10.00'))
        
        # Check if late fee already applied
        if not hasattr(payment, 'late_fee_applied') or not payment.late_fee_applied:
            payment.late_fee = late_fee
            payment.late_fee_applied = True
            payment.save()
            
            logger.info(f"Applied late fee of {late_fee} to payment {payment.id}")
        
        # Send overdue notification
        try:
            send_overdue_notification(
                payment.loan.borrower.email,
                payment,
                late_fee
            )
            notified_count += 1
        except Exception as e:
            logger.error(f"Error sending overdue notification for payment {payment.id}: {str(e)}")
    
    logger.info(f"Overdue check completed. Overdue: {overdue_count}, Notified: {notified_count}")
    return {
        'overdue': overdue_count,
        'notified': notified_count,
        'timestamp': timezone.now().isoformat()
    }

@shared_task
def update_loan_statuses():
    """
    Update loan statuses based on payment progress.
    Mark loans as COMPLETED when all payments are made.
    """
    logger.info("Updating loan statuses...")
    
    funded_loans = Loan.objects.filter(status='FUNDED')
    updated_count = 0
    completed_count = 0
    
    for loan in funded_loans:
        total_payments = Payment.objects.filter(loan=loan).count()
        paid_payments = Payment.objects.filter(loan=loan, paid=True).count()
        
        if total_payments > 0 and paid_payments == total_payments:
            # All payments completed
            loan.status = 'COMPLETED'
            loan.save()
            completed_count += 1
            logger.info(f"Loan {loan.id} marked as COMPLETED")
        elif paid_payments > 0:
            # Some payments made, but not all
            # You could add a 'PARTIALLY_PAID' status if needed
            pass
        
        updated_count += 1
    
    # Also check for loans that should be marked as DEFAULTED
    # (e.g., too many overdue payments)
    defaulted_loans = check_and_mark_defaulted_loans()
    
    logger.info(f"Loan status update completed. Updated: {updated_count}, Completed: {completed_count}, Defaulted: {len(defaulted_loans)}")
    return {
        'updated': updated_count,
        'completed': completed_count,
        'defaulted': len(defaulted_loans),
        'timestamp': timezone.now().isoformat()
    }

@shared_task
def process_single_payment(payment_id):
    """
    Process a single payment (can be called manually for retries)
    """
    try:
        payment = Payment.objects.get(id=payment_id, paid=False)
        
        with transaction.atomic():
            borrower_profile = Profile.objects.get(user=payment.loan.borrower)
            lender_profile = Profile.objects.get(user=payment.loan.lender)
            
            if borrower_profile.balance >= payment.amount:
                borrower_profile.balance -= payment.amount
                borrower_profile.save()
                
                lender_profile.balance += payment.amount
                lender_profile.save()
                
                payment.paid = True
                payment.paid_at = timezone.now()
                payment.save()
                
                Transaction.objects.create(
                    from_user=payment.loan.borrower,
                    to_user=payment.loan.lender,
                    amount=payment.amount,
                    note=f'Manual retry payment for loan {payment.loan.id}'
                )
                
                logger.info(f"Successfully processed payment {payment_id}")
                return {'success': True, 'payment_id': payment_id}
            else:
                logger.warning(f"Insufficient balance for payment {payment_id}")
                return {'success': False, 'reason': 'insufficient_balance'}
                
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found or already paid")
        return {'success': False, 'reason': 'not_found'}
    except Exception as e:
        logger.error(f"Error processing payment {payment_id}: {str(e)}")
        return {'success': False, 'reason': 'error', 'error': str(e)}

def check_and_mark_defaulted_loans():
    """
    Check for loans that should be marked as defaulted
    (e.g., 30+ days overdue on multiple payments)
    """
    today = timezone.now().date()
    default_threshold = 30  # days
    
    default_candidates = Loan.objects.filter(
        status='FUNDED',
        payments__due_date__lte=today - timedelta(days=default_threshold),
        payments__paid=False
    ).distinct()
    
    defaulted_loans = []
    
    for loan in default_candidates:
        # Check if multiple payments are severely overdue
        severely_overdue = Payment.objects.filter(
            loan=loan,
            due_date__lte=today - timedelta(days=default_threshold),
            paid=False
        ).count()
        
        if severely_overdue >= 2:  # At least 2 payments severely overdue
            loan.status = 'DEFAULTED'
            loan.save()
            defaulted_loans.append(loan)
            logger.warning(f"Loan {loan.id} marked as DEFAULTED")
    
    return defaulted_loans