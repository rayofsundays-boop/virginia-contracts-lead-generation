# ContractLink AI - Government Procurement SaaS Platform

**Full-Stack Production SaaS Platform** for discovering, classifying, and delivering government procurement opportunities from all 50 US states using AI-powered automation.

## 🚀 Features

### Backend (Django + Celery + AI)
- ✅ **Django REST API** with full CRUD operations
- ✅ **PostgreSQL Database** with production-ready schema
- ✅ **Celery Workers** for background scraping and AI tasks
- ✅ **Redis** for task queue and caching
- ✅ **OpenAI GPT-4o-mini Integration** for RFP classification
- ✅ **Automated Web Scrapers** for 50 state portals
- ✅ **AI-Powered City Discovery** using GPT-4
- ✅ **Real-time Notifications** system
- ✅ **Email Digest** functionality
- ✅ **JWT Authentication** with Django Rest Framework
- ✅ **Production-Ready Deployment** on Render.com

### Frontend (React + Vite + Tailwind CSS)
- ✅ **React 18** with modern hooks
- ✅ **Vite** for lightning-fast dev server
- ✅ **Tailwind CSS** for responsive design
- ✅ **React Router** for navigation
- ✅ **Axios** for API integration
- ✅ **Dashboard** with statistics
- ✅ **RFP Search & Filtering**
- ✅ **User Authentication** (Login/Register)
- ✅ **Bookmark Management**
- ✅ **Settings & Preferences**

---

## 📁 Project Structure

```
ContractLinkAI/
├── backend/                          # Django Backend
│   ├── contractlink_backend/         # Main project settings
│   │   ├── settings.py              # Production settings
│   │   ├── urls.py                  # URL routing
│   │   ├── celery.py                # Celery configuration
│   │   ├── wsgi.py                  # WSGI application
│   │   └── asgi.py                  # ASGI application
│   │
│   ├── apps/                        # Django apps
│   │   ├── users/                   # User management
│   │   │   ├── models.py           # Custom User model
│   │   │   ├── serializers.py      # User API serializers
│   │   │   ├── views.py            # User API views
│   │   │   ├── urls.py             # User routes
│   │   │   └── admin.py            # Admin configuration
│   │   │
│   │   ├── rfps/                    # RFP management
│   │   │   ├── models.py           # RFP, SavedRFP, RFPActivity
│   │   │   ├── serializers.py      # RFP API serializers
│   │   │   ├── views.py            # RFP API views
│   │   │   ├── urls.py             # RFP routes
│   │   │   ├── tasks.py            # Celery tasks for RFPs
│   │   │   └── admin.py            # Admin configuration
│   │   │
│   │   ├── states/                  # State/City portals
│   │   │   ├── models.py           # StatePortal, CityPortal, VendorRegistration
│   │   │   ├── serializers.py      # State API serializers
│   │   │   ├── views.py            # State API views
│   │   │   ├── urls.py             # State routes
│   │   │   └── admin.py            # Admin configuration
│   │   │
│   │   ├── scrapers/                # Web scraping system
│   │   │   ├── models.py           # ScrapeJob, ScrapeError
│   │   │   ├── scraper_base.py     # Base scraper classes
│   │   │   ├── rfp_parser.py       # RFP parsing utilities
│   │   │   ├── tasks.py            # Celery scraping tasks
│   │   │   └── urls.py             # Scraper API routes
│   │   │
│   │   ├── ai_engine/               # AI classification system
│   │   │   ├── models.py           # AIClassification, AIPortalDiscovery
│   │   │   ├── classifier.py       # OpenAI integration
│   │   │   └── tasks.py            # AI Celery tasks
│   │   │
│   │   └── notifications/           # Notification system
│   │       ├── models.py           # Notification, EmailDigest
│   │       └── tasks.py            # Email notification tasks
│   │
│   ├── manage.py                    # Django management command
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment variables template
│   ├── Procfile                     # Celery worker commands
│   └── render.yaml                  # Render.com deployment config
│
├── frontend/                        # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── Navbar.jsx          # Navigation component
│   │   │
│   │   ├── pages/
│   │   │   ├── HomePage.jsx        # Landing page
│   │   │   ├── RFPsPage.jsx        # RFP listing
│   │   │   ├── StatesPage.jsx      # State portals
│   │   │   ├── CitiesPage.jsx      # City portals
│   │   │   ├── LoginPage.jsx       # Login form
│   │   │   ├── RegisterPage.jsx    # Registration form
│   │   │   ├── DashboardPage.jsx   # User dashboard
│   │   │   └── SettingsPage.jsx    # User settings
│   │   │
│   │   ├── services/
│   │   │   └── api.js              # Axios API client
│   │   │
│   │   ├── App.jsx                 # Main app component
│   │   ├── main.jsx                # React entry point
│   │   └── index.css               # Tailwind CSS imports
│   │
│   ├── index.html                   # HTML template
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js              # Vite configuration
│   ├── tailwind.config.js          # Tailwind configuration
│   └── postcss.config.js           # PostCSS configuration
│
└── README.md                        # This file
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- OpenAI API Key

### Backend Setup

1. **Clone repository and navigate to backend:**
```bash
cd ContractLinkAI/backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your settings:
# - SECRET_KEY
# - DATABASE_URL
# - REDIS_URL
# - OPENAI_API_KEY
# - EMAIL credentials
```

5. **Run migrations:**
```bash
python manage.py migrate
```

6. **Create superuser:**
```bash
python manage.py createsuperuser
```

7. **Collect static files:**
```bash
python manage.py collectstatic --no-input
```

8. **Start development server:**
```bash
python manage.py runserver
```

9. **Start Celery worker (new terminal):**
```bash
celery -A contractlink_backend worker --loglevel=info
```

10. **Start Celery beat scheduler (new terminal):**
```bash
celery -A contractlink_backend beat --loglevel=info
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd ContractLinkAI/frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Create environment file:**
```bash
echo "VITE_API_URL=http://localhost:8000/api" > .env
```

