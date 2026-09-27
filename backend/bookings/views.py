import json, razorpay
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Booking

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
def create_order(request):
    data = request.data
    amount = int(data['amount']) * 100
    razorpay_order = client.order.create({"amount": amount, "currency": "INR", "payment_capture": "1"})
    Booking.objects.create(name=data['name'], phone=data['phone'], plan_type=data['plan_type'], amount=data['amount'], razorpay_order_id=razorpay_order['id'])
    return Response({'order_id': razorpay_order['id'], 'amount': razorpay_order['amount'], 'currency': 'INR'})

@api_view(['POST'])
def verify_payment(request):
    data = request.data
    try:
        client.utility.verify_payment_signature({'razorpay_order_id': data['razorpay_order_id'], 'razorpay_payment_id': data['razorpay_payment_id'], 'razorpay_signature': data['razorpay_signature']})
        booking = Booking.objects.get(razorpay_order_id=data['razorpay_order_id'])
        booking.razorpay_payment_id, booking.razorpay_signature, booking.is_paid = data['razorpay_payment_id'], data['razorpay_signature'], True
        booking.save()
        return Response({'status': 'Success'})
    except Exception as e: return Response({'status': 'Failed', 'message': str(e)}, status=400)

@csrf_exempt
def razorpay_webhook(request):
    if request.method == 'POST':
        webhook_body, webhook_signature = request.body.decode('utf-8'), request.headers.get('X-Razorpay-Signature')
        try: client.utility.verify_webhook_signature(webhook_body, webhook_signature, settings.RAZORPAY_WEBHOOK_SECRET)
        except razorpay.errors.SignatureVerificationError: return HttpResponse(status=400)
        payload = json.loads(webhook_body)
        if payload.get('event') == 'order.paid':
            payment_entity = payload['payload']['payment']['entity']
            try:
                booking = Booking.objects.get(razorpay_order_id=payment_entity['order_id'])
                if not booking.is_paid:
                    booking.razorpay_payment_id, booking.is_paid = payment_entity['id'], True
                    booking.save()
            except Booking.DoesNotExist: pass
        return HttpResponse(status=200)
    return HttpResponse(status=405)
