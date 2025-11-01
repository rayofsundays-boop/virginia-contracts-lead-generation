# User Profile & Customer Dashboard Features

## Overview
Complete user profile system with dropdown menu, internal customer dashboard, and subscription management capabilities.

## Features Implemented ✅

### 1. User Profile Dropdown Menu (Upper Right Corner)
**Location:** Navigation bar (upper right) - appears after sign in

**Features:**
- **Avatar Display**: Circular avatar with user's first initial and gradient background
- **User Email**: Shows current signed-in email
- **Subscription Badge**: Shows Premium/Trial/Free status
- **Quick Links:**
  - My Profile - View/edit account details
  - Customer Dashboard - Internal workspace
  - My Leads - Direct access to leads portal
  - Subscription - Manage subscription
  - Cancel Subscription - For paid members only
  - Sign Out - Logout

**Visual Design:**
- Gradient purple avatar (matches brand colors)
- Dropdown menu with icons for each action
- Responsive design (avatar only on mobile, email + avatar on desktop)
- Shadow effects and hover states

### 2. User Profile Page (`/user-profile`)
**Access:** Click "My Profile" from dropdown or navigate directly

**Sections:**
- **Profile Card:**
  - Large avatar with user initial
  - Email address
  - Member since date
  - Subscription status badge
  - Quick action buttons (Dashboard, Upgrade)

- **Activity Stats:**
  - Leads Viewed
  - Saved Opportunities
  - Proposals Submitted

- **Account Information:**
  - Email address
  - Business name
  - Contact person
  - Phone number
  - City location
  - Edit profile button

- **Subscription Details:**
  - Current plan information
  - Billing cycle details
  - Next billing date
  - Premium benefits list
  - Cancel subscription button (paid members)
  - Upgrade button (free/trial members)

- **Password & Security:**
  - Change password functionality
  - Security recommendations

**Modals:**
- Edit Profile Modal - Update business info, contact name, phone, city
- Change Password Modal - Current password verification + new password
- Cancel Subscription Modal - Shared with navigation dropdown

### 3. Customer Dashboard (`/customer-dashboard`)
**Access:** Click "Customer Dashboard" from dropdown or profile page

**Purpose:** Internal workspace/command center for customers

**Features:**
- **Welcome Header:**
  - Personalized greeting with user name
  - Total opportunities count
  - Gradient purple background

- **Quick Stats Cards (4 boxes):**
  - Government Contracts count (blue icon)
  - Supply Opportunities count (green icon)
  - Commercial Leads count (yellow icon)
  - Quick Wins count (red icon)
  - Hover animations on cards

- **Quick Actions Panel:**
  - Large buttons for primary actions:
    - View All Leads
    - Quick Wins
    - Supply Contracts
    - Government Contracts
    - Commercial Leads

- **Latest Opportunities:**
  - Shows 5 most recent leads
  - Mix of government contracts and supply opportunities
  - Each showing: title, agency, location, value, lead type
  - "View" button for each opportunity
  - "View All" link to full leads page

- **Subscription Status Card:**
  - Active premium status (green)
  - Free trial status (blue)
  - Free account with upgrade prompt (yellow)
  - Manage/Upgrade buttons

- **Resources & Support:**
  - Proposal Templates with download link
  - Contract Guide for learning
  - Customer Support contact link
  - Icon-based design with colored backgrounds

### 4. Subscription Management
**Cancel Subscription Feature:**

**Access Points:**
- User Profile dropdown menu (nav bar)
- User Profile page subscription section

**Modal Features:**
- Warning header (red background)
- List of features user will lose
- Note about access until billing period end
- Optional cancellation reason text area
- "Keep Subscription" (secondary) vs "Cancel" (danger) buttons

**Backend Processing:**
- Updates `subscription_status` to 'cancelled'
- Saves cancellation reason
- Records cancellation date
- Updates session immediately
- JSON response for AJAX handling

**Database Changes:**
- New columns: `cancellation_reason` (TEXT), `cancellation_date` (TIMESTAMP)
- Index on cancellation_date for reporting

### 5. Profile Updates
**Edit Profile:**
- Update business name
- Update contact name
- Update phone number
- Select city from dropdown (VA cities)
- Form validation
- Success/error flash messages

**Change Password:**
- Requires current password
- New password (min 8 characters)
- Confirm password matching
- Password hashing with werkzeug
- Current password verification

## Routes Added

### Frontend Routes:
- `GET /user-profile` - User profile page
- `GET /customer-dashboard` - Customer dashboard/internal workspace

### Backend Routes:
- `POST /update-profile` - Update user information
- `POST /change-password` - Change user password
- `POST /cancel-subscription` - Cancel subscription (JSON API)

## Database Migrations

### Local (SQLite):
```bash
sqlite3 leads.db < migrations/add_cancellation_columns.sql
```

### Production (PostgreSQL):
```sql
-- Run migrations/add_cancellation_columns_postgres.sql in Render PostgreSQL shell
```

**Columns Added:**
- `cancellation_reason` TEXT - User's reason for cancelling
- `cancellation_date` TIMESTAMP - When subscription was cancelled

## User Experience Flow

### New User Sign In:
1. User signs in with email/password
2. Profile dropdown appears in upper right (avatar + email)
3. User clicks dropdown to see menu
4. Options: Profile, Dashboard, Leads, Subscription, Sign Out

### Viewing Profile:
1. Click "My Profile" from dropdown
2. See account overview, stats, subscription details
3. Edit profile info via modal
4. Change password via modal
5. Cancel subscription (if paid member)

### Using Dashboard:
1. Click "Customer Dashboard" from dropdown or profile
2. View stats at a glance (government, supply, commercial, quick wins)
3. Use quick action buttons to navigate
4. See latest opportunities feed
5. Check subscription status
6. Access resources and support

### Cancelling Subscription:
1. Click "Cancel Subscription" from dropdown or profile
2. Modal appears with warning
3. Review what will be lost
4. Optionally provide reason
5. Confirm cancellation
6. Redirected to profile with confirmation
7. Access continues until end of billing period

## Visual Design Elements

### Colors:
- **Avatar Gradient**: Purple gradient (#667eea to #764ba2)
- **Premium Badge**: Green (bg-success)
- **Trial Badge**: Blue (bg-info)
- **Free Badge**: Gray (bg-secondary)
- **Dashboard Header**: Purple gradient background

### Icons (Font Awesome):
- User profile: `fa-user-circle`, `fa-user`
- Dashboard: `fa-tachometer-alt`
- Leads: `fa-list`
- Subscription: `fa-crown`
- Cancel: `fa-times-circle`
- Sign out: `fa-sign-out-alt`
- Edit: `fa-edit`
- Password: `fa-key`, `fa-lock`
- Stats: `fa-flag`, `fa-box`, `fa-building`, `fa-bolt`

### Animations:
- Dropdown slide-in effect
- Card hover lift (translateY -5px)
- Shadow transitions
- Button hover states

## Security Features

1. **Login Required**: All profile/dashboard routes use `@login_required` decorator
2. **Password Hashing**: Werkzeug security for password changes
3. **Current Password Verification**: Must verify current password to change
4. **Session Management**: User ID stored in session, verified on each request
5. **CSRF Protection**: Forms submitted via POST with validation
6. **SQL Injection Prevention**: Parameterized queries with SQLAlchemy text()

## Responsive Design

### Mobile (< 768px):
- Avatar only in dropdown (no email text)
- Stacked stats cards
- Full-width action buttons
- Simplified profile layout

### Tablet (768px - 992px):
- Avatar + email in dropdown
- 2-column stats grid
- Responsive sidebar on dashboard

### Desktop (> 992px):
- Full layout with all elements
- 4-column stats grid
- Multi-column dashboard
- Expanded profile details

## Testing Checklist

- [x] Profile dropdown appears after sign in
- [x] Avatar shows correct initial
- [x] Subscription badge shows correct status
- [x] User profile page loads with data
- [x] Edit profile modal works
- [x] Change password validates correctly
- [x] Customer dashboard shows stats
- [x] Latest opportunities display
- [x] Cancel subscription modal appears for paid users
- [x] Cancel subscription updates database
- [x] Sign out clears session

## Next Steps (Optional Enhancements)

1. **Avatar Upload**: Allow users to upload profile photos
2. **Activity Tracking**: Track actual leads viewed/saved
3. **Email Notifications**: Send confirmation emails for profile changes
4. **Two-Factor Authentication**: Add 2FA for enhanced security
5. **Subscription Pause**: Allow users to pause instead of cancel
6. **Dashboard Customization**: Let users customize dashboard widgets
7. **Export Data**: Allow users to export their account data
8. **Dark Mode**: Add dark mode toggle to profile settings

## Support & Documentation

For questions or issues:
- Contact support through dashboard resources section
- Email: support@vacontracts.com
- Check QUICK_START.md for general setup
- See TROUBLESHOOTING.md for common issues
