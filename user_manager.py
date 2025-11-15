"""
User Management Helper Functions
Provides utilities for user CRUD operations, authentication, and session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import pyotp

from app import db


class UserManager:
    """User management utilities"""
    
    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        **kwargs
    ) -> Optional[int]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            phone: Phone number
            company_name: Company name
            **kwargs: Additional fields (subscription_tier, lead_source, etc.)
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            # Check if user already exists
            existing = db.session.execute(text("""
                SELECT id FROM users WHERE email = :email OR username = :username
            """), {'email': email, 'username': username}).fetchone()
            
            if existing:
                print(f"[USER_MGR] User already exists: {email}")
                return None
            
            # Generate password hash
            password_hash = generate_password_hash(password)
            
            # Prepare full name
            full_name = f"{first_name or ''} {last_name or ''}".strip() or username
            
            # Insert user
            result = db.session.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name, full_name,
                    phone, company_name, is_active, is_verified, 
                    subscription_status, subscription_tier, free_credits_remaining,
                    lead_source, created_at, updated_at
                ) VALUES (
                    :username, :email, :password_hash, :first_name, :last_name, :full_name,
                    :phone, :company_name, 1, 0,
                    :subscription_status, :subscription_tier, :free_credits,
                    :lead_source, :created_at, :updated_at
                )
                RETURNING id
            """), {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'phone': phone,
                'company_name': company_name,
                'subscription_status': kwargs.get('subscription_status', 'free'),
                'subscription_tier': kwargs.get('subscription_tier', 'free'),
                'free_credits': kwargs.get('free_credits_remaining', 3),
                'lead_source': kwargs.get('lead_source', 'website'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
            user_id = result.fetchone()[0]
            db.session.commit()
            
            print(f"[USER_MGR] Created user: {username} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            db.session.rollback()
            print(f"[USER_MGR] Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = db.session.execute(text("""
                SELECT * FROM users WHERE id = :id AND is_deleted = 0
            """), {'id': user_id}).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            print(f"[USER_MGR] Error fetching user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            result = db.session.execute(text("""
                SELECT * FROM users WHERE LOWER(email) = LOWER(:email) AND is_deleted = 0
            """), {'email': email}).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            print(f"[USER_MGR] Error fetching user: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            result = db.session.execute(text("""
                SELECT * FROM users WHERE LOWER(username) = LOWER(:username) AND is_deleted = 0
            """), {'username': username}).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            print(f"[USER_MGR] Error fetching user: {e}")
            return None
    
    @staticmethod
    def authenticate(identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username/email and password.
        
        Args:
            identifier: Username or email
            password: Plain text password
            
        Returns:
            User dict if authenticated, None otherwise
        """
        try:
            # Find user by username or email
            result = db.session.execute(text("""
                SELECT * FROM users 
                WHERE (LOWER(username) = LOWER(:identifier) OR LOWER(email) = LOWER(:identifier))
                AND is_active = 1 AND is_deleted = 0
            """), {'identifier': identifier}).fetchone()
            
            if not result:
                print(f"[USER_MGR] User not found: {identifier}")
                return None
            
            user = dict(result._mapping)
            
            # Check if account is locked
            if user.get('account_locked_until'):
                lock_time = user['account_locked_until']
                if isinstance(lock_time, str):
                    lock_time = datetime.fromisoformat(lock_time)
                if datetime.utcnow() < lock_time:
                    print(f"[USER_MGR] Account locked until {lock_time}")
                    return None
            
            # Verify password
            if not check_password_hash(user['password_hash'], password):
                # Increment failed attempts
                failed_attempts = user.get('failed_login_attempts', 0) + 1
                
                # Lock account after 5 failed attempts
                lock_until = None
                if failed_attempts >= 5:
                    lock_until = datetime.utcnow() + timedelta(minutes=30)
                
                db.session.execute(text("""
                    UPDATE users 
                    SET failed_login_attempts = :attempts,
                        account_locked_until = :lock_until
                    WHERE id = :id
                """), {
                    'attempts': failed_attempts,
                    'lock_until': lock_until,
                    'id': user['id']
                })
                db.session.commit()
                
                print(f"[USER_MGR] Invalid password for {identifier} (attempt {failed_attempts})")
                return None
            
            # Successful login - reset failed attempts and update last login
            db.session.execute(text("""
                UPDATE users 
                SET failed_login_attempts = 0,
                    account_locked_until = NULL,
                    last_login = :now
                WHERE id = :id
            """), {
                'now': datetime.utcnow(),
                'id': user['id']
            })
            db.session.commit()
            
            print(f"[USER_MGR] Authentication successful: {identifier}")
            return user
            
        except Exception as e:
            print(f"[USER_MGR] Authentication error: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def update_user(user_id: int, **fields) -> bool:
        """Update user fields"""
        try:
            if not fields:
                return False
            
            # Build SET clause
            set_parts = []
            params = {'id': user_id, 'updated_at': datetime.utcnow()}
            
            for field, value in fields.items():
                set_parts.append(f"{field} = :{field}")
                params[field] = value
            
            set_clause = ", ".join(set_parts)
            
            db.session.execute(text(f"""
                UPDATE users 
                SET {set_clause}, updated_at = :updated_at
                WHERE id = :id
            """), params)
            
            db.session.commit()
            print(f"[USER_MGR] Updated user {user_id}: {', '.join(fields.keys())}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[USER_MGR] Error updating user: {e}")
            return False
    
    @staticmethod
    def change_password(user_id: int, new_password: str) -> bool:
        """Change user password"""
        try:
            password_hash = generate_password_hash(new_password)
            
            db.session.execute(text("""
                UPDATE users 
                SET password_hash = :hash, updated_at = :now
                WHERE id = :id
            """), {
                'hash': password_hash,
                'now': datetime.utcnow(),
                'id': user_id
            })
            
            db.session.commit()
            print(f"[USER_MGR] Password changed for user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[USER_MGR] Error changing password: {e}")
            return False
    
    @staticmethod
    def soft_delete_user(user_id: int) -> bool:
        """Soft delete user (mark as deleted)"""
        try:
            db.session.execute(text("""
                UPDATE users 
                SET is_deleted = 1, 
                    is_active = 0,
                    deleted_at = :now,
                    updated_at = :now
                WHERE id = :id
            """), {
                'now': datetime.utcnow(),
                'id': user_id
            })
            
            db.session.commit()
            print(f"[USER_MGR] Soft deleted user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[USER_MGR] Error deleting user: {e}")
            return False
    
    @staticmethod
    def list_users(
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
        subscription_tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List users with filtering"""
        try:
            conditions = ["is_deleted = 0"]
            params = {'limit': limit, 'offset': offset}
            
            if is_active is not None:
                conditions.append("is_active = :is_active")
                params['is_active'] = is_active
            
            if subscription_tier:
                conditions.append("subscription_tier = :tier")
                params['tier'] = subscription_tier
            
            where_clause = " AND ".join(conditions)
            
            results = db.session.execute(text(f"""
                SELECT * FROM users
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), params).fetchall()
            
            return [dict(row._mapping) for row in results]
            
        except Exception as e:
            print(f"[USER_MGR] Error listing users: {e}")
            return []


# Activity logging helper
def log_user_activity(
    user_id: int,
    activity_type: str,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[str] = None
):
    """Log user activity"""
    try:
        db.session.execute(text("""
            INSERT INTO user_activity_log (
                user_id, activity_type, activity_description,
                ip_address, user_agent, metadata, created_at
            ) VALUES (
                :user_id, :activity_type, :description,
                :ip_address, :user_agent, :metadata, :created_at
            )
        """), {
            'user_id': user_id,
            'activity_type': activity_type,
            'description': description,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata': metadata,
            'created_at': datetime.utcnow()
        })
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[USER_ACTIVITY] Error logging: {e}")
