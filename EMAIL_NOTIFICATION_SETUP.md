# Email Notification System Setup Guide

## 🎯 Overview

Complete email notification system for the VA Contracts Lead Generation platform with:
- ✅ Test notification emails
- ✅ Daily briefing emails (8 AM EST automatic)
- ✅ Real-time new lead alerts
- ✅ Gmail SMTP with SSL/TLS encryption
- ✅ APScheduler for automated daily sends
- ✅ Professional HTML email templates

---

## 📁 Files Created

### Core System Files:
1. **`src/email_service.py`** - Gmail SMTP email sending service
2. **`src/email_templates.py`** - HTML email templates (test, daily briefing, lead alerts)
3. **`src/routes/notifications.py`** - Flask blueprint with notification endpoints
4. **`src/scheduler.py`** - APScheduler for automated daily briefings at 8 AM EST

### Integration:
- **`app.py`** - Updated to register notifications blueprint and start scheduler
- **`requirements.txt`** - Added `APScheduler==3.10.4`

---

## 🔧 Render Environment Configuration

### Step 1: Set Up Gmail App Password

1. **Go to Google Account Settings**: https://myaccount.google.com/
2. **Enable 2-Step Verification** (required for app passwords)
3. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → Type "ContractLink Render"
   - Click "Generate"
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 2: Add Environment Variables in Render

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Select your service**: `virginia-contracts-lead-generation`
3. **Navigate to**: Environment → Environment Variables
4. **Add these 2 variables**:

```
EMAIL_USER = yourgmail@gmail.com
EMAIL_PASS = abcdefghijklmnop
```

**Important Notes:**
- `EMAIL_USER` = Your full Gmail address (e.g., `yourname@gmail.com`)
- `EMAIL_PASS` = The 16-character app password (remove spaces)
- **DO NOT use your real Gmail password** - must be app password
- These variables are encrypted by Render automatically

### Step 3: Deploy

1. **Commit and push** all changes to GitHub (already done ✅)
2. **Render auto-deploys** from your GitHub repository
3. **Wait for deployment** to complete (check Render logs)
4. **Verify deployment** shows no errors

---

## 🧪 Testing the System

### Test 1: Admin Test Endpoint (No Login Required)

**Purpose**: Verify email credentials are configured correctly

**URL**: `https://your-app.onrender.com/notifications/test-admin?email=YOUR_EMAIL@gmail.com`

**Expected Result**:
```json
{
  "status": "success",
  "message": "Test email sent to YOUR_EMAIL@gmail.com"
}
```

**Check your inbox** for:
- Subject: "✅ Test Notification from ContractLink.ai"
- Professional HTML email with success message

**If it fails**:
```json
{
  "status": "error",
  "message": "Failed to send test email. Check EMAIL_USER and EMAIL_PASS environment variables."
}
```
→ Double-check environment variables in Render

---

### Test 2: Authenticated Test Email (Login Required)

**Purpose**: Test email for logged-in users

**Steps**:
1. Login to your account at `https://your-app.onrender.com/signin`
2. Navigate to: `https://your-app.onrender.com/notifications/send-test`

**Expected Result**:
```json
{
  "status": "success",
  "message": "Test email sent to your-email@example.com"
}
```

**Email arrives** with:
- Subject: "✅ Test Notification from ContractLink.ai"
- Styled HTML with purple branding
- Links to dashboard

---

### Test 3: Daily Briefing (Manual Trigger)

**Purpose**: Test daily briefing email with recent leads

**Steps**:
1. Login to your account
2. Navigate to: `https://your-app.onrender.com/notifications/daily`

**Expected Result**:
```json
{
  "status": "success",
  "message": "Daily briefing sent to your-email@example.com",
  "leads_count": 5
}
```

**Email Content**:
- Subject: "📊 Daily Briefing: 5 New Leads"
- List of leads with project names, states, values, deadlines
- Professional HTML styling
- Links to view all leads

---

### Test 4: New Lead Alert

**Purpose**: Send real-time alert for a specific lead

**URL**: `https://your-app.onrender.com/notifications/new-lead/<lead_id>`

**Example**: `/notifications/new-lead/123`

