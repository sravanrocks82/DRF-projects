from django.urls import path
from .views import PaymentCreateView, PaymentStatusView, PaymentExecuteView, PaymentCancelView

urlpatterns = [
    path('payments/', PaymentCreateView.as_view(), name='initiate-payment'),
    path('payments/<int:pk>/', PaymentStatusView.as_view(), name='payment-status'),
    path('payment/execute/', PaymentExecuteView.as_view(), name='payment-execute'),
    path('payment/cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
]