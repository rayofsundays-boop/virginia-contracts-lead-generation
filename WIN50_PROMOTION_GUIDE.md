# WIN50 Promotion System - Complete Guide

## 🎉 Overview
**WIN50** is a site-wide 50% discount promotion code that applies to both monthly and annual subscription plans.

## 💰 Pricing with WIN50

| Plan Type | Regular Price | WIN50 Price | Savings |
|-----------|--------------|-------------|---------|
| Monthly   | $99.00/month | $49.50/month | $49.50 |
| Annual    | $950.00/year | $475.00/year | $475.00 |

---

## 🚀 How It Works

### 1. **Sales Banner** (Site-Wide)
- **Location**: Top of every page (templates/base.html)
- **Design**: Animated red gradient with pulsing emoji
- **Content**: "🎉 Special Offer: Get 50% OFF with code WIN50 at checkout!"
- **CTA Button**: "Subscribe Now" → Links to `/subscription?promo=WIN50`
- **Dismissible**: Users can close banner (stored in sessionStorage)

### 2. **Subscription Page** (Promo Code Entry)
- **Location**: `/subscription` page (templates/subscription.html)
- **Promo Input**: Text field with "Enter promo code" placeholder
- **Validation**: JavaScript checks if code === 'WIN50'
- **Visual Feedback**:
  - ✅ Success: Green message "✅ 50% discount applied!"
  - ❌ Error: Red message "❌ Invalid promo code"
- **Price Update**: Shows strikethrough original price with discounted price
  - Monthly: ~~$99.00~~ **$49.50**/month
  - Annual: ~~$950.00~~ **$475.00**/year

### 3. **Backend Processing** (Automatic Discount)
- **Route**: `/subscribe/<plan_type>` in app.py
- **Logic**:
  1. Checks URL parameter: `request.args.get('promo')`
  2. If promo == 'WIN50', switches to discounted plan
  3. Uses `monthly_win50` or `annual_win50` plan IDs
  4. Stores promo code in session for tracking
- **PayPal Integration**: Creates billing agreement with discounted plan_id

### 4. **Success Tracking** (Analytics)
- **Route**: `/subscription-success` in app.py
- **Logging**: Prints promo code usage to console
- **Message**: Shows custom success message with discount percentage
- **Session Cleanup**: Removes promo code from session after activation

---

## 🛠️ PayPal Dashboard Setup

### Required: Create Discounted Plans

You need to create **two additional billing plans** in PayPal:

#### 1. Monthly WIN50 Plan ($49.50/month)
1. Go to PayPal Developer Dashboard → Products & Services
2. Click "Create Plan"
3. **Details**:
   - Name: "Monthly Subscription (50% OFF)"
   - Type: Service
   - Category: Subscription
4. **Pricing**:
   - Billing Frequency: Every 1 month
   - Price: $49.50 USD
   - Setup Fee: $0.00
5. **Settings**:
   - Auto-renewal: Enabled
   - Trial period: None
6. **Save** and copy the Plan ID (starts with `P-`)

#### 2. Annual WIN50 Plan ($475.00/year)
1. Same steps as above
2. **Pricing**:
   - Billing Frequency: Every 12 months
   - Price: $475.00 USD
3. **Save** and copy the Plan ID

### Environment Variables

Add these to your `.env` file or hosting platform:

```bash
# Original Plans
PAYPAL_MONTHLY_PLAN_ID=P-XXXXXXXXXXXXXXXXXX
PAYPAL_ANNUAL_PLAN_ID=P-YYYYYYYYYYYYYYYY

# WIN50 Discounted Plans (NEW)
PAYPAL_MONTHLY_WIN50_PLAN_ID=P-ZZZZZZZZZZZZZZZZZZ
PAYPAL_ANNUAL_WIN50_PLAN_ID=P-AAAAAAAAAAAAAAAAAAA
```

**Important**: Replace the placeholder IDs with your actual PayPal plan IDs.

---

## 📝 Code Implementation

### 1. SUBSCRIPTION_PLANS Dictionary (app.py line 101)

```python
SUBSCRIPTION_PLANS = {
    'monthly': {
        'name': 'Monthly Subscription',
        'price': 99.00,
        'plan_id': os.environ.get('PAYPAL_MONTHLY_PLAN_ID', 'P-MONTHLY-PLAN-ID')
    },
    'annual': {
        'name': 'Annual Subscription',
        'price': 950.00,
        'plan_id': os.environ.get('PAYPAL_ANNUAL_PLAN_ID', 'P-ANNUAL-PLAN-ID')
    },
    # WIN50 Discounted Plans (50% OFF)
    'monthly_win50': {
        'name': 'Monthly Subscription (50% OFF)',
        'price': 49.50,
        'plan_id': os.environ.get('PAYPAL_MONTHLY_WIN50_PLAN_ID', 'P-MONTHLY-WIN50-PLAN-ID')
    },
    'annual_win50': {
        'name': 'Annual Subscription (50% OFF)',
        'price': 475.00,
        'plan_id': os.environ.get('PAYPAL_ANNUAL_WIN50_PLAN_ID', 'P-ANNUAL-WIN50-PLAN-ID')
    }
}
```

### 2. Subscribe Route Logic (app.py line ~4570)

```python
# Check for promo code
promo_code = request.args.get('promo', '').upper()

# Apply WIN50 promo code - switch to discounted plan
if promo_code == 'WIN50':
    # Use discounted plan ID
    discounted_plan_type = f"{plan_type}_win50"
    
    if discounted_plan_type in SUBSCRIPTION_PLANS:
        plan_type = discounted_plan_type
        session['promo_code_used'] = 'WIN50'
        session['discount_percent'] = 50
        flash('🎉 Promo code WIN50 applied! You\'re getting 50% OFF!', 'success')
```

