# Email Notifications & Ad Service Guide

## 📧 Email Notifications System

### Overview
Automatically notify your subscribers when new cleaning leads come in. This keeps them engaged and ensures they never miss an opportunity.

### Features Implemented

#### 1. **New Lead Notifications**
When someone submits a cleaning request (residential or commercial), all paid subscribers with email notifications enabled receive an instant email containing:
- Property/Business details
- Location and contact information
- Service requirements
- Budget range
- Estimated monthly value
- Direct link to Lead Marketplace

#### 2. **Bid Notifications**
When a contractor submits a bid on a commercial lead, the business owner receives an email with:
- Contractor information
- Proposed price
- Timeline
- Full proposal details

### Email Configuration

#### Setup SMTP (Gmail example):

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account → Security
   - Select "2-Step Verification"
   - At the bottom, select "App passwords"
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Set Environment Variables** on Render.com:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   ```

#### Alternative Email Services:

**SendGrid** (Recommended for production):
```python
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = 'your-sendgrid-api-key'
```

**Mailgun**:
```python
app.config['MAIL_SERVER'] = 'smtp.mailgun.org'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-mailgun-username'
app.config['MAIL_PASSWORD'] = 'your-mailgun-password'
```

**AWS SES**:
```python
app.config['MAIL_SERVER'] = 'email-smtp.us-east-1.amazonaws.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-ses-username'
app.config['MAIL_PASSWORD'] = 'your-ses-password'
```

### Email Templates

The system sends plain text and HTML emails. Example:

**New Residential Lead:**
```
Subject: 🏠 New Residential Cleaning Lead in Virginia Beach

New residential cleaning lead available!

Location: 123 Ocean View Dr, Virginia Beach, VA 23451
Property Type: Single Family Home
Square Footage: 2,500 sq ft
Bedrooms: 4
Bathrooms: 3
Frequency: Bi-Weekly
Budget: $200-300
Estimated Value: $400/month

Services Needed:
General cleaning, Deep cleaning, Kitchen cleaning

Contact: John Doe
Phone: (757) 555-1234
Email: john@example.com

Login to your Lead Marketplace to view full details!
```

### Notification Settings

Users can control notifications in their account settings:
- ✅ Enable/Disable email notifications
- 🔔 SMS notifications (coming soon)
- 📱 Push notifications (coming soon)

---

## 💰 Ad Service System

### Overview
Monetize your platform with display advertising while providing a better experience for paid subscribers (ad-free).

### Ad Networks Supported

#### 1. **Google AdSense** (Primary - Best for most sites)
- **Revenue**: $2-5 CPM (Cost Per 1000 impressions)
- **Setup Time**: 1-2 days
- **Approval Time**: 24-48 hours
- **Requirements**: Original content, traffic, policy compliance

**Setup Steps**:
1. Sign up at [google.com/adsense](https://www.google.com/adsense/)
2. Add your site and verify ownership
3. Create ad units in dashboard
4. Copy your publisher ID (ca-pub-XXXXXXX)
5. Update `ad_config.py` with your IDs
6. Deploy and wait for approval

#### 2. **Carbon Ads** (Alternative - Great for tech/business sites)
- **Revenue**: $3-8 CPM
- **Setup Time**: Instant
- **Approval Time**: Manual review (quality traffic required)
- **Best For**: Professional/technical audiences

#### 3. **Media.net** (Alternative - Yahoo/Bing network)
- **Revenue**: $1-4 CPM
- **Setup Time**: 1 day
- **Approval Time**: 24-48 hours
- **Best For**: US/UK traffic

### Ad Placements

Current implementation includes ads on:

1. **Homepage**:
   - Header banner (after category cards)
   - In-feed ad (between sections)

2. **Contract Pages**:
   - Sidebar ads (right column)
   - Between listings

3. **NOT shown on**:
   - Lead Marketplace (paid subscribers only)
   - Registration/Login pages
   - Checkout pages

### Ad Types Available

```html
<!-- Horizontal Banner -->
{{ header_ad() }}

<!-- Sidebar Ad -->
{{ sidebar_ad() }}

<!-- In-Feed Ad (looks like content) -->
{{ infeed_ad() }}

<!-- Square Ad (300x250) -->
{{ square_ad() }}