**Expected Result**:
```json
{
  "status": "success",
  "message": "New lead alert sent to your-email@example.com",
  "lead": {
    "project": "Hampton Recreation Centers Cleaning",
    "state": "VA",
    "value": "$125,000",
    "deadline": "2025-12-15"
  }
}
```

**Email Content**:
- Subject: "🔔 New Lead Alert: Hampton Recreation Centers Cleaning"
- Full lead details with description
- CTA button to view full details
- Professional HTML styling

---

## 🕐 Automated Daily Briefings

### Scheduler Configuration

**When**: Every day at **8:00 AM EST**  
**Timezone**: America/New_York  
**Recipients**: All users with `subscription_status = 'active'`

### How It Works:

1. **APScheduler** starts automatically when Flask app launches
2. **Every morning at 8 AM EST**:
   - Fetches leads from last 24 hours (`federal_contracts` table)
   - Queries all active subscribers from `users` table
   - Sends personalized daily briefing to each subscriber
   - Logs success/failure for each email

### Verify Scheduler is Running:

Check Render logs for these messages on startup:
```
✅ Email notifications blueprint registered
✅ Daily email scheduler started (8 AM EST briefings)
✅ Scheduler started. Daily briefing scheduled for 8:00 AM EST.
   Next run: 2025-11-15 08:00:00-05:00
```

### Manual Trigger for Testing:

You can manually trigger the daily job by calling `/notifications/daily` endpoint (see Test 3 above).

---

## 📧 Email Templates

