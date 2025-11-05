# Internal Messaging System Documentation

## Overview
Complete internal mailbox system for customer-to-admin communication, allowing customers to send questions about GSA contracts, billing, technical support, and other inquiries directly to administrators.

## ✅ Features Implemented

### Customer Features
- **Send Messages** - Customers can send categorized messages to admin
- **Message Types** - General, GSA, Contract, Billing, Technical, Other
- **Inbox** - View all messages and admin responses
- **Read Status** - Messages marked as read automatically when viewed
- **Phone Support** - Display of phone number (757) 945-7428

### Admin Features
- **Centralized Mailbox** - View all customer messages in one place
- **Unread Counter** - Badge showing number of unread messages
- **Message Preview** - View full message content in modal
- **Quick Reply** - Reply directly from mailbox with modal form
- **Auto Read Marking** - Original messages marked as read when replied
- **Sorting** - Unread messages shown first, then by date

## Routes

### Customer Routes
- `GET /send-message-to-admin` - Display message form
- `POST /send-message-to-admin` - Submit new message to admin
- `GET /my-messages` - View customer inbox (messages from admin)

### Admin Routes
- `GET /admin/messages` - Admin mailbox showing all customer messages
- `POST /admin/reply-message` - Reply to a customer message

## Database Schema

Uses existing `messages` table:
```sql
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES leads(id),
    recipient_id INTEGER NOT NULL REFERENCES leads(id),
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES leads(id),
    FOREIGN KEY (recipient_id) REFERENCES leads(id)
);
```

## Templates

### `send_message.html`
Customer-facing form to send messages:
- Message type dropdown (general, gsa, contract, billing, technical, other)
- Subject field (200 character limit)
- Message textarea (5000 character limit)
- Phone number display with clickable tel: link
- 24-hour response time notice

### `customer_messages.html`
Customer inbox to view messages from admin:
- List of all messages (sent and received)
- Read/unread visual indicators
- Admin badge for admin replies
- Sender name and timestamp
- Empty state with "Send Message" CTA

### `admin_mailbox.html`
Admin interface to manage customer messages:
- Table view with sortable columns
- Unread count badge in header
- Status icons (envelope/envelope-open)
- View modal with full message content
- Reply modal with original message context
- Auto-prefills "Re: " in subject line

## Navigation Integration

### Customer Navigation (base.html)
Added to user dropdown menu:
- **My Messages** - View inbox (`/my-messages`)
- **Contact Admin** - Send new message (`/send-message-to-admin`)

### Admin Navigation (base.html)
Added to admin section of dropdown:
- **Customer Messages** - View mailbox (`/admin/messages`)

## Message Flow

### Customer Sends Message
1. Customer clicks "Contact Admin" in navigation
2. Fills out form with message type, subject, and message
3. Message inserted into database with `is_admin = FALSE`
4. Subject prefixed with `[TYPE]` (e.g., `[GSA] Question about SAM.gov registration`)
5. Admin user ID automatically determined from database
6. Success flash message shown, redirect to dashboard

### Admin Views Messages
1. Admin clicks "Customer Messages" in navigation
2. System queries all messages where recipient is admin
3. Messages sorted: unread first, then by date descending
4. Unread count badge displayed in header
5. Each message shows status icon, sender info, subject, date

### Admin Replies
1. Admin clicks "Reply" button on any message
2. Reply modal opens with original message context
3. Subject auto-fills with "Re: [original subject]"
4. Admin types response
5. Reply inserted into database with `is_admin = TRUE`
6. Original message marked as `is_read = TRUE`
7. Success flash message, stay on mailbox page

### Customer Views Reply
1. Customer clicks "My Messages" in navigation
2. System queries messages where recipient is customer
3. Admin replies shown with red "From Admin" badge
4. All messages automatically marked as read when viewed

## Security Features
- ✅ `@login_required` decorator on all routes
- ✅ `@admin_required` decorator on admin routes
- ✅ Parameterized SQL queries (no SQL injection)
- ✅ Input validation (required fields, max lengths)
- ✅ Database rollback on errors
- ✅ User can only view their own messages
- ✅ Admin determined by `is_admin = TRUE` in database

## Character Limits
- **Subject**: 200 characters
- **Message Body**: 5000 characters
- **Enforced**: HTML form validation + database constraints

## Future Enhancements (Optional)
- [ ] Email notifications when customer sends message
- [ ] Email notifications when admin replies
- [ ] Message threading/conversations
- [ ] Attachments support
- [ ] Message search functionality
- [ ] Message categories filter in mailbox
- [ ] Bulk actions (mark all as read, delete)
- [ ] Message analytics (response time, volume)
- [ ] Customer satisfaction rating after reply

## Testing Checklist
- [ ] Customer can send message to admin
- [ ] Message appears in admin mailbox with correct info
- [ ] Unread count badge updates correctly
- [ ] Admin can view full message in modal
- [ ] Admin can reply to message
- [ ] Reply appears in customer inbox
- [ ] Original message marked as read after reply
- [ ] Customer sees "From Admin" badge on replies
- [ ] Navigation links work from all pages
- [ ] Empty states display correctly
- [ ] Phone number links work (tel: protocol)
- [ ] Forms validate required fields
- [ ] Character limits enforced
- [ ] Non-admin users cannot access admin routes
- [ ] Flash messages display correctly

## Contact Information
- **Phone**: (757) 945-7428 (clickable in form and footer)
- **Response Time**: 24 hours during business days
- **Location**: Footer and send_message.html template

## Deployment Notes
- No new dependencies required
- Uses existing database table
- No environment variables needed
- Works with current PostgreSQL on Render
- Compatible with existing authentication system

---

**Created**: November 2025  
**Status**: ✅ Complete and ready for testing
