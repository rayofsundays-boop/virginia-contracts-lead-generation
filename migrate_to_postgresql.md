# PostgreSQL Migration Guide

Your app is now **PostgreSQL-ready**! Here's how to deploy with persistent database storage:

## What Changed:

✅ Added PostgreSQL support packages to `requirements.txt`:
- `psycopg2-binary` - PostgreSQL adapter
- `SQLAlchemy` - Database ORM
- `Flask-SQLAlchemy` - Flask integration

✅ Updated `app.py` to auto-detect database:
- Uses PostgreSQL if `DATABASE_URL` environment variable is set
- Falls back to SQLite for local development
- Works seamlessly with both!

## Local Development (SQLite):

```bash
# No changes needed - continues using SQLite
python app.py
```

## Deploy to Render with PostgreSQL:

### Step 1: Create PostgreSQL Database on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Name: `virginia-leads-db`
4. Plan: **Free** (up to 1GB storage)
5. Click **Create Database**
6. Wait for it to provision (~2 minutes)
7. Copy the **Internal Database URL** (starts with `postgresql://`)

### Step 2: Deploy Your Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repo: `virginia-contracts-lead-generation`
3. Configure:
   - **Name**: `virginia-contracts`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Plan**: Free

### Step 3: Add Environment Variables

In your web service settings, add:

```
SECRET_KEY=your-secret-production-key-here
DATABASE_URL=<paste-your-postgresql-internal-url>
```

### Step 4: Deploy!

1. Click **Create Web Service**
2. Render will automatically deploy
3. Your database tables will be created automatically on first run
4. All 150+ leads will be added on first launch

## Benefits of PostgreSQL:

✅ **Persistent Storage** - Data survives deploys and restarts  
✅ **Concurrent Users** - Handles multiple users simultaneously  
✅ **Production-Ready** - Used by millions of applications  
✅ **Automatic Backups** - Render provides daily backups  
✅ **Better Performance** - Optimized for web applications  

## Verify Migration:

After deploying, check your logs in Render:
- Should see: "✅ Database tables created successfully!"
- Should see leads being added
- No errors about database connections

## Rollback Plan:

If you need to go back to SQLite locally:
1. Remove or comment out the `DATABASE_URL` environment variable
2. App will automatically use SQLite
3. Your local `leads.db` file remains unchanged

---

**Your app now works with both SQLite (dev) and PostgreSQL (production)!** 🚀