### 3. Frontend JavaScript (templates/subscription.html)

```javascript
function applyPromoCode() {
    const promoCode = document.getElementById('promoCodeInput').value.trim().toUpperCase();
    
    if (promoCode === 'WIN50') {
        // Store in sessionStorage
        sessionStorage.setItem('promoCode', 'WIN50');
        
        // Show success message
        document.getElementById('promoMessage').innerHTML = 
            '<div class="alert alert-success">✅ 50% discount applied!</div>';
        
        // Update pricing display
        updatePricing(0.5); // 50% discount
        
        // Update Subscribe buttons with promo parameter
        document.querySelectorAll('.subscribe-btn').forEach(btn => {
            btn.href = btn.href.split('?')[0] + '?promo=WIN50';
        });
    } else {
        // Show error
        document.getElementById('promoMessage').innerHTML = 
            '<div class="alert alert-danger">❌ Invalid promo code</div>';
    }
}
```

---

## 🎯 User Flow

### Scenario 1: Banner Click
1. User sees sales banner on any page
2. Clicks "Subscribe Now" button
3. Redirected to `/subscription?promo=WIN50`
4. JavaScript auto-applies WIN50 code
5. Prices update with strikethrough
6. User clicks "Subscribe Monthly" or "Subscribe Annually"
7. Redirected to PayPal with discounted plan
8. Subscription activates at 50% off

### Scenario 2: Manual Entry
1. User navigates to `/subscription` directly
2. Enters "WIN50" in promo code field
3. Clicks "Apply Code" button
4. Prices update with discount
5. User clicks Subscribe button
6. Same checkout flow as above

### Scenario 3: Direct Link Share
1. Someone shares link with `?promo=WIN50`
2. User clicks link
3. Auto-applies discount on page load
4. User proceeds to checkout

---

## 📊 Analytics & Tracking

### What's Logged
- **Console Output**: Every WIN50 subscription includes:
  ```
  ✅ Promo Code Used: WIN50 (50% off) - User: customer@example.com
  ```
- **Session Data**: Promo code stored during checkout flow
- **Database**: Could extend to add `promo_code` column to `leads` table

### Future Enhancements
1. **Admin Dashboard**: Track WIN50 usage statistics
2. **Database Column**: Add `promo_code_used` to `leads` table
3. **Expiration Date**: Set WIN50 to expire after X date
4. **Usage Limits**: One-time use per customer
5. **Revenue Tracking**: Calculate total discount given vs. conversions gained

---

## 🧪 Testing Checklist

### Before Going Live
- [ ] Create both discounted plans in PayPal Dashboard
- [ ] Add plan IDs to environment variables
- [ ] Test banner appears on all pages
- [ ] Test banner dismissal persists across sessions
- [ ] Test promo code validation (WIN50 vs invalid code)
- [ ] Test price updates with strikethrough
- [ ] Test monthly subscription with WIN50
- [ ] Test annual subscription with WIN50
- [ ] Verify PayPal shows correct discounted price
- [ ] Confirm subscription activates as "paid"
- [ ] Check console logs for promo code tracking
- [ ] Test without promo code (regular pricing)

### Edge Cases
- [ ] Test with uppercase WIN50
- [ ] Test with lowercase win50
- [ ] Test with spaces " WIN50 "
- [ ] Test expired promo codes (future feature)
- [ ] Test multiple promo code attempts
- [ ] Test closing banner and reopening browser
- [ ] Test on mobile devices (responsive design)

---

## 🎨 Customization

### Change Discount Percentage
1. Update `SUBSCRIPTION_PLANS` prices (e.g., 30% off = $69.30 monthly)
2. Update JavaScript discount multiplier (e.g., 0.7 for 30% off)
3. Update banner text "50% OFF" → "30% OFF"
4. Update promo message "50% discount applied!" → "30% discount applied!"

### Create New Promo Codes
1. Add new entries to `SUBSCRIPTION_PLANS` (e.g., `monthly_summer25`)
2. Create corresponding PayPal plans
3. Update JavaScript validation to accept new code
4. Add new banner or promotion section

### Disable Promotion
1. Comment out sales banner in `templates/base.html`
2. Remove promo code input from `templates/subscription.html`
3. Keep backend logic for existing subscribers

---

## 🚨 Important Notes

- **PayPal Plans Required**: You MUST create discounted plans in PayPal first
- **Environment Variables**: Set plan IDs before deploying
- **Session Storage**: Banner dismissal is browser-specific (not account-based)
- **Promo Code Case**: Code is converted to uppercase automatically
- **One Plan at a Time**: Users can only use one promo code per checkout

---

## 📞 Support

If customers report issues with WIN50:
1. Verify discounted plans exist in PayPal
2. Check environment variables are set correctly
3. Clear browser cache and cookies
4. Test with PayPal sandbox before live testing
5. Check console logs for error messages

---

## 🎓 Next Steps

1. **Create PayPal Plans**: Set up discounted plans in dashboard
2. **Add Environment Variables**: Copy plan IDs to .env file
3. **Test Thoroughly**: Complete testing checklist above
4. **Monitor Analytics**: Track WIN50 conversion rates
5. **Marketing**: Promote WIN50 in emails, social media, ads

---

**Last Updated**: November 5, 2025  
**Status**: ✅ Fully Implemented and Ready for Testing
