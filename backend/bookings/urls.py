from django.urls import path
from .views import create_order, verify_payment, razorpay_webhook
urlpatterns = [
    path('api/create-order/', create_order),
    path('api/verify-payment/', verify_payment),
    path('api/webhook/razorpay/', razorpay_webhook),
]
