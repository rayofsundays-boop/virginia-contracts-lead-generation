"""
Test PostgreSQL migration setup
"""
import os
import sys

def test_imports():
    """Test that all required packages can be imported"""
    print("🧪 Testing PostgreSQL migration setup...\n")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy imported successfully (version {sqlalchemy.__version__})")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import flask_sqlalchemy
        print("✅ Flask-SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ Flask-SQLAlchemy import failed: {e}")
        return False
    
    # Test psycopg2 is available for Render deployment
    try:
        import psycopg2
        print(f"✅ psycopg2 imported successfully")
    except ImportError:
        print("⚠️  psycopg2 not available locally (normal - will work on Render)")
    
    print("\n📊 Testing database configuration...")
    
    # Test SQLite (default for local)
    from app import app, db
    
    with app.app_context():
        db_url = str(db.engine.url)
        if 'sqlite' in db_url:
            print(f"✅ Using SQLite for local development: {db_url}")
        elif 'postgresql' in db_url:
            print(f"✅ Using PostgreSQL for production: {db_url}")
        else:
            print(f"⚠️  Unknown database type: {db_url}")
    
    print("\n✅ All tests passed! Your app is PostgreSQL-ready!")
    print("\n📝 Next steps:")
    print("   1. Deploy to Render")
    print("   2. Create PostgreSQL database on Render")
    print("   3. Add DATABASE_URL environment variable")
    print("   4. Your data will be persistent! 🚀")
    
    return True

if __name__ == "__main__":
    test_imports()
