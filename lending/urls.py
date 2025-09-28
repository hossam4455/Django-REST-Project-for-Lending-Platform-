from django.urls import path
from .views import AvailableLoansView, LoanCreateView, RejectOfferView,SubmitOfferView, AcceptOfferView, FundLoanView, MakePaymentView




urlpatterns = [
    path('loans/', LoanCreateView.as_view(), name='create-loan'),
    path('loans/<int:loan_id>/offers/', SubmitOfferView.as_view(), name='submit-offer'),
    path('loans/<int:loan_id>/offers/<int:offer_id>/reject/', RejectOfferView.as_view(), name='reject-offer'),  # Add this
    path('loans/<int:loan_id>/accept/', AcceptOfferView.as_view(), name='accept-offer'),
    path('loans/<int:loan_id>/fund/', FundLoanView.as_view(), name='fund-loan'),
    path('loans/<int:loan_id>/payments/<int:payment_id>/pay/', MakePaymentView.as_view(), name='make-payment'),
]