from app import app, db
from sqlalchemy import text

with app.app_context():
    result = db.session.execute(text("""
        SELECT company_name, city, state, data_source 
        FROM aviation_cleaning_leads 
        ORDER BY id
    """)).fetchall()
    
    print(f"\n✈️  Current aviation leads in database: {len(result)}")
    for i, row in enumerate(result, 1):
        print(f"{i}. {row[0]} - {row[1]}, {row[2]} (Source: {row[3]})")
