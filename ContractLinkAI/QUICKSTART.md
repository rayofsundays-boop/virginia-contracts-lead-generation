# ContractLink AI - Quick Deployment Guide

## ⚡ Quick Start (5 Minutes)

### Option 1: Local Development

**Terminal 1 - Backend:**
```bash
cd ContractLinkAI/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd ContractLinkAI/backend
source venv/bin/activate
celery -A contractlink_backend worker -l info
```

**Terminal 3 - Celery Beat:**
```bash
cd ContractLinkAI/backend
source venv/bin/activate
celery -A contractlink_backend beat -l info
```

**Terminal 4 - Frontend:**
```bash
cd ContractLinkAI/frontend
npm install
echo "VITE_API_URL=http://localhost:8000/api" > .env
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

---

### Option 2: Render.com Deployment (Production)

**1. Fork/Clone Repository**

**2. Create Render Account:**
- Sign up at https://render.com

**3. Deploy Backend:**
- Click "New +" → "Blueprint"
- Connect GitHub repository
- Render reads `backend/render.yaml` automatically
- Set environment variables:
  ```
  OPENAI_API_KEY=sk-your-key
  EMAIL_HOST_PASSWORD=your-email-key
  ```
- Click "Apply"

**4. Run Migrations:**
- In Render dashboard → Web Service → Shell:
  ```bash
  python manage.py migrate
  python manage.py createsuperuser
  ```

**5. Deploy Frontend:**
- Click "New +" → "Static Site"
- Build command: `npm run build`
- Publish directory: `dist`
- Environment: `VITE_API_URL=https://your-backend.onrender.com/api`

**Done!** ✅ Your app is live on Render.com

---

## 🔑 Required API Keys

1. **OpenAI API Key** (Required for AI classification)
   - Get at: https://platform.openai.com/api-keys
   - Cost: ~$0.001 per RFP classification
   - Set as: `OPENAI_API_KEY`

2. **Email Service** (Optional but recommended)
   - SendGrid: https://sendgrid.com
   - Mailgun: https://www.mailgun.com
   - Set as: `EMAIL_HOST_PASSWORD`

3. **Django Secret Key** (Required for production)
   - Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Set as: `SECRET_KEY`

---

## 📊 Verify Installation

**Backend Health Check:**
```bash
curl http://localhost:8000/api/rfps/
# Should return JSON with RFPs (empty array if none yet)
```

**Frontend Health Check:**
- Open http://localhost:3000
- Should see ContractLink AI homepage

**Celery Health Check:**
- Check worker terminal for "ready" message
- Check beat terminal for scheduled tasks

**Admin Panel:**
- Open http://localhost:8000/admin
- Login with superuser credentials
- Verify all models appear

---

## 🚀 First Tasks After Installation

1. **Create State Portals** (in Django Admin):
   - Add state portals for states you want to monitor
   - Set portal URLs and scraper configs

2. **Run Initial Scrape** (in Django shell):
   ```python
   from apps.scrapers.tasks import hourly_state_scrape
   hourly_state_scrape.delay()
   ```

3. **Test AI Classification** (in Django shell):
   ```python
   from apps.ai_engine.classifier import AIClassifier
   classifier = AIClassifier()
   result = classifier.classify_rfp(
       "Janitorial Services for County Buildings",
       "Seeking contractor for daily cleaning services..."
   )
   print(result)
   ```

4. **Create Test User** (Frontend):
   - Go to /register
   - Create account
   - Test dashboard, RFP browsing, bookmarking

---

## 🐛 Common Issues & Fixes

### "Module not found" errors
```bash
pip install -r requirements.txt  # Backend
npm install  # Frontend
```

### "Connection refused" to database
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env

### "Connection refused" to Redis
- Ensure Redis is running: `redis-server`
- Check REDIS_URL in .env

### OpenAI API errors
- Verify API key is correct
- Check account has credits
- Test: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### CORS errors in browser
- Check CORS_ALLOWED_ORIGINS in backend settings.py
- Ensure frontend URL is included

### Celery tasks not running
- Check worker logs for errors
- Verify Redis connection
- Ensure migrations are run

---

## 📁 Project Files Checklist

**Backend (Django):**
- ✅ manage.py
- ✅ requirements.txt
- ✅ .env.example (copy to .env)
- ✅ Procfile (Celery workers)
- ✅ render.yaml (Render deployment)
- ✅ contractlink_backend/ (settings, urls, celery)
- ✅ apps/ (6 Django apps)

**Frontend (React):**
- ✅ package.json
- ✅ vite.config.js
- ✅ tailwind.config.js
- ✅ index.html
- ✅ src/ (components, pages, services)

**Documentation:**
- ✅ README.md (comprehensive guide)
- ✅ QUICKSTART.md (this file)

---

## 💡 Tips

**Development:**
- Use Django Debug Toolbar for SQL query analysis
- Use React DevTools for component debugging
- Monitor Celery tasks in Flower: `celery -A contractlink_backend flower`

**Production:**
- Set DEBUG=False in Django
- Use environment variables for all secrets
- Enable logging to file or service (Sentry, etc.)
- Set up monitoring for Celery workers
- Use CDN for static assets
- Enable database backups

**Performance:**
- Add database indexes for frequently queried fields
- Use Redis caching for expensive queries
- Paginate large result sets
- Optimize images and assets

---

## 🎓 Learning Resources

**Django:**
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/

**Celery:**
- https://docs.celeryq.dev/

**React:**
- https://react.dev/
- https://reactrouter.com/

**Tailwind CSS:**
- https://tailwindcss.com/docs

**OpenAI:**
- https://platform.openai.com/docs/

---

## 🚀 You're Ready!

Your ContractLink AI platform is ready to discover and classify government contracts!

**Next:** Add state-specific scrapers and start monitoring procurement portals.

---

**Need Help?**
- 📖 Full docs: README.md
- 🐛 Issues: GitHub Issues
- 💬 Support: support@contractlink.ai
