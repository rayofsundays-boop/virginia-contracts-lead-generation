"""
Email Templates for VA Contracts Lead Generation Platform
HTML email templates for notifications and briefings
"""

def test_notification():
    """
    Simple test notification to verify email system is working
    
    Returns:
        str: HTML content for test email
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            h2 { color: #4F46E5; border-bottom: 3px solid #4F46E5; padding-bottom: 10px; }
            .success { background: #10b981; color: white; padding: 15px; border-radius: 8px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🚀 VA Contracts Lead Gen – Test Notification</h2>
            <div class="success">
                <p style="margin: 0; font-size: 18px;">✅ This is a successful test alert notification! 🎉</p>
            </div>
            <p>Your email notification system is configured correctly and working as expected.</p>
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Daily briefings will be sent automatically at 8 AM EST</li>
                <li>New lead notifications will arrive in real-time</li>
                <li>All emails are sent securely via SSL/TLS encryption</li>
            </ul>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="font-size: 12px; color: #6b7280;">
                ContractLink.ai | Virginia Contracts Lead Generation Platform<br>
                <a href="https://contractlink.ai" style="color: #4F46E5;">Visit Dashboard</a>
            </p>
        </div>
    </body>
    </html>
    """

def daily_briefing(leads):
    """
    Daily briefing email with new leads summary
    
    Args:
        leads (list): List of lead dictionaries with 'project', 'state', 'value', 'deadline' keys
        
    Returns:
        str: HTML content for daily briefing email
    """
    if not leads:
        leads_html = "<p style='color: #6b7280;'><em>No new leads today. Check back tomorrow!</em></p>"
    else:
        items = []
        for lead in leads:
            project = lead.get('project', 'N/A')
            state = lead.get('state', 'N/A')
            value = lead.get('value', 'N/A')
            deadline = lead.get('deadline', 'N/A')
            
            items.append(f"""
            <li style="margin-bottom: 15px; padding: 15px; background: #f9fafb; border-left: 4px solid #4F46E5; border-radius: 4px;">
                <strong style="color: #1a202c; font-size: 16px;">{project}</strong><br>
                <span style="color: #4a5568; font-size: 14px;">📍 {state} | 💰 {value} | ⏰ Deadline: {deadline}</span>
            </li>
            """)
        
        leads_html = f"<ul style='list-style: none; padding: 0;'>{''.join(items)}</ul>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f3f4f6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: white; border-radius: 8px; }}
            h2 {{ color: #4F46E5; border-bottom: 3px solid #4F46E5; padding-bottom: 10px; }}
            .summary {{ background: #ede9fe; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .summary strong {{ color: #4F46E5; font-size: 24px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Your Daily Lead Briefing</h2>
            <div class="summary">
                <p style="margin: 0;">You have <strong>{len(leads)}</strong> new lead{'s' if len(leads) != 1 else ''} today.</p>
            </div>
            
            <h3 style="color: #1a202c;">🎯 Today's Opportunities</h3>
            {leads_html}
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="font-size: 12px; color: #6b7280;">
                ContractLink.ai | Virginia Contracts Lead Generation Platform<br>
                <a href="https://contractlink.ai/contracts" style="color: #4F46E5;">View All Leads</a> | 
                <a href="https://contractlink.ai/profile" style="color: #4F46E5;">Manage Preferences</a>
            </p>
        </div>
    </body>
    </html>
    """

def new_lead_alert(lead):
    """
    Real-time notification for a single new lead
    
    Args:
        lead (dict): Lead dictionary with 'project', 'state', 'value', 'deadline', 'description' keys
        
    Returns:
        str: HTML content for new lead alert email
    """
    project = lead.get('project', 'N/A')
    state = lead.get('state', 'N/A')
    value = lead.get('value', 'N/A')
    deadline = lead.get('deadline', 'N/A')
    description = lead.get('description', 'No description available.')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h2 {{ color: #4F46E5; border-bottom: 3px solid #4F46E5; padding-bottom: 10px; }}
            .alert {{ background: #fef3c7; border-left: 5px solid #f59e0b; padding: 15px; border-radius: 4px; }}
            .details {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .cta {{ display: inline-block; background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="alert">
                <p style="margin: 0; font-size: 16px;"><strong>🔔 New Lead Alert!</strong></p>
            </div>
            
            <h2>🎯 {project}</h2>
            
            <div class="details">
                <p><strong>Location:</strong> 📍 {state}</p>
                <p><strong>Estimated Value:</strong> 💰 {value}</p>
                <p><strong>Deadline:</strong> ⏰ {deadline}</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 15px 0;">
                <p><strong>Description:</strong></p>
                <p style="color: #4a5568;">{description}</p>
            </div>
            
            <a href="https://contractlink.ai/contracts" class="cta">View Full Details →</a>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="font-size: 12px; color: #6b7280;">
                ContractLink.ai | Virginia Contracts Lead Generation Platform<br>
                <a href="https://contractlink.ai/profile" style="color: #4F46E5;">Manage Email Preferences</a>
            </p>
        </div>
    </body>
    </html>
    """
