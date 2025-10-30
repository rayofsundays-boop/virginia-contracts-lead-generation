# Deployment Guide: Flask to Website

## Option 1: Render.com (Free & Easy)

### Step 1: Prepare for Deployment
```bash
# Create a Procfile for Render
echo "web: python app.py" > Procfile

# Update requirements.txt with gunicorn
echo "gunicorn==21.2.0" >> requirements.txt
```

### Step 2: Modify app.py for Production
```python
# Change the last line in app.py from:
app.run(host='0.0.0.0', port=8080, debug=True)

# To:
import os
port = int(os.environ.get('PORT', 8080))
app.run(host='0.0.0.0', port=port, debug=False)
```

### Step 3: Deploy to Render
1. Push code to GitHub repository
2. Go to render.com and create account
3. Connect GitHub repo
4. Deploy as Web Service
5. Your app will be live at: https://yourapp.onrender.com

---

## Option 2: Embed via iframe (Quick Solution)

### Create an iframe embedding code:
```html
<iframe 
    src="http://localhost:8080" 
    width="100%" 
    height="800px" 
    frameborder="0">
    Your browser doesn't support iframes.
</iframe>
```

### For live deployment:
```html
<iframe 
    src="https://your-deployed-app.onrender.com" 
    width="100%" 
    height="800px" 
    frameborder="0"
    style="border: 1px solid #ccc; border-radius: 8px;">
    Loading Virginia Contracts App...
</iframe>
```

---

## Option 3: Static Export (Convert to Static HTML)

### Export database data to JSON:
```python
# Add this route to app.py
@app.route('/export')
def export_data():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('SELECT * FROM contracts')
    contracts = c.fetchall()
    conn.close()
    
    return {
        'contracts': [
            {
                'title': c[1], 'agency': c[2], 'location': c[3],
                'value': c[4], 'deadline': c[5], 'description': c[6]
            } for c in contracts
        ]
    }
```

---

## Option 4: WordPress Integration

### Create WordPress shortcode:
```php
function virginia_contracts_shortcode() {
    return '<iframe src="https://your-app.onrender.com" width="100%" height="800px" frameborder="0"></iframe>';
}
add_shortcode('virginia_contracts', 'virginia_contracts_shortcode');
```

### Use in WordPress:
```
[virginia_contracts]
```

---

## Option 5: Direct HTML Integration

### Extract and modify templates for static hosting:
1. Generate static HTML files from Flask templates
2. Convert database to JavaScript/JSON
3. Host on GitHub Pages, Netlify, or similar

---

## Security Considerations for Public Deployment

### Add environment variables:
```python
import os
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key')
```

### Update database for production:
```python
# Consider PostgreSQL for production
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///leads.db')
```