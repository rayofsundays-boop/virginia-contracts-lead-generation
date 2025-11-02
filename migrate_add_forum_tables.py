#!/usr/bin/env python3
"""
Migration script to add community forum discussion tables
Enables users to discuss opportunities and admins to post new proposals
"""

from app import app, db
from sqlalchemy import text

def run_migration():
    """Add forum_posts and forum_comments tables"""
    
    with app.app_context():
        print("🔧 Starting migration: Adding community forum discussion tables...")
        
        try:
            # Create forum_posts table
            print("📝 Creating forum_posts table...")
            db.session.execute(text('''
                CREATE TABLE IF NOT EXISTS forum_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    post_type TEXT DEFAULT 'discussion',
                    user_email TEXT NOT NULL,
                    user_name TEXT,
                    related_lead_id TEXT,
                    related_lead_type TEXT,
                    is_admin_post BOOLEAN DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # Create forum_comments table
            print("📝 Creating forum_comments table...")
            db.session.execute(text('''
                CREATE TABLE IF NOT EXISTS forum_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    user_email TEXT NOT NULL,
                    user_name TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    parent_comment_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES forum_posts (id),
                    FOREIGN KEY (parent_comment_id) REFERENCES forum_comments (id)
                )
            '''))
            
            # Create forum_post_likes table
            print("📝 Creating forum_post_likes table...")
            db.session.execute(text('''
                CREATE TABLE IF NOT EXISTS forum_post_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_email TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, user_email),
                    FOREIGN KEY (post_id) REFERENCES forum_posts (id)
                )
            '''))
            
            db.session.commit()
            print("✅ All forum tables created successfully!")
            
            # Create sample admin post
            print("\n📊 Creating sample admin welcome post...")
            db.session.execute(text('''
                INSERT OR IGNORE INTO forum_posts 
                (title, content, post_type, user_email, user_name, is_admin_post, status)
                VALUES 
                (:title, :content, :type, :email, :name, 1, 'active')
            '''), {
                'title': 'Welcome to the Virginia Contracts Community Forum!',
                'content': '''Welcome to our community forum! 🎉

This is your space to:
✅ Discuss cleaning contract opportunities across Virginia
✅ Share bidding strategies and proposal tips
✅ Ask questions and get advice from experienced contractors
✅ See new commercial and residential cleaning requests posted by our team
✅ Network with other cleaning professionals

**How it works:**
- Browse opportunities posted by our admin team from submitted requests
- Start discussions about specific contracts or general topics
- Comment on posts to share your insights
- Like helpful posts and comments

**Admin Posts:**
Our team will regularly post new opportunities from:
- Commercial businesses seeking cleaning services
- Residential clients looking for cleaners
- Government contract opportunities
- Supply and vendor opportunities

Let's build a thriving community together! Feel free to introduce yourself and share what types of contracts you're interested in.

Best regards,
Virginia Contracts Lead Generation Team''',
                'type': 'announcement',
                'email': 'admin@vacontracts.com',
                'name': 'Admin Team'
            })
            db.session.commit()
            
            print("✅ Sample post created!")
            
            # Show statistics
            post_count = db.session.execute(text("SELECT COUNT(*) FROM forum_posts")).scalar()
            print(f"\n📈 Forum Statistics:")
            print(f"   - Total posts: {post_count}")
            print(f"\n🎯 Forum is ready at: /community-forum")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()


if __name__ == '__main__':
    run_migration()