4. **Start development server:**
```bash
npm run dev
```

5. **Open browser:**
```
http://localhost:3000
```

---

## 🚀 Deployment to Render.com

### Backend Deployment

1. **Create Render.com account** at https://render.com

2. **Create New Blueprint:**
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically

3. **Configure Environment Variables:**
   Set these in Render dashboard:
   - `SECRET_KEY`: Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `EMAIL_HOST_PASSWORD`: Email service API key (SendGrid, Mailgun, etc.)

4. **Deploy:**
   - Render will automatically create:
     - Web service (Django)
     - Worker service (Celery)
     - Scheduler service (Celery Beat)
     - Redis instance
     - PostgreSQL database
   - All services are configured in `render.yaml`

5. **Run migrations:**
   - In Render dashboard → Web Service → Shell
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Frontend Deployment

1. **Build for production:**
```bash
cd frontend
npm run build
```

2. **Deploy to Render Static Site:**
   - Create new "Static Site" on Render
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Add environment variable: `VITE_API_URL=https://your-backend.onrender.com/api`

---

## 📊 Database Models

### User Model
- Custom user with subscription fields
- Notification preferences
- Preferred states/categories
- Minimum contract value filters

### RFP Model
- RFP number, title, description
- Source information (state, city, agency)
- AI classification category & confidence
- Contract value, duration
- Posted date, due date
- Contact information
- Keywords, NAICS codes

### StatePortal Model
- State code, name
- Portal URL, registration URL
- Scraper configuration
- Statistics (total RFPs, success/failure rates)

### CityPortal Model
- City name, state
- Portal URL discovered by AI
- Discovery confidence score
- Verification status

### VendorRegistration Model
- User vendor registrations
- Registration status
- Vendor ID, certifications
- Expiration tracking

---

## 🤖 Celery Tasks

### Hourly State Scrape
**Schedule:** Every hour at :00
**Task:** `scrapers.tasks.hourly_state_scrape`
- Scrapes all 50 active state portals
- Saves new RFPs to database
- Updates portal statistics

### Nightly City Discovery
**Schedule:** Daily at 2:00 AM
**Task:** `scrapers.tasks.nightly_city_discovery`
- Uses AI to discover city portals
- Processes 10 major cities per night
- Only saves high-confidence results (>0.6)

### AI Classification
**Schedule:** Every 30 minutes
**Task:** `ai_engine.tasks.classify_new_rfps`
- Classifies unclassified RFPs
- Processes 50 RFPs per run
- Updates category and confidence score

### Email Notifications
**Schedule:** Daily at 8:00 AM
**Task:** `notifications.tasks.send_notification_emails`
- Sends daily digest emails
- Filters by user preferences
- Tracks email opens/clicks

### Cleanup Old RFPs
**Schedule:** Weekly on Sunday at 3:00 AM
**Task:** `rfps.tasks.cleanup_old_rfps`
- Marks expired RFPs (>90 days old)
- Optionally deletes very old RFPs

