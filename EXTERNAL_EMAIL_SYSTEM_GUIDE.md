# External Email System - Complete Guide

## 🎉 System Overview
The External Email System allows admins to send emails to any external email address directly from the platform. Built with SMTP/TLS encryption, rate limiting, and comprehensive tracking.

---

## ✅ What's Been Built

### 1. **Database Schema** (`external_emails` table)
**24 Fields:**
- `id` (Primary Key)
- `sender_user_id` (Foreign Key to users)
- `sender_username` (Text)
- `is_admin_sender` (Boolean)
- `recipient_email` (Text, required)
- `recipient_name` (Text, optional)
- `subject` (Text, required)
- `message_body` (Text, required - plain text)
- `message_html` (Text, optional - HTML version)
- `message_type` (Text: general/support/marketing/notification/followup/announcement)
- `status` (Text: pending/sent/failed)
- `sent_at` (Timestamp)
- `delivery_error` (Text)
- `priority` (Text: normal/high/low)
- `tracking_id` (Unique identifier)
- `reply_to_email` (Text)
- `cc_emails` (Text)
- `bcc_emails` (Text)
- `attachments_json` (Text - JSON array)
- `metadata_json` (Text - extra data)
- `ip_address` (Text)
- `user_agent` (Text)
- `created_at` (Timestamp, default NOW)
- `updated_at` (Timestamp, auto-update)

**5 Indexes:**
- `idx_external_emails_sender` (sender_user_id)
- `idx_external_emails_recipient` (recipient_email)
- `idx_external_emails_status` (status)
- `idx_external_emails_sent_at` (sent_at)
- `idx_external_emails_tracking` (tracking_id)

**Created By:** `create_external_emails_table.py`

---

### 2. **Email Service** (`external_email_service.py`)
**Class:** `ExternalEmailService`

**Methods:**
```python
@staticmethod
def validate_email(email: str) -> bool
    """Validates email format using regex"""

@staticmethod
def send_external_email(
    to_email: str,
    subject: str,
    message_body: str,
    message_html: str = None,
    message_type: str = 'general',
    sender_user_id: int = None,
    sender_username: str = 'Admin',
    priority: str = 'normal'
) -> dict
    """Sends email via SMTP and tracks in database"""
```

**Features:**
- ✅ TLS/SSL encryption (smtplib with ssl.create_default_context())
- ✅ Multipart messages (plain text + HTML)
- ✅ Database tracking (creates record before send, updates after)
- ✅ Error handling (catches SMTP auth failures, delivery errors)
- ✅ Environment variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL`

**Example Usage:**
```python
from external_email_service import ExternalEmailService

result = ExternalEmailService.send_external_email(
    to_email='customer@example.com',
    subject='Welcome to ContractLink.ai',
    message_body='Thank you for subscribing!',
    message_html='<h1>Thank you for subscribing!</h1>',
    message_type='general',
    sender_user_id=1,
    sender_username='admin2'
)

if result['success']:
    print(f"Email sent! ID: {result['email_id']}")
else:
    print(f"Failed: {result['error']}")
```

---

### 3. **API Endpoint** (`app.py`)

#### **POST /send-external-email**
**Purpose:** Send external email with rate limiting

**Authentication:** Admin only (`session.get('is_admin')`)

**Rate Limiting:** 50 emails per 60 minutes per user

**Request Body (JSON):**
```json
{
  "recipient_email": "customer@example.com",
  "recipient_name": "John Doe",
  "subject": "Your Subscription Confirmation",
  "message_body": "Thank you for subscribing...",
  "message_html": "<h1>Thank you...</h1>",
  "message_type": "support",
  "priority": "high"
}
```

**Response (JSON):**
```json
{
  "success": true,
  "message": "Email sent successfully!",
  "email_id": 123
}
```

**Error Responses:**
- 401: Not authenticated
- 403: Not admin
- 429: Rate limit exceeded (50 emails/hour)
- 400: Validation errors (invalid email, missing subject/body)
- 500: SMTP/server errors

**Code Location:** `app.py` line ~25150

---

#### **GET /external-emails**
**Purpose:** View all sent external emails

**Authentication:** Admin only

**Returns:** Renders `admin_external_emails.html` with list of all emails

**Query:** Fetches last 100 emails ordered by `created_at DESC`

**Code Location:** `app.py` line ~25313

---

### 4. **Admin UI Templates**

#### **admin_send_external_email.html**
**Route:** `/send-external-email` (GET)

**Features:**
- Message type dropdown (general, support, marketing, notification, followup, announcement)
- Recipient email input with validation
- Recipient name (optional)
- Subject field (required)
- Plain text message body (required)
- HTML message body (optional)
- Priority selector (normal, high, low)
- Preview button with Bootstrap modal
- Async form submission with fetch API
- Loading states: "Sending..." with spinner
- Success message: "✅ Message sent successfully! Email ID: {id}"
- Error handling with dismissible alerts

**JavaScript:**
- Email validation regex
- Required field checks before submit
- Async POST to `/send-external-email`
- Disables button during send
- Shows success/error messages
- Resets form on success

---

#### **admin_external_emails.html**
**Route:** `/external-emails` (GET)

**Features:**
- **Stats Cards:** Total sent, successful, failed, pending counts
- **Emails Table:** ID, recipient, subject, type, status, sender, sent date, actions
- **Admin Badges:** Shows "Admin" badge on `is_admin_sender` emails
- **Status Indicators:**
  - ✅ Sent (green badge)
  - ❌ Failed (red badge)
  - ⏰ Pending (yellow badge)
- **Actions:**
  - View button (opens modal with full details)
  - Error button (shows delivery_error if exists)
- **DataTable Integration:** Sortable, searchable, paginated (25 per page)
- **Empty State:** "No External Emails Sent Yet" with CTA button

**Modals:**
- View Email Modal: Shows full email details
- Error Modal: Displays delivery error messages

---

## 🔧 Environment Setup

### Required Environment Variables
Add to `.env` or Render environment:

```bash
# SMTP Server Configuration
SMTP_HOST=smtp.gmail.com           # For Gmail
SMTP_PORT=587                       # TLS port (465 for SSL)

