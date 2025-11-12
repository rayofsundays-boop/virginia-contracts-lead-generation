"""
Beta Tester Renewal Reminder Script
Sends email reminders to beta testers 30 days before expiry
Run this daily via cron job
"""
from app import app, db
from sqlalchemy import text
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_renewal_reminder(email, contact_name, days_remaining, expiry_date):
    """Send renewal reminder email to beta tester"""
    try:
        smtp_server = app.config.get('MAIL_SERVER')
        smtp_port = app.config.get('MAIL_PORT', 587)
        smtp_user = app.config.get('MAIL_USERNAME')
        smtp_password = app.config.get('MAIL_PASSWORD')
        
        if not all([smtp_server, smtp_user, smtp_password]):
            print(f"⚠️  Email not configured - skipping reminder for {email}")
            return False
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🌟 Beta Tester Membership Expiring in {days_remaining} Days'
        msg['From'] = smtp_user
        msg['To'] = email
        
        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">⏰ Beta Tester Renewal Reminder</h1>
            </div>
            
            <div style="padding: 30px; background-color: #f8f9fa;">
                <h2 style="color: #333;">Hi {contact_name},</h2>
                
                <p style="font-size: 16px; color: #555;">
                    Your <strong>1-year Beta Tester membership</strong> is expiring soon!
                </p>
                
                <div style="background: white; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 18px;"><strong>⏰ Time Remaining:</strong> {days_remaining} days</p>
                    <p style="margin: 10px 0 0 0; color: #666;"><strong>Expiry Date:</strong> {expiry_date.strftime('%B %d, %Y')}</p>
                </div>
                
                <h3 style="color: #333;">What You've Enjoyed as a Beta Tester:</h3>
                <ul style="color: #555; line-height: 1.8;">
                    <li>✅ Full Premium platform access</li>
                    <li>✅ Unlimited contract leads and downloads</li>
                    <li>✅ Priority customer support</li>
                    <li>✅ Early access to new features</li>
                </ul>
                
                <h3 style="color: #333;">Continue Your Premium Access:</h3>
                <p style="color: #555;">
                    To maintain your Premium access after {expiry_date.strftime('%B %d, %Y')}, 
                    subscribe to our monthly ($99/mo) or annual ($950/yr) plan.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://virginia-contracts-lead-generation.onrender.com/subscription" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; padding: 15px 40px; text-decoration: none; 
                              border-radius: 25px; font-weight: bold; display: inline-block;">
                        🚀 Subscribe Now
                    </a>
                </div>
                
                <p style="color: #888; font-size: 14px; margin-top: 30px;">
                    Thank you for being an early adopter and helping us improve ContractLink.ai!
                </p>
            </div>
            
            <div style="background-color: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0;">ContractLink.ai - Where Virginia's Contractors Win</p>
                <p style="margin: 10px 0 0 0; font-size: 12px; color: #999;">
                    You're receiving this because you're a Beta Tester member
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Sent renewal reminder to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending reminder to {email}: {e}")
        return False

def check_and_send_reminders():
    """Check for beta testers expiring in 30 days and send reminders"""
    with app.app_context():
        try:
            # Get beta testers expiring in 30 days (± 1 day window)
            today = datetime.utcnow()
            target_date = today + timedelta(days=30)
            date_min = target_date - timedelta(days=1)
            date_max = target_date + timedelta(days=1)
            
            query = text("""
                SELECT email, contact_name, beta_expiry_date 
                FROM leads 
                WHERE (is_beta_tester = TRUE OR is_beta_tester = 1)
                AND beta_expiry_date BETWEEN :date_min AND :date_max
                AND subscription_status != 'paid'
            """)
            
            results = db.session.execute(query, {
                'date_min': date_min,
                'date_max': date_max
            }).fetchall()
            
            print(f"\n🔍 Found {len(results)} beta testers with 30 days remaining")
            
            for row in results:
                email = row[0]
                contact_name = row[1]
                expiry_date = row[2]
                
                if isinstance(expiry_date, str):
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                    except:
                        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S')
                
                days_remaining = (expiry_date - today).days
                send_renewal_reminder(email, contact_name, days_remaining, expiry_date)
            
            print(f"\n✅ Completed renewal reminder check")
            
        except Exception as e:
            print(f"❌ Error in renewal reminder script: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_and_send_reminders()
