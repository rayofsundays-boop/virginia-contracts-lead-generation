# Stripe Environment Variables - Quick Setup Card

## 🔑 Required Stripe Keys

Add these to your `.env` file locally and Render Environment tab in production:

### 1. API Keys (Get from Stripe Dashboard > Developers > API Keys)
```bash
# Client-side key (visible in HTML)
STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Server-side key (KEEP SECRET!)
STRIPE_SECRET_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Price IDs (Get from Stripe Dashboard > Products)

#### Create 4 Products in Stripe:

**Product 1: Monthly Subscription**
- Name: ContractLink Monthly
- Price: $99.00/month recurring
- Copy Price ID below:
```bash
STRIPE_MONTHLY_PRICE_ID=price_1xxxxxxxxxxxxxxxxxx
```

**Product 2: Annual Subscription**
- Name: ContractLink Annual  
- Price: $950.00/year recurring
- Copy Price ID below:
```bash
STRIPE_ANNUAL_PRICE_ID=price_1xxxxxxxxxxxxxxxxxx
```

**Product 3: Monthly WIN50 (50% off)**
- Name: ContractLink Monthly - WIN50 Promo
- Price: $49.50/month recurring
- Copy Price ID below:
```bash
STRIPE_MONTHLY_WIN50_PRICE_ID=price_1xxxxxxxxxxxxxxxxxx
```

**Product 4: Annual WIN50 (50% off)**
- Name: ContractLink Annual - WIN50 Promo
- Price: $475.00/year recurring
- Copy Price ID below:
```bash
STRIPE_ANNUAL_WIN50_PRICE_ID=price_1xxxxxxxxxxxxxxxxxx
```

---

## 📋 Quick Setup Steps

### Step 1: Create Stripe Account
1. Go to https://stripe.com/register
2. Sign up for free account
3. Verify email
4. Start in **Test Mode** (toggle in top-right)

### Step 2: Get API Keys
1. Go to **Developers** → **API Keys**
2. Copy **Publishable key** (starts with `pk_test_`)
3. Click "Reveal test key" under **Secret key**
4. Copy secret key (starts with `sk_test_`)
5. Add both to `.env` file

### Step 3: Create Products
1. Go to **Products** → **Add Product**
2. Create 4 products (see above)
3. For each product:
   - Click on the product
   - Copy the **Price ID** from the pricing section
   - Add to `.env` file

### Step 4: Add to Render
1. Go to Render Dashboard
2. Select your web service
3. Click **Environment** tab
4. Click **Add Environment Variable**
5. Add all 6 Stripe variables
6. Click **Save Changes** (triggers auto-deploy)

### Step 5: Test
1. Visit `https://your-app.onrender.com/checkout`
2. Select a plan
3. Enter test card: `4242 4242 4242 4242`
4. CVV: Any 3 digits
5. Expiry: Any future date
6. Complete payment → Should succeed!

---

## ✅ Verification Checklist

- [ ] Stripe account created
- [ ] Test mode enabled
- [ ] API keys copied and added to `.env`
- [ ] 4 products created in Stripe
- [ ] All 4 price IDs copied and added to `.env`
- [ ] Environment variables added to Render
- [ ] Test payment successful with test card
- [ ] Database shows subscription after payment
- [ ] User gains access to premium features

---

## 🧪 Test Cards

```
✅ Success:
Card: 4242 4242 4242 4242
CVV: Any 3 digits
Expiry: Any future date

❌ Declined:
Card: 4000 0000 0000 0002

🔐 Requires 3D Secure:
Card: 4000 0025 0000 3155
```

---

## 🚨 Troubleshooting

### Error: "Invalid API Key"
- Check if you copied the full key (no spaces)
- Verify you're using test keys in test mode
- Restart Flask app after adding keys

### Error: "No such price"
- Double-check price IDs in Stripe Dashboard
- Ensure price is set to **recurring**
- Verify price is in correct mode (test/live)

### PayPal Button Missing
- Check `PAYPAL_CLIENT_ID` is set
- Verify billing plan IDs exist in PayPal
- Check browser console for errors

### Database Error
```bash
# Run migration to add payment columns
python add_stripe_columns.py
```

---

## 🎯 When Ready for Production

### Switch to Live Mode:
1. Complete Stripe business verification
2. Activate Live Mode in Stripe Dashboard
3. Create 4 live products (same as test)
4. Get live API keys (`pk_live_` and `sk_live_`)
5. Replace test keys with live keys in Render
6. Test with real $1 payment
7. Set up bank account for payouts

### Security Checklist:
- [ ] Live keys stored only in Render (never in code)
- [ ] HTTPS enabled on domain
- [ ] Webhook signature verification enabled
- [ ] PCI compliance reviewed
- [ ] Terms of Service updated with refund policy

---

## 📞 Support

**Stripe Dashboard:** https://dashboard.stripe.com
**Stripe Docs:** https://stripe.com/docs
**Stripe Support:** support@stripe.com

**ContractLink Support:** admin@contractlink.ai
**GitHub:** rayofsundays-boop/virginia-contracts-lead-generation

---

## 🎉 Complete!

Once all 6 Stripe environment variables are set, your unified checkout is ready to accept payments! 🚀
