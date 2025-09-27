from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_payment_reminder(user_email, payment, due=False, automatic=False):
    """
    Send payment reminder or confirmation email
    """
    try:
        if automatic and payment.paid:
            subject = 'Payment Processed Successfully'
            message = f'''
            Your monthly payment of ${payment.amount} for loan #{payment.loan.id} 
            has been automatically processed successfully.
            
            Payment Date: {payment.paid_at.strftime("%Y-%m-%d")}
            Thank you for your timely payment!
            '''
        elif due:
            subject = 'Payment Due Reminder'
            message = f'''
            Friendly reminder: Your payment of ${payment.amount} for loan #{payment.loan.id} 
            is due on {payment.due_date.strftime("%Y-%m-%d")}.
            
            Please ensure sufficient funds are available in your account for automatic processing.
            '''
        else:
            subject = 'Payment Processing Attempt'
            message = f'''
            We attempted to process your payment of ${payment.amount} for loan #{payment.loan.id},
            but there were insufficient funds in your account.
            
            Please add funds to your account to avoid late fees.
            '''
        
        # In production, you would actually send the email
        logger.info(f"Would send email to {user_email}: {subject}")
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
        
    except Exception as e:
        logger.error(f"Error sending payment reminder: {str(e)}")

def send_overdue_notification(user_email, payment, late_fee):
    """
    Send overdue payment notification with late fee information
    """
    try:
        subject = 'Payment Overdue Notification'
        message = f'''
        IMPORTANT: Your payment of ${payment.amount} for loan #{payment.loan.id} 
        is overdue. A late fee of ${late_fee} has been applied.
        
        Original Due Date: {payment.due_date.strftime("%Y-%m-%d")}
        Late Fee: ${late_fee}
        Total Amount Due: ${payment.amount + late_fee}
        
        Please make the payment immediately to avoid further penalties.
        '''
        
        logger.info(f"Would send overdue notification to {user_email}")
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
        
    except Exception as e:
        logger.error(f"Error sending overdue notification: {str(e)}")