"""
External Email Service
Secure SMTP/TLS email sending with HTML support, tracking, and error handling.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text

from app import db


class ExternalEmailService:
    """Service for sending external emails via SMTP with tracking"""
    
    def __init__(self):
        """Initialize SMTP configuration from environment variables"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', os.getenv('EMAIL_USER', ''))
        self.smtp_password = os.getenv('SMTP_PASSWORD', os.getenv('EMAIL_PASSWORD', ''))
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'ContractLink.ai')
        
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def send_external_email(
        self,
        to_email: str,
        subject: str,
        message_body: str,
        message_html: Optional[str] = None,
        sender_user_id: Optional[int] = None,
        sender_username: Optional[str] = None,
        sender_email: Optional[str] = None,
        message_type: str = 'general',
        recipient_name: Optional[str] = None,
        priority: str = 'normal',
        tags: Optional[str] = None,
        campaign_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an external email via SMTP with TLS/SSL encryption.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            message_body: Plain text message body
            message_html: Optional HTML version of message
            sender_user_id: User ID of sender
            sender_username: Username of sender
            sender_email: Email of sender
            message_type: Type of message (general, support, marketing, etc.)
            recipient_name: Optional recipient name
            priority: Email priority (normal, high, low)
            tags: Optional comma-separated tags
            campaign_id: Optional campaign identifier
            ip_address: IP address of sender
            user_agent: User agent of sender
            
        Returns:
            Dict with 'success' boolean, 'message', and 'email_id' if successful
        """
        
        # Validation
        if not self.validate_email(to_email):
            return {
                'success': False,
                'message': 'Invalid email address format',
                'email_id': None
            }
        
        if not subject or not subject.strip():
            return {
                'success': False,
                'message': 'Subject cannot be empty',
                'email_id': None
            }
        
        if not message_body or not message_body.strip():
            return {
                'success': False,
                'message': 'Message body cannot be empty',
                'email_id': None
            }
        
        if not self.smtp_user or not self.smtp_password:
            return {
                'success': False,
                'message': 'SMTP credentials not configured',
                'email_id': None
            }
        
        # Create database record first
        try:
            result = db.session.execute(text("""
                INSERT INTO external_emails (
                    sender_user_id, sender_username, sender_email, is_admin_sender,
                    recipient_email, recipient_name, message_type, subject,
                    message_body, message_html, status, priority, tags, campaign_id,
                    ip_address, user_agent, created_at, updated_at
                ) VALUES (
                    :sender_user_id, :sender_username, :sender_email, :is_admin,
                    :recipient_email, :recipient_name, :message_type, :subject,
                    :message_body, :message_html, 'pending', :priority, :tags, :campaign_id,
                    :ip_address, :user_agent, :created_at, :updated_at
                )
                RETURNING id
            """), {
                'sender_user_id': sender_user_id,
                'sender_username': sender_username,
                'sender_email': sender_email,
                'is_admin': 1,  # Mark as admin sender
                'recipient_email': to_email,
                'recipient_name': recipient_name,
                'message_type': message_type,
                'subject': subject,
                'message_body': message_body,
                'message_html': message_html,
                'priority': priority,
                'tags': tags,
                'campaign_id': campaign_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            email_id = result.fetchone()[0]
            db.session.commit()
            print(f"[EMAIL] Created email record: {email_id}")
        except Exception as db_err:
            db.session.rollback()
            print(f"[EMAIL] Database error: {db_err}")
            return {
                'success': False,
                'message': f'Database error: {str(db_err)}',
                'email_id': None
            }
        
        # Send email via SMTP
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add priority header
            if priority == 'high':
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif priority == 'low':
                msg['X-Priority'] = '5'
                msg['X-MSMail-Priority'] = 'Low'
            
            # Attach plain text version
            text_part = MIMEText(message_body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Attach HTML version if provided
            if message_html:
                html_part = MIMEText(message_html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Create secure SSL context
            context = ssl.create_default_context()
            
            # Connect and send
            print(f"[EMAIL] Connecting to {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)  # Secure with TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            # Update database record as sent
            db.session.execute(text("""
                UPDATE external_emails
                SET status = 'sent',
                    sent_at = :sent_at,
                    delivery_attempted = 1,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                'sent_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'id': email_id
            })
            db.session.commit()
            
            print(f"[EMAIL] ✅ Successfully sent email {email_id} to {to_email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'email_id': email_id
            }
            
        except smtplib.SMTPAuthenticationError as auth_err:
            error_msg = f'SMTP authentication failed: {str(auth_err)}'
            print(f"[EMAIL] ❌ {error_msg}")
            
            # Update database with error
            db.session.execute(text("""
                UPDATE external_emails
                SET status = 'failed',
                    delivery_attempted = 1,
                    delivery_error = :error,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                'error': error_msg,
                'updated_at': datetime.utcnow(),
                'id': email_id
            })
            db.session.commit()
            
            return {
                'success': False,
                'message': 'Email authentication failed. Check SMTP credentials.',
                'email_id': email_id
            }
            
        except smtplib.SMTPException as smtp_err:
            error_msg = f'SMTP error: {str(smtp_err)}'
            print(f"[EMAIL] ❌ {error_msg}")
            
            db.session.execute(text("""
                UPDATE external_emails
                SET status = 'failed',
                    delivery_attempted = 1,
                    delivery_error = :error,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                'error': error_msg,
                'updated_at': datetime.utcnow(),
                'id': email_id
            })
            db.session.commit()
            
            return {
                'success': False,
                'message': f'Email delivery failed: {str(smtp_err)}',
                'email_id': email_id
            }
            
        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            print(f"[EMAIL] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            db.session.execute(text("""
                UPDATE external_emails
                SET status = 'failed',
                    delivery_attempted = 1,
                    delivery_error = :error,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                'error': error_msg,
                'updated_at': datetime.utcnow(),
                'id': email_id
            })
            db.session.commit()
            
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'email_id': email_id
            }


# Global instance
email_service = ExternalEmailService()


def send_external_email(**kwargs) -> Dict[str, Any]:
    """
    Convenience function to send external email.
    
    Usage:
        result = send_external_email(
            to_email='user@example.com',
            subject='Hello',
            message_body='This is a test',
            message_html='<p>This is a <b>test</b></p>',
            sender_user_id=1,
            message_type='support'
        )
        
        if result['success']:
            print(f"Email sent! ID: {result['email_id']}")
        else:
            print(f"Failed: {result['message']}")
    """
    return email_service.send_external_email(**kwargs)
