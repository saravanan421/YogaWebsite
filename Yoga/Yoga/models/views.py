import razorpay
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import Booking

# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
def create_order(request):
    data = request.data
    amount = int(data['amount']) * 100 # Razorpay requires amount in paise
    
    # 1. Create order in Razorpay
    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1" # Auto-capture
    })
    
    # 2. Save booking in database with the generated order ID
    booking = Booking.objects.create(
        name=data['name'],
        phone=data['phone'],
        plan_type=data['plan_type'],
        amount=data['amount'],
        razorpay_order_id=razorpay_order['id']
    )
    
    return Response({
        'order_id': razorpay_order['id'],
        'amount': razorpay_order['amount'],
        'currency': 'INR'
    })

@api_view(['POST'])
def verify_payment(request):
    data = request.data
    try:
        # 1. Verify signature with Razorpay
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        
        # 2. Update database to mark as paid
        booking = Booking.objects.get(razorpay_order_id=data['razorpay_order_id'])
        booking.razorpay_payment_id = data['razorpay_payment_id']
        booking.razorpay_signature = data['razorpay_signature']
        booking.is_paid = True
        booking.save()
        
        return Response({'status': 'Success', 'message': 'Payment successful'})
    except Exception as e:
        return Response({'status': 'Failed', 'message': str(e)}, status=400)