# SMTP Authentication
SMTP_USER=your-email@gmail.com      # Your email
SMTP_PASSWORD=your-app-password     # App password (not regular password)

# Sender Email
FROM_EMAIL=noreply@contractlink.ai  # Display email
```

### Gmail Setup (Recommended)
1. Enable 2FA on your Google account
2. Generate App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy 16-character password
3. Use app password as `SMTP_PASSWORD`

### Other SMTP Providers
- **SendGrid:** `smtp.sendgrid.net` (port 587)
- **Mailgun:** `smtp.mailgun.org` (port 587)
- **AWS SES:** `email-smtp.us-east-1.amazonaws.com` (port 587)
- **Outlook:** `smtp-mail.outlook.com` (port 587)

---

## 🧪 Testing Checklist

### 1. **Local Testing**
```bash
# Set environment variables
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export FROM_EMAIL=noreply@contractlink.ai

# Start Flask app
python app.py
```

### 2. **Test Cases**

#### ✅ Valid Email Send
1. Navigate to `/send-external-email`
2. Fill in all fields:
   - Recipient: your-test-email@gmail.com
   - Subject: Test Email
   - Message: This is a test
3. Click "Send Email"
4. Verify:
   - Success message appears
   - Email received in inbox
   - Record appears in `/external-emails`
   - Status shows "Sent" (green badge)

#### ❌ Invalid Email Format
1. Enter invalid email: `invalid-email`
2. Click "Send Email"
3. Verify: Error message "Invalid email format"

#### ❌ Missing Required Fields
1. Leave subject empty
2. Click "Send Email"
3. Verify: Error message "Subject is required"

#### ⏰ Rate Limiting
1. Send 50 emails rapidly (use script or loop)
2. Try 51st email
3. Verify: Error "Rate limit exceeded. Maximum 50 emails per hour."

#### 🔒 Admin Authentication
1. Log out or use non-admin account
2. Try accessing `/send-external-email`
3. Verify: Redirected to home with "Unauthorized" message

#### 📊 Database Tracking
1. Send email
2. Check database:
```sql
SELECT * FROM external_emails ORDER BY id DESC LIMIT 1;
```
3. Verify fields populated:
   - `sender_user_id` = current user ID
   - `is_admin_sender` = 1
   - `status` = 'sent'
   - `sent_at` = current timestamp
   - `delivery_error` = NULL

#### 🚫 SMTP Failure Simulation
1. Set wrong SMTP password in environment
2. Try sending email
3. Verify:
   - Error message shown
   - Status = 'failed' in database
   - `delivery_error` contains SMTP error

---

## 🚀 Production Deployment

### Step 1: Database Migration
```bash
# On Render, run via console or auto-deploy script
python create_external_emails_table.py
```

**Expected Output:**
```
✅ external_emails table created successfully
```

### Step 2: Configure Environment Variables
In Render dashboard:
1. Go to Environment tab
2. Add variables:
   - `SMTP_HOST` = smtp.gmail.com
   - `SMTP_PORT` = 587
   - `SMTP_USER` = your-email@gmail.com
   - `SMTP_PASSWORD` = your-app-password
   - `FROM_EMAIL` = noreply@contractlink.ai
3. Save changes (triggers redeploy)

### Step 3: Verify Deployment
1. Navigate to: `https://your-app.onrender.com/external-emails`
2. Check: Page loads without errors
3. Click: "Send New Email" button
4. Send test email to yourself
5. Verify: Email received and record appears in list

### Step 4: Monitor Logs
```bash
# In Render logs, watch for:
✅ "Email sent successfully to customer@example.com"
❌ "SMTP error: Authentication failed"
⏰ "Rate limit exceeded for user 1"
```

---

## 📊 Admin Usage Guide

### Sending Emails
1. Log in as admin (admin2/Admin2!Secure123)
2. Navigate to `/send-external-email`
3. Select **Message Type:**
   - **General:** Regular communication
   - **Support:** Customer support responses
   - **Marketing:** Promotional emails
   - **Notification:** System alerts
   - **Followup:** Follow-up messages
   - **Announcement:** Important announcements
4. Enter recipient email (validated on submit)
5. Add recipient name (optional, shows in greeting)
6. Write subject (required)
7. Compose message:
   - **Plain Text:** Always required (fallback)
   - **HTML:** Optional (rich formatting)
8. Set priority (normal/high/low)
9. Click "Preview" to see email (optional)
10. Click "Send Email"
11. Wait for confirmation (1-3 seconds)

### Viewing Sent Emails
1. Navigate to `/external-emails`
2. View stats cards:
   - Total sent
   - Successful (green)
   - Failed (red)
   - Pending (yellow)
3. Browse table:
   - Sort by any column
   - Search by recipient/subject
   - Click "View" for details
   - Click "Error" icon for failure reasons
4. Filter with DataTable search

### Troubleshooting Failed Emails
1. Find failed email in `/external-emails`
2. Click red "Error" button
3. Read error message:
   - **"Authentication failed":** Check SMTP credentials
   - **"Connection refused":** Check SMTP host/port
   - **"Recipient address rejected":** Invalid email
   - **"Rate limit":** Wait 60 minutes
4. Fix issue and resend manually

---

## 🔐 Security Features

### Rate Limiting
- **Limit:** 50 emails per user per 60 minutes
- **Storage:** In-memory (resets on restart)
- **Bypass:** Admins only (no public access)

### Authentication
- Admin-only access (`session.get('is_admin')`)
- Checks on both GET and POST routes
- Redirects non-admins to home

### Input Validation
- Email format regex validation
- Subject and body required checks
- Sanitizes user input before database insert

### SMTP Security
- TLS encryption (STARTTLS)
- Secure context (ssl.create_default_context())
- App passwords (not plain passwords)

### Database Security
- Prepared statements (SQLAlchemy text())
- No SQL injection vectors
- Indexes for performance

---

## 📈 Future Enhancements (Optional)

### Attachments
- Add file upload to form
- Store attachments in S3/cloud storage
- Add `attachments_json` array to emails

### Email Templates
- Create template library
- Variable substitution: `{{name}}`, `{{company}}`
- Template selector in form

### Scheduled Emails
- Add `scheduled_at` field
- Background job to send at specific time
- Cron or Celery integration

### Reply Tracking
- Parse incoming emails
- Create `email_replies` table
- Show conversation threads

### Analytics
- Open rate tracking (pixel)
- Click tracking (link wrapper)
- Dashboard charts

### Bulk Email
- Upload CSV of recipients
- Send same email to multiple people
- Progress bar for bulk sends

---

## 🎯 Quick Reference

### Routes
| Route | Method | Purpose |
|-------|--------|---------|
| `/send-external-email` | GET | Show email form |
| `/send-external-email` | POST | Send email (API) |
| `/external-emails` | GET | View sent emails |

### Files
| File | Purpose |
|------|---------|
| `create_external_emails_table.py` | Database schema |
| `external_email_service.py` | SMTP service |
| `templates/admin_send_external_email.html` | Compose form |
| `templates/admin_external_emails.html` | List view |
| `app.py` (line ~25150) | API endpoint |

### Environment Variables
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@contractlink.ai
```

### Rate Limits
- **50 emails per hour** per admin user
- Resets every 60 minutes
- Stored in memory (cleared on restart)

---

## ✅ Deployment Checklist

- [ ] Run `create_external_emails_table.py` on production
- [ ] Set 5 environment variables in Render
- [ ] Test sending email to yourself
- [ ] Verify email received in inbox
- [ ] Check `/external-emails` list view
- [ ] Test rate limiting (send 51 emails)
- [ ] Test invalid email format
- [ ] Test missing subject/body
- [ ] Monitor Render logs for errors
- [ ] Document any issues

---

## 🐛 Common Issues

### Issue: "Authentication failed"
**Cause:** Wrong SMTP password
**Fix:** Generate new app password in Gmail, update `SMTP_PASSWORD`

### Issue: "Connection refused"
**Cause:** Wrong SMTP host or port
**Fix:** Use `smtp.gmail.com` and port `587` for Gmail

### Issue: Email not received
**Cause:** Spam filter or wrong recipient
**Fix:** Check spam folder, verify email address

### Issue: Rate limit not working
**Cause:** In-memory storage cleared on restart
**Fix:** Expected behavior; use Redis for persistent limits

### Issue: HTML not rendering
**Cause:** Email client blocking HTML
**Fix:** Plain text fallback always sent

---

## 📞 Support

For issues with the external email system:
1. Check Render logs for SMTP errors
2. Verify environment variables are set
3. Test with Gmail app password
4. Review `/external-emails` for delivery errors
5. Contact Chinnea if authentication issues persist

---

**System Status:** ✅ READY FOR TESTING
**Last Updated:** November 2025
**Version:** 1.0.0
