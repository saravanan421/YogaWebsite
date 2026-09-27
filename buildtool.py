import os
import zipfile

# Define the project structure and file contents
files_to_create = {
    # BACKEND FILES
    "backend/requirements.txt": """django
djangorestframework
razorpay
django-cors-headers
""",
    "backend/yoga_backend/settings.py": """import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-test-key'
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'bookings',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'yoga_backend.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',],},},]
WSGI_APPLICATION = 'yoga_backend.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3',}}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True
RAZORPAY_KEY_ID = 'rzp_test_your_key_here'
RAZORPAY_KEY_SECRET = 'your_secret_here'
RAZORPAY_WEBHOOK_SECRET = 'your_webhook_secret_here'
""",
    "backend/yoga_backend/urls.py": """from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bookings.urls')),
]
""",
    "backend/bookings/models.py": """from django.db import models
class Booking(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    plan_type = models.CharField(max_length=50)
    amount = models.IntegerField()
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} - {self.plan_type} - Paid: {self.is_paid}"
""",
    "backend/bookings/views.py": """import json, razorpay
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
""",
    "backend/bookings/urls.py": """from django.urls import path
from .views import create_order, verify_payment, razorpay_webhook
urlpatterns = [
    path('api/create-order/', create_order),
    path('api/verify-payment/', verify_payment),
    path('api/webhook/razorpay/', razorpay_webhook),
]
""",
    "backend/manage.py": """#!/usr/bin/env python
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yoga_backend.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__ == '__main__': main()
""",

    # FRONTEND FILES
    "frontend/package.json": """{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": { "dev": "vite", "build": "vite build", "preview": "vite preview" },
  "dependencies": { "axios": "^1.6.8", "react": "^18.2.0", "react-dom": "^18.2.0" },
  "devDependencies": { "@vitejs/plugin-react": "^4.2.1", "vite": "^5.2.0" }
}
""",
    "frontend/index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Yoga Registration</title>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
    "frontend/vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ plugins: [react()] })
""",
    "frontend/src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
""",
    "frontend/src/App.jsx": """import React from 'react';
import BookingForm from './BookingForm';
function App() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px', fontFamily: 'sans-serif' }}>
      <BookingForm />
    </div>
  );
}
export default App;
""",
    "frontend/src/BookingForm.jsx": """import React, { useState } from 'react';
import axios from 'axios';

const BookingForm = () => {
  const [formData, setFormData] = useState({ name: '', phone: '', plan_type: 'Monthly', amount: 1999 });

  const handlePlanChange = (e) => {
    const plans = { 'Monthly': 1999, 'Quarterly': 4999, 'Half-yearly': 8999 };
    setFormData({ ...formData, plan_type: e.target.value, amount: plans[e.target.value] });
  };

  const displayRazorpay = async (e) => {
    e.preventDefault();
    const { data } = await axios.post('http://localhost:8000/api/create-order/', formData);

    const options = {
      key: "rzp_test_your_key_here",
      amount: data.amount,
      currency: data.currency,
      name: "Yoga Classes",
      description: `${formData.plan_type} Subscription`,
      order_id: data.order_id,
      handler: async function (response) {
        try {
          await axios.post('http://localhost:8000/api/verify-payment/', response);
          alert('Registration successful! Welcome to the class.');
        } catch { alert('Payment verification failed.'); }
      },
      prefill: { name: formData.name, contact: formData.phone },
      theme: { color: "#6b7280" }
    };

    const paymentObject = new window.Razorpay(options);
    paymentObject.open();
  };

  return (
    <form onSubmit={displayRazorpay} style={{ width: '400px', display: 'flex', flexDirection: 'column', gap: '15px', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2 style={{ textAlign: 'center' }}>Register for Classes</h2>
      <input type="text" placeholder="Full Name" required value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} style={{ padding: '10px' }} />
      <input type="tel" placeholder="WhatsApp/Phone No." required value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} style={{ padding: '10px' }} />
      <select value={formData.plan_type} onChange={handlePlanChange} style={{ padding: '10px' }}>
        <option value="Monthly">Monthly - ₹1999</option>
        <option value="Quarterly">Quarterly - ₹4999</option>
        <option value="Half-yearly">Half-yearly - ₹8999</option>
      </select>
      <button type="submit" style={{ padding: '12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>
        Pay ₹{formData.amount}
      </button>
    </form>
  );
};
export default BookingForm;
"""
}

def main():
    print("Creating project directories and files...")
    for filepath, content in files_to_create.items():
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w",encoding="utf-8") as f:
                f.write(content)
    # zip_filename = "shubhyogini_project.zip"
    # print(f"Archiving to {zip_filename}...")
    # with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    #     for root, _, files in os.walk("."):
    #         for file in files:
    #             if file != "build_project.py" and not file.endswith('.zip') and "__pycache__" not in root:
    #                 zipf.write(os.path.join(root, file))
                    
    print(f"\\nSuccess! Your complete project has been created and zipped into'.")
    print("You can extract the zip, or just use the generated 'backend' and 'frontend' folders directly.")

if __name__ == "__main__":
    main()