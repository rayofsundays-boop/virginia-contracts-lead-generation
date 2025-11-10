# WIN50 Quick Reference Card

## 🎯 What is WIN50?
**50% OFF** promo code for all subscription plans

---

## 💰 Pricing

| Plan | Regular | WIN50 | You Save |
|------|---------|-------|----------|
| Monthly | $99/mo | **$49.50/mo** | $49.50 |
| Annual | $950/yr | **$475/yr** | $475 |

---

## 🚀 How Customers Use It

### Option 1: Click Banner
1. See banner: "🎉 Get 50% OFF with code WIN50"
2. Click "Subscribe Now"
3. Auto-applies discount
4. Choose plan and pay

### Option 2: Enter Manually
1. Go to subscription page
2. Enter "WIN50" in promo field
3. Click "Apply Code"
4. See updated prices
5. Choose plan and pay

---

## 🛠️ Admin Setup (REQUIRED)

### Step 1: Create PayPal Plans
Create these 2 plans in PayPal Dashboard:

1. **Monthly WIN50 Plan**
   - Price: $49.50/month
   - Frequency: Every 1 month
   - Copy Plan ID (starts with P-)

2. **Annual WIN50 Plan**
   - Price: $475/year
   - Frequency: Every 12 months
   - Copy Plan ID

### Step 2: Add Environment Variables
```bash
PAYPAL_MONTHLY_WIN50_PLAN_ID=P-XXXXXXXXXX
PAYPAL_ANNUAL_WIN50_PLAN_ID=P-YYYYYYYYYY
```

### Step 3: Restart App
```bash
# Kill Flask process
# Restart with updated .env
flask run
```

### Step 4: Test
1. Visit site, see banner
2. Click banner or go to /subscription
3. Enter WIN50
4. Verify prices show $49.50 / $475
5. Test PayPal checkout

---

## 📍 Where It Appears

- **Sales Banner**: Every page (top of screen)
- **Subscription Page**: Promo code input field
- **Success Message**: "Subscription activated with 50% discount!"

---

## 🔗 Important URLs

- Banner link: `/subscription?promo=WIN50`
- Subscribe route: `/subscribe/<plan_type>?promo=WIN50`
- Success page: `/subscription-success`

---

## 📊 Tracking

### Console Output
```
✅ Promo Code Used: WIN50 (50% off) - User: customer@example.com
```

### Session Data
- `promo_code_used`: "WIN50"
- `discount_percent`: 50

---

## ❓ Troubleshooting

### Banner not showing?
- Check `templates/base.html` line ~415
- Clear browser cache
- Check sessionStorage (may be dismissed)

### Promo code not working?
- Verify PayPal plans created
- Check environment variables set
- View console for errors
- Try uppercase: WIN50 (not win50)

### Discount not applying?
- Confirm plan IDs are correct
- Check .env file loaded
- Restart Flask app
- Test in PayPal sandbox first

### PayPal shows wrong price?
- Plan ID mismatch
- Create new plans with correct pricing
- Update environment variables

---

## 📞 Support Commands

### Check environment variables
```bash
echo $PAYPAL_MONTHLY_WIN50_PLAN_ID
echo $PAYPAL_ANNUAL_WIN50_PLAN_ID
```

### Verify plan in code
```python
from app import SUBSCRIPTION_PLANS
print(SUBSCRIPTION_PLANS['monthly_win50'])
print(SUBSCRIPTION_PLANS['annual_win50'])
```

### Test promo detection
```python
# Visit: /subscription?promo=WIN50
# Should see flash message: "🎉 Promo code WIN50 applied!"
```

---

## 🎓 Full Documentation

See `WIN50_PROMOTION_GUIDE.md` for complete setup instructions, user flows, and customization options.

---

## ✅ Launch Checklist

- [ ] PayPal monthly WIN50 plan created ($49.50/mo)
- [ ] PayPal annual WIN50 plan created ($475/yr)
- [ ] Environment variables added to .env
- [ ] Environment variables deployed to production
- [ ] Flask app restarted
- [ ] Banner visible on homepage
- [ ] Promo code validation tested
- [ ] Price updates working
- [ ] PayPal checkout tested with discount
- [ ] Subscription activation confirmed
- [ ] Console logging verified
- [ ] Email marketing prepared
- [ ] Social media posts scheduled

---

**Status**: ✅ Code deployed, awaiting PayPal setup  
**Time to Launch**: ~30 minutes  
**Last Updated**: November 5, 2025