---

## 🔧 API Endpoints

### Authentication
```
POST   /api/auth/register/          Register new user
POST   /api/auth/token/             Login (get auth token)
GET    /api/auth/users/me/          Get current user
PATCH  /api/auth/users/update_profile/  Update profile
GET    /api/auth/users/settings/    Get user settings
PATCH  /api/auth/users/settings/    Update settings
```

### RFPs
```
GET    /api/rfps/                   List all RFPs (paginated)
GET    /api/rfps/{id}/              Get RFP detail
GET    /api/rfps/my_bookmarks/      Get user's bookmarked RFPs
POST   /api/rfps/{id}/bookmark/     Bookmark an RFP
POST   /api/rfps/{id}/unbookmark/   Remove bookmark
GET    /api/rfps/statistics/        Get RFP statistics
```

### States
```
GET    /api/states/                 List all state portals
GET    /api/states/{id}/            Get state portal detail
GET    /api/states/{id}/cities/     Get cities for a state
```

### Cities
```
GET    /api/states/cities/          List all city portals
GET    /api/cities/                 Search cities
```

### Vendor Registrations
```
GET    /api/states/vendor-registrations/  List user's registrations
POST   /api/states/vendor-registrations/  Create registration
PATCH  /api/states/vendor-registrations/{id}/  Update registration
```

---

## 🎨 Frontend Pages

1. **Home Page** (`/`)
   - Hero section with CTA
   - Feature highlights
   - Statistics showcase

2. **RFPs Page** (`/rfps`)
   - Searchable RFP listing
   - Filters (state, category, active only)
   - Bookmark functionality
   - Pagination

3. **States Page** (`/states`)
   - List of all 50 states
   - RFP count per state
   - Quick navigation

4. **Dashboard** (`/dashboard`)
   - User statistics
   - Recent activity
   - Bookmarked RFPs

5. **Login/Register** (`/login`, `/register`)
   - Authentication forms
   - JWT token management

6. **Settings** (`/settings`)
   - User preferences
   - Notification settings
   - Profile management

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

---

## 📝 Environment Variables

### Backend (.env)
```env
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-openai-key
EMAIL_HOST_PASSWORD=your-email-api-key
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api
```

---

## 📚 Technology Stack

**Backend:**
- Django 5.0
- Django REST Framework 3.14
- Celery 5.3
- Redis 5.0
- PostgreSQL 14+
- httpx + BeautifulSoup4
- OpenAI Python SDK
- Gunicorn (production server)

**Frontend:**
- React 18
- Vite 5
- Tailwind CSS 3
- React Router DOM 6
- Axios
- Heroicons

**Deployment:**
- Render.com (Backend + Workers)
- Render Static Sites (Frontend)
- PostgreSQL (Managed database)
- Redis (Managed cache)

---

## 🔐 Security

- ✅ CSRF protection enabled
- ✅ Secure password hashing
- ✅ JWT token authentication
- ✅ HTTPS enforced in production
- ✅ CORS properly configured
- ✅ Rate limiting on API endpoints
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection

---

## 📈 Performance

- **Database Indexing:** Optimized queries with proper indexes
- **Caching:** Redis caching for frequently accessed data
- **Pagination:** API responses paginated (50 items per page)
- **Async Scraping:** Concurrent requests with httpx
- **Static Files:** WhiteNoise for efficient static file serving
- **CDN Ready:** Static assets can be served from CDN

---

## 🐛 Troubleshooting

### Django won't start
- Check `.env` file exists and has correct values
- Verify PostgreSQL is running
- Run migrations: `python manage.py migrate`

### Celery worker not running
- Ensure Redis is running: `redis-cli ping`
- Check Celery logs for errors
- Verify `REDIS_URL` in `.env`

### Frontend can't connect to API
- Check `VITE_API_URL` in frontend `.env`
- Verify Django backend is running
- Check CORS settings in Django

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI account has credits
- Monitor rate limits

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@contractlink.ai
- Documentation: [Full docs]

---

## 🎉 Success!

You now have a fully functional, production-ready SaaS platform for government procurement! 🚀

**Next Steps:**
1. Configure state-specific scrapers in `apps/scrapers/scraper_base.py`
2. Customize email templates in notification tasks
3. Add more RFP categories as needed
4. Set up monitoring with Sentry or similar
5. Configure analytics with Google Analytics
6. Add payment integration (Stripe, etc.)

---

**Built with ❤️ using Django + React + AI**
