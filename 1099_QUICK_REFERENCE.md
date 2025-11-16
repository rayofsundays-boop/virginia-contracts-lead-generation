# 1099 Cleaner Requests - Quick Reference Card

## 🎯 Feature at a Glance
**Free job posting system** where companies submit 1099 contractor requests → Admin reviews → Auto-posts to forum → Subscribers get full contact info.

---

## 📍 Key Routes

### Public Routes
| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/request-1099-cleaners` | Submit job request | No |
| `/forum/1099-cleaners` | View job listings | No (limited) |
| `/browse-1099-cleaners` | Browse opportunities | Login (gated) |

### Admin Routes
| Route | Purpose |
|-------|---------|
| `/admin/1099-cleaner-requests` | List all requests |
| `/admin/1099-cleaner-requests/<id>` | View/approve/deny |

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/1099-cleaner-requests/create` | POST | Submit request |
| `/api/admin/1099-cleaner-requests/<id>/approve` | POST | Approve |
| `/api/admin/1099-cleaner-requests/<id>/deny` | POST | Deny |
| `/api/admin/1099-cleaner-requests/<id>/notes` | POST | Add note |
| `/api/forum/1099-cleaners/<post_id>/view` | POST | Track view |

---

## 🗃️ Database Tables

1. **`cleaner_requests`** - Main submissions (22 columns)
2. **`cleaner_request_notes`** - Admin internal notes
3. **`cleaner_request_messages`** - Two-way messaging (not implemented)
4. **`cleaner_request_forum_posts`** - Published jobs

---

## 🔄 Workflow

```
1. Company submits → Status: pending_review
2. Admin reviews → Approve or Deny
3. If approved → Auto-creates forum post (published = 1)
4. Forum post visible at /forum/1099-cleaners
5. Subscribers see full contact info
```

---

## 📧 Email Triggers

| Action | Recipient | Content |
|--------|-----------|---------|
| Company submits | Admin | New request notification |
| Company submits | Company | Confirmation email |
| Admin approves | Company | Approval + forum link |
| Admin denies | Company | Denial reason |

---

## 🔐 Subscription Gate

**Non-Subscribers See:**
- Service category
- Location (city, state)
- Pay rate
- Job description
- Urgency level
- Requirements

**Subscribers See (ADDITIONAL):**
- ✅ Company name
- ✅ Email address
- ✅ Phone number
- ✅ Direct contact links

---

## 🎨 UI Components

### Public Form (13 Fields)
- Company info: name, contact, email, phone
- Location: city, state
- Job details: category, description, pay rate, start date, urgency
- Requirements: background check, equipment

### Admin Interface
- Stats cards: Pending/Approved/Denied/Total
- Filters: Status, urgency, search
- Actions: Approve, Deny, Add Notes

### Forum Listing
- Card grid layout (responsive)
- State/category/urgency filters
- Subscription gate for contact info
- View tracking

---

## 🧪 Quick Test Commands

### Setup Database
```bash
python3 create_1099_cleaner_tables.py
```

### Check Request Count
```sql
SELECT status, COUNT(*) FROM cleaner_requests GROUP BY status;
```

### View Latest Forum Posts
```sql
SELECT title, company_name, views FROM cleaner_request_forum_posts 
WHERE published = 1 ORDER BY created_at DESC LIMIT 10;
```

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Emails not sending | Check Flask-Mail config + ADMIN_EMAIL env var |
| Contact info not showing | Verify user has active subscription |
| Forum posts not appearing | Check `published = 1` and status = `approved` |
| Approve button doesn't work | Ensure user has admin role |

---

## 📊 Status Fields

**Request Status:**
- `pending_review` - Awaiting admin action
- `approved` - Approved and posted to forum
- `denied` - Rejected with reason
- `closed` - Job filled/expired

**Forum Post:**
- `published = 1` - Visible in forum
- `published = 0` - Hidden

---

## 🎯 Metrics to Track

- **Submissions:** Total requests per week
- **Approval Rate:** % approved vs denied
- **Forum Engagement:** Views per post
- **Conversion:** Forum viewers → subscribers
- **Time to Approval:** Hours from submission to approval

---

## ✅ Completion Status

**Phase 1 (MVP): 87.5% Complete**
- ✅ Database schema
- ✅ Public submission form
- ✅ Admin review interface
- ✅ Approve/deny workflow
- ✅ Email notifications
- ✅ Community forum
- ✅ Subscription-gated browse page
- ⏳ Two-way messaging (future)

---

## 📞 Quick Support

**Admin Panel:** `/admin/1099-cleaner-requests`  
**Public Form:** `/request-1099-cleaners`  
**Community Forum:** `/forum/1099-cleaners`  
**Browse Page:** `/browse-1099-cleaners`

**Environment Variables Needed:**
```env
ADMIN_EMAIL=admin@contractlink.ai
MAIL_DEFAULT_SENDER=noreply@contractlink.ai
```

---

**Version:** 1.0  
**Last Updated:** November 12, 2024  
**Files Modified:** 5 templates, app.py, 1 database script
