"""
Notifications Blueprint for VA Contracts Lead Generation Platform
Flask routes for sending email notifications and daily briefings
"""

from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from email_service import send_email
import email_templates

notifications = Blueprint("notifications", __name__)

@notifications.route("/notifications/send-test")
@login_required
def send_test():
    """
    Send a test notification email to the current user
    Requires authentication to prevent spam
    
    Returns:
        JSON response with status
    """
    user_email = current_user.email
    
    if not user_email:
        return jsonify({
            "status": "error",
            "message": "No email address found for current user"
        }), 400
    
    success = send_email(
        to=user_email,
        subject="✅ Test Notification from ContractLink.ai",
        html=email_templates.test_notification()
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Test email sent to {user_email}"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to send test email. Check server logs."
        }), 500

@notifications.route("/notifications/daily")
@login_required
def send_daily():
    """
    Send daily briefing email to the current user
    Fetches recent leads from the database
    
    Returns:
        JSON response with status
    """
    from database import get_db
    
    user_email = current_user.email
    
    if not user_email:
        return jsonify({
            "status": "error",
            "message": "No email address found for current user"
        }), 400
    
    # Fetch recent leads from the database
    db = get_db()
    cursor = db.cursor()
    
    # Get leads from last 24 hours
    cursor.execute("""
        SELECT title, state, estimated_value, deadline, description
        FROM federal_contracts
        WHERE created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    # Format leads for email template
    leads = []
    for row in rows:
        leads.append({
            'project': row[0] or 'Unnamed Project',
            'state': row[1] or 'N/A',
            'value': f"${row[2]:,.0f}" if row[2] else 'N/A',
            'deadline': row[3] or 'N/A',
            'description': row[4] or 'No description available.'
        })
    
    success = send_email(
        to=user_email,
        subject=f"📊 Daily Briefing: {len(leads)} New Lead{'s' if len(leads) != 1 else ''}",
        html=email_templates.daily_briefing(leads)
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Daily briefing sent to {user_email}",
            "leads_count": len(leads)
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to send daily briefing. Check server logs."
        }), 500

@notifications.route("/notifications/new-lead/<int:lead_id>")
@login_required
def send_new_lead_alert(lead_id):
    """
    Send real-time alert for a specific new lead
    
    Args:
        lead_id: ID of the lead in federal_contracts table
        
    Returns:
        JSON response with status
    """
    from database import get_db
    
    user_email = current_user.email
    
    if not user_email:
        return jsonify({
            "status": "error",
            "message": "No email address found for current user"
        }), 400
    
    # Fetch lead details from database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT title, state, estimated_value, deadline, description
        FROM federal_contracts
        WHERE id = ?
    """, (lead_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return jsonify({
            "status": "error",
            "message": f"Lead {lead_id} not found"
        }), 404
    
    # Format lead for email template
    lead = {
        'project': row[0] or 'Unnamed Project',
        'state': row[1] or 'N/A',
        'value': f"${row[2]:,.0f}" if row[2] else 'N/A',
        'deadline': row[3] or 'N/A',
        'description': row[4] or 'No description available.'
    }
    
    success = send_email(
        to=user_email,
        subject=f"🔔 New Lead Alert: {lead['project']}",
        html=email_templates.new_lead_alert(lead)
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"New lead alert sent to {user_email}",
            "lead": lead
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to send new lead alert. Check server logs."
        }), 500

@notifications.route("/notifications/test-admin")
def send_test_admin():
    """
    Admin-only test endpoint without authentication (for Render testing)
    Use query parameter: ?email=your@email.com
    
    Returns:
        JSON response with status
    """
    test_email = request.args.get('email')
    
    if not test_email:
        return jsonify({
            "status": "error",
            "message": "Missing 'email' query parameter. Use: /notifications/test-admin?email=your@email.com"
        }), 400
    
    success = send_email(
        to=test_email,
        subject="✅ Admin Test Notification from ContractLink.ai",
        html=email_templates.test_notification()
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Test email sent to {test_email}"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to send test email. Check EMAIL_USER and EMAIL_PASS environment variables."
        }), 500