<!-- Custom Business Ad -->
{{ custom_business_ad(
    title="Premium Membership", 
    description="Get unlimited leads", 
    link="/register",
    cta="Upgrade Now"
) }}
```

### Custom Ads (Your Own Promotions)

Use custom ads to promote your own services:
- Premium subscriptions
- Referral programs
- Featured contractor listings
- Partner services

Edit `ad_config.py` to customize:
```python
CUSTOM_ADS = [
    {
        "title": "Premium Membership - 50% Off!",
        "description": "Unlock unlimited leads...",
        "link": "/register?promo=PREMIUM50",
        "cta": "Upgrade Now"
    }
]
```

### Revenue Optimization

#### Estimated Monthly Revenue:

| Monthly Visitors | Page Views | Ad Revenue |
|-----------------|------------|------------|
| 5,000           | 15,000     | $30-75     |
| 10,000          | 30,000     | $60-150    |
| 25,000          | 75,000     | $150-375   |
| 50,000          | 150,000    | $300-750   |
| 100,000         | 300,000    | $600-1,500 |

**Assumptions**: 3 page views per visit, $2-5 CPM

#### Maximizing Revenue:

1. **Increase Traffic**:
   - SEO optimization
   - Content marketing
   - Social media
   - Google/Facebook ads

2. **Improve Ad Placement**:
   - Above the fold
   - In-content (higher CTR)
   - Mobile-optimized
   - A/B testing

3. **Premium Features**:
   - Offer ad-free experience to paid users
   - Create urgency to upgrade
   - Show "Remove ads" prompts

### Ad Performance Tracking

Monitor in your AdSense dashboard:
- **Page RPM**: Revenue per 1000 page views
- **CTR**: Click-through rate
- **CPC**: Cost per click
- **Impressions**: Ad views

### Compliance Requirements

⚠️ **IMPORTANT**: To run ads, you MUST:

1. **Privacy Policy** - Required by AdSense
2. **Cookie Consent** - Required by GDPR/CCPA
3. **Terms of Service** - Recommended
4. **Ad Disclosure** - Mark sponsored content

Example Cookie Banner:
```html
<div class="cookie-banner">
  This site uses cookies and displays ads. 
  <a href="/privacy">Learn more</a>
  <button onclick="acceptCookies()">Accept</button>
</div>
```

### Ad Blocking

~25-30% of users have ad blockers. Strategies:
1. Politely ask to whitelist your site
2. Offer ad-free premium tier
3. Use server-side ad delivery (harder to block)
4. Focus on non-intrusive ads

---

## 🚀 Implementation Checklist

### Email Notifications:
- [x] Configure SMTP settings
- [x] Create notification functions
- [x] Integrate with lead submission
- [x] Integrate with bid submission
- [ ] Set environment variables on Render
- [ ] Test email delivery
- [ ] Add unsubscribe link
- [ ] Create email preferences page

### Ad Service:
- [x] Create ad component templates
- [x] Add AdSense script to base template
- [x] Integrate ads on homepage
- [x] Create ad configuration file
- [ ] Sign up for AdSense
- [ ] Get publisher ID
- [ ] Create ad units
- [ ] Update ad_config.py with IDs
- [ ] Add privacy policy page
- [ ] Add cookie consent banner
- [ ] Test ad display
- [ ] Monitor revenue

---

## 📊 Expected Results

### Month 1-3:
- **Email Notifications**: 80% open rate, 40% CTR
- **Ad Revenue**: $50-200/month (building traffic)
- **User Engagement**: +25% from notifications

### Month 4-6:
- **Email Notifications**: Drive 50+ contractor logins per day
- **Ad Revenue**: $200-500/month
- **Conversions**: 5-10% free to paid (ad removal incentive)

### Month 7-12:
- **Email Notifications**: Critical retention tool
- **Ad Revenue**: $500-1,000/month
- **Premium Revenue**: $3,000+/month (primary revenue)

---

## 🛠 Troubleshooting

### Emails Not Sending:
1. Check MAIL_USERNAME and MAIL_PASSWORD env variables
2. Verify app password (not regular Gmail password)
3. Check spam folder
4. Try SendGrid instead of Gmail
5. Check Flask-Mail logs in Render

### Ads Not Showing:
1. Verify AdSense script in base.html
2. Check if ads approved (can take 24-48 hours)
3. Inspect browser console for errors
4. Check ad blocker isn't active
5. Verify publisher ID is correct
6. Make sure site meets AdSense policies

### Low Ad Revenue:
1. Increase traffic (SEO, marketing)
2. Improve ad placement (above fold)
3. Use responsive ad units
4. Try different ad networks
5. A/B test placements
6. Focus on high-paying keywords

---

## 📈 Next Steps

1. **Set up email credentials** on Render
2. **Test notifications** by submitting a lead
3. **Apply for AdSense** account
4. **Add privacy policy** and cookie consent
5. **Monitor performance** in dashboards
6. **Iterate and optimize** based on data

---

## 💡 Pro Tips

1. **Email**: Use HTML templates for better engagement
2. **Ads**: Start with fewer ads, add more gradually
3. **Premium**: Use "ad-free" as selling point
4. **Testing**: A/B test everything
5. **Compliance**: Always follow ad network policies
6. **User Experience**: Never let ads ruin UX
7. **Revenue**: Diversify - don't rely only on ads

---

## 📞 Support

Need help setting up?
- Email issues: Check Flask-Mail documentation
- Ad issues: Check AdSense support forum
- General: Review this guide and ad_config.py

Good luck monetizing your platform! 🎉
