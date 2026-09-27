import React, { useState } from 'react';
import axios from 'axios';

const BookingForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    plan_type: 'Monthly',
    amount: 1999
  });

  const handlePlanChange = (e) => {
    const plans = { 'Monthly': 1999, 'Quarterly': 4999, 'Half-yearly': 8999 };
    const selectedPlan = e.target.value;
    setFormData({ ...formData, plan_type: selectedPlan, amount: plans[selectedPlan] });
  };

  const displayRazorpay = async (e) => {
    e.preventDefault();

    // 1. Request an Order ID from your Django backend
    const { data } = await axios.post('http://localhost:8000/api/create-order/', formData);

    // 2. Configure Razorpay Checkout options
    const options = {
      key: "rzp_test_your_key_here", // Must match backend environment
      amount: data.amount,
      currency: data.currency,
      name: "Yoga Classes",
      description: `${formData.plan_type} Subscription`,
      order_id: data.order_id,
      handler: async function (response) {
        // 3. Send successful payment details back to Django for verification
        try {
          const verifyResult = await axios.post('http://localhost:8000/api/verify-payment/', {
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature
          });
          alert('Registration successful! Welcome to the class.');
        } catch (error) {
          alert('Payment verification failed.');
        }
      },
      prefill: {
        name: formData.name,
        contact: formData.phone,
      },
      theme: {
        color: "#6b7280" // Slate gray to match typical wellness themes
      }
    };

    // 4. Open the Razorpay popup
    const paymentObject = new window.Razorpay(options);
    paymentObject.open();
  };

  return (
    <form onSubmit={displayRazorpay} style={{ maxWidth: '400px', margin: 'auto', display: 'flex', flexDirection: 'column', gap: '15px' }}>
      <h2>Register for Classes</h2>
      
      <input 
        type="text" 
        placeholder="Full Name" 
        required 
        value={formData.name}
        onChange={(e) => setFormData({...formData, name: e.target.value})}
      />
      
      <input 
        type="tel" 
        placeholder="WhatsApp/Phone No." 
        required 
        value={formData.phone}
        onChange={(e) => setFormData({...formData, phone: e.target.value})}
      />
      
      <select value={formData.plan_type} onChange={handlePlanChange}>
        <option value="Monthly">Monthly - ₹1999</option>
        <option value="Quarterly">Quarterly - ₹4999</option>
        <option value="Half-yearly">Half-yearly - ₹8999</option>
      </select>

      <button type="submit" style={{ padding: '10px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px' }}>
        Pay ₹{formData.amount}
      </button>
    </form>
  );
};

export default BookingForm;