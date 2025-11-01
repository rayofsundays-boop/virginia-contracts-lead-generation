# Email Notifications Setup for Lead Generation

## 📧 Email Configuration

Your app now sends automatic email notifications to **info@eliteecocareservices.com** every time someone registers!

## 🔧 Required Environment Variables

For email to work on Render.com, you need to set these environment variables:

### In Render Dashboard > Environment:

1. **MAIL_USERNAME**
   ```
   Key: MAIL_USERNAME
   Value: your-gmail-address@gmail.com
   ```

2. **MAIL_PASSWORD** 
   ```
   Key: MAIL_PASSWORD
   Value: your-gmail-app-password
   ```

## 📱 Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this 16-character password (not your regular Gmail password)

## 📩 What Emails You'll Receive

When someone registers, you'll get an email with:

```
Subject: New Lead: [Company Name] - Virginia Government Contracts

COMPANY DETAILS:
Company Name: ABC Cleaning Services
Contact Person: John Smith
Email: john@abccleaning.com
Phone: (555) 123-4567
State: VA
Experience: 5 years
Certifications: CIMS Certified, Bonded

Registration Time: 2025-10-30 18:30:45

This lead is interested in government contract opportunities in Virginia cities:
- Hampton
- Suffolk  
- Virginia Beach
- Newport News
- Williamsburg

Follow up promptly to convert this lead!
```

## 🚀 Benefits

- **Instant Notifications**: Know immediately when someone registers
- **Complete Lead Info**: All contact details in one email
- **Professional Format**: Easy to read and act on
- **Lead Tracking**: Never miss a potential customer

## 🛠️ Alternative Email Options

If you don't want to use Gmail, you can also use:
- **SendGrid** (professional email service)
- **Mailgun** (developer-friendly)
- **SMTP2GO** (reliable delivery)

Just update the MAIL_SERVER and port settings in the code.

## ✅ Current Setup

- ✅ Emails sent to: **info@eliteecocareservices.com**
- ✅ Automatic on every registration
- ✅ Complete lead information included
- ✅ Professional formatting
- ✅ Ready for production use