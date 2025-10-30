# Render.com Environment Variables Setup

## Required Environment Variables for Production

### In Render.com Dashboard:

1. **Go to your Web Service settings**
2. **Click "Environment" tab**
3. **Add these environment variables:**

### SECRET_KEY (Recommended for Security)
```
Key: SECRET_KEY
Value: your-super-secret-random-string-here-make-it-long-and-random
```

### PORT (Automatically set by Render)
```
Key: PORT
Value: (Render sets this automatically)
```

### Optional - Database URL (for future PostgreSQL upgrade)
```
Key: DATABASE_URL
Value: sqlite:///leads.db (or PostgreSQL URL later)
```

## How to Generate a Secure SECRET_KEY

Run this in your terminal to generate a random secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as your SECRET_KEY value in Render.

## Your App Will Work Without These

The app has fallback values, so it will deploy successfully even without setting these environment variables. But for production security, it's recommended to set at least the SECRET_KEY.

## Current Fallback Values:
- SECRET_KEY: 'virginia-contracting-fallback-key-2024'
- DATABASE_URL: 'leads.db' (SQLite file)
- PORT: 8080 (or whatever Render provides)