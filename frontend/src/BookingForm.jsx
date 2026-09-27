import React, { useState } from 'react';
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