### 1. Test Notification
- **Template**: `email_templates.test_notification()`
- **Purpose**: Verify email system works
- **Style**: Success banner with checkmark emoji
- **Branding**: ContractLink.ai purple (#4F46E5)

### 2. Daily Briefing
- **Template**: `email_templates.daily_briefing(leads)`
- **Purpose**: Morning summary of new leads
- **Style**: Lead cards with icons (📍 location, 💰 value, ⏰ deadline)
- **Data**: Shows count + list of recent leads

### 3. New Lead Alert
- **Template**: `email_templates.new_lead_alert(lead)`
- **Purpose**: Real-time notification for individual leads
- **Style**: Alert banner + detailed lead card
- **CTA**: "View Full Details" button linking to dashboard

---

## 🔒 Security Features

### Email Transport Security:
- ✅ **SSL/TLS Encryption**: All emails sent via secure SMTP (port 587)
- ✅ **Gmail App Passwords**: Never uses real account password
- ✅ **Environment Variables**: Credentials stored securely in Render
- ✅ **No Plaintext Storage**: Email credentials never committed to Git

### Authentication:
- ✅ **Login Required**: Most endpoints require `@login_required` decorator
- ✅ **Test Endpoint**: `/test-admin` open for initial verification only
- ✅ **User Context**: Emails sent to `current_user.email` automatically

### Rate Limiting (Future Enhancement):
- Consider adding Flask-Limiter to prevent spam
- Example: 10 test emails per user per hour

---

## 🛠️ Troubleshooting

### Problem: "Email credentials missing"

**Symptoms**:
```
⚠️ Email credentials missing. Set EMAIL_USER and EMAIL_PASS environment variables.
```

**Solution**:
1. Check Render environment variables exist
2. Verify no typos in variable names (case-sensitive)
3. Redeploy service after adding variables
4. Check Render logs show variables loaded

---

### Problem: "Authentication failed"

**Symptoms**:
```
❌ ERROR sending email: (535, b'5.7.8 Username and Password not accepted')
```

**Solution**:
1. Verify `EMAIL_PASS` is Gmail **app password** (not account password)
2. Remove spaces from 16-character app password
3. Confirm 2-Step Verification enabled on Gmail account
4. Generate new app password if needed

---

### Problem: "Failed to send email"

**Symptoms**:
```
❌ ERROR sending email to user@example.com: [Errno -2] Name or service not known
```

**Solution**:
1. Check Render server has internet access (should be default)
2. Verify Gmail SMTP not blocked by firewall
3. Test SMTP connection: `telnet smtp.gmail.com 587`
4. Check Render status page for outages

---

### Problem: Scheduler not starting

**Symptoms**:
```
⚠️ Email notifications not available. Install apscheduler to enable.
```

**Solution**:
1. Verify `APScheduler==3.10.4` in requirements.txt
2. Check Render build logs show apscheduler installed
3. Redeploy if package missing
4. Check for import errors in Render logs

---

### Problem: No emails received

**Symptoms**: API returns success but no email in inbox

**Solution**:
1. **Check spam folder** (especially Gmail)
2. **Wait 2-3 minutes** (SMTP can be slow)
3. **Verify recipient email** is correct
4. **Check Gmail "Sent" folder** to confirm emails sent
5. **Review Render logs** for SMTP errors

---

## 📊 Database Schema Requirements

### Required Table: `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    username TEXT,
    password_hash TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    is_admin INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Required Table: `federal_contracts`
```sql
CREATE TABLE federal_contracts (
    id INTEGER PRIMARY KEY,
    title TEXT,
    state TEXT,
    estimated_value REAL,
    deadline TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Note**: Tables should already exist from main app setup.

---

## 🚀 API Endpoints Reference

### 1. `/notifications/test-admin`
- **Method**: GET
- **Auth**: None (admin testing only)
- **Query Params**: `email` (required)
- **Example**: `/notifications/test-admin?email=test@example.com`
- **Response**: JSON with status
- **Purpose**: Verify email credentials work

### 2. `/notifications/send-test`
- **Method**: GET
- **Auth**: Required (`@login_required`)
- **Query Params**: None (uses `current_user.email`)
- **Response**: JSON with status
- **Purpose**: Send test email to logged-in user

### 3. `/notifications/daily`
- **Method**: GET
- **Auth**: Required (`@login_required`)
- **Query Params**: None
- **Response**: JSON with status + leads count
- **Purpose**: Manually trigger daily briefing

### 4. `/notifications/new-lead/<lead_id>`
- **Method**: GET
- **Auth**: Required (`@login_required`)
- **URL Params**: `lead_id` (integer, federal_contracts.id)
- **Response**: JSON with status + lead details
- **Purpose**: Send real-time alert for specific lead

---

## 📝 Future Enhancements

### Phase 2 Features:
1. **Email Preferences**:
   - User settings page to enable/disable daily briefings
   - Custom notification frequency (daily, weekly, instant)
   - Filter by state, contract value, deadline

2. **Advanced Templates**:
   - Weekly digest (summary of all leads)
   - Bid deadline reminders (3 days before, 1 day before)
   - Saved search alerts

3. **Analytics**:
   - Email open rates (requires tracking pixels)
   - Click-through rates on CTA buttons
   - Most popular email times

4. **Multi-Channel**:
   - SMS notifications via Twilio
   - Slack integration for team alerts
   - Push notifications (Progressive Web App)

---

## ✅ Deployment Checklist

Before going live, verify:

- [ ] Gmail app password generated
- [ ] `EMAIL_USER` and `EMAIL_PASS` set in Render
- [ ] `APScheduler==3.10.4` in requirements.txt
- [ ] All 4 source files created (`email_service.py`, `email_templates.py`, `notifications.py`, `scheduler.py`)
- [ ] `app.py` imports and registers blueprint
- [ ] Code committed and pushed to GitHub
- [ ] Render deployed successfully (check logs)
- [ ] Test endpoint works: `/notifications/test-admin?email=YOUR_EMAIL`
- [ ] Scheduler started (check logs for "✅ Scheduler started")
- [ ] First daily briefing scheduled for next 8 AM EST
- [ ] Logged-in user can receive test email: `/notifications/send-test`

---

## 📞 Support

**Issues?** Check:
1. Render logs for detailed error messages
2. This troubleshooting guide above
3. Gmail account settings (2FA, app passwords)
4. Environment variables spelling/formatting

**Success Indicators**:
- ✅ "Email sent successfully to..." in Render logs
- ✅ JSON response: `{"status": "success"}`
- ✅ Email arrives in inbox within 2 minutes
- ✅ Scheduler shows next run time in logs

---

## 🎉 You're All Set!

Your email notification system is now:
- ✅ Fully automated (daily briefings at 8 AM EST)
- ✅ Secure (SSL/TLS, app passwords, environment variables)
- ✅ Professional (branded HTML templates)
- ✅ Scalable (handles multiple subscribers)
- ✅ Production-ready for Render deployment

**Next Steps**:
1. Set environment variables in Render
2. Deploy and verify
3. Test all 4 endpoints
4. Monitor scheduler logs
5. Enjoy automated lead notifications! 🚀
