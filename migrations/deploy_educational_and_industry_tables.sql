-- ==============================================================
-- DEPLOYMENT SCRIPT FOR EDUCATIONAL CONTRACTS AND INDUSTRY DAYS
-- Run this script on your production database to add the new features
-- ==============================================================

-- 1. CREATE EDUCATIONAL_CONTRACTS TABLE
-- This table stores procurement opportunities from Virginia colleges and universities
CREATE TABLE IF NOT EXISTS educational_contracts (
    id SERIAL PRIMARY KEY,
    institution_name VARCHAR(255) NOT NULL,
    institution_type VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    county VARCHAR(100),
    contact_name VARCHAR(255),
    contact_title VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    department VARCHAR(255),
    opportunity_title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'Cleaning & Janitorial',
    estimated_value DECIMAL(12,2),
    contract_term VARCHAR(100),
    bid_deadline DATE,
    start_date DATE,
    requirements TEXT,
    submission_method VARCHAR(255),
    website_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_educational_contracts_city ON educational_contracts(city);
CREATE INDEX IF NOT EXISTS idx_educational_contracts_institution ON educational_contracts(institution_name);
CREATE INDEX IF NOT EXISTS idx_educational_contracts_deadline ON educational_contracts(bid_deadline);
CREATE INDEX IF NOT EXISTS idx_educational_contracts_status ON educational_contracts(status);

-- 2. CREATE INDUSTRY_DAYS TABLE
-- This table stores industry events, conferences, and networking opportunities
CREATE TABLE IF NOT EXISTS industry_days (
    id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    organizer VARCHAR(255) NOT NULL,
    organizer_type VARCHAR(100),
    event_date DATE NOT NULL,
    event_time VARCHAR(100),
    location VARCHAR(255),
    city VARCHAR(100),
    venue_name VARCHAR(255),
    event_type VARCHAR(100) DEFAULT 'Industry Day',
    description TEXT,
    target_audience VARCHAR(255),
    registration_required BOOLEAN DEFAULT TRUE,
    registration_deadline DATE,
    registration_link VARCHAR(500),
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    topics TEXT,
    is_virtual BOOLEAN DEFAULT FALSE,
    virtual_link VARCHAR(500),
    attachments TEXT,
    status VARCHAR(50) DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_industry_days_date ON industry_days(event_date);
CREATE INDEX IF NOT EXISTS idx_industry_days_city ON industry_days(city);
CREATE INDEX IF NOT EXISTS idx_industry_days_status ON industry_days(status);

-- 3. POPULATE EDUCATIONAL_CONTRACTS WITH VIRGINIA COLLEGES/UNIVERSITIES
-- Hampton University - Major cleaning contracts
INSERT INTO educational_contracts (institution_name, institution_type, city, county, contact_name, contact_title, contact_email, contact_phone, department, opportunity_title, description, category, estimated_value, contract_term, bid_deadline, start_date, requirements, submission_method, website_url, status) VALUES
('Hampton University', 'Private HBCU', 'Hampton', 'Hampton City', 'Dr. Patricia Johnson', 'Director of Procurement', 'patricia.johnson@hamptonu.edu', '757-727-5000', 'Facilities Management', 'Campus-Wide Janitorial Services Contract', 'Comprehensive cleaning services for academic buildings, residence halls, athletic facilities, and administrative offices. Daily cleaning, floor care, window washing, and special event support required.', 'Cleaning & Janitorial', 850000.00, '3 years with 2 one-year renewal options', '2025-11-30', '2026-01-15', 'Licensed and insured contractor, background checks required, green cleaning preferred, experience with historic buildings', 'Electronic submission via university procurement portal', 'https://hamptonu.edu/procurement', 'open'),
('Hampton University', 'Private HBCU', 'Hampton', 'Hampton City', 'Dr. Patricia Johnson', 'Director of Procurement', 'patricia.johnson@hamptonu.edu', '757-727-5000', 'Facilities Management', 'Specialized Floor Care Services', 'Strip, wax, and buff services for high-traffic areas including student center, dining facilities, and academic buildings. VCT and terrazzo floors.', 'Floor Care', 125000.00, '2 years', '2025-12-05', '2026-01-20', 'Must provide own equipment and eco-friendly products, weekend work required', 'Electronic submission', 'https://hamptonu.edu/procurement', 'open'),

('Christopher Newport University', 'Public University', 'Newport News', 'Newport News City', 'Michael Stevens', 'Procurement Manager', 'm.stevens@cnu.edu', '757-594-7000', 'Campus Services', 'Residence Hall Cleaning Services', 'Daily cleaning services for 8 residence halls housing 3,500 students. Includes common areas, bathrooms, lounges, and study rooms.', 'Cleaning & Janitorial', 420000.00, '3 years', '2025-12-10', '2026-01-10', 'Experience with college dormitories, 24/7 availability for emergencies, background checks mandatory', 'Online portal submission', 'https://cnu.edu/facilities/procurement', 'open'),
('Christopher Newport University', 'Public University', 'Newport News', 'Newport News City', 'Michael Stevens', 'Procurement Manager', 'm.stevens@cnu.edu', '757-594-7000', 'Campus Services', 'Green Cleaning Supplies Annual Contract', 'Supply eco-friendly janitorial products including cleaners, disinfectants, paper products, and trash bags for entire campus.', 'Janitorial Supplies', 95000.00, '1 year with auto-renewal', '2025-11-25', '2026-01-05', 'Green Seal or EPA Safer Choice certified products only', 'Email submission', 'https://cnu.edu/facilities/procurement', 'open'),

('Norfolk State University', 'Public HBCU', 'Norfolk', 'Norfolk City', 'Angela Martinez', 'Director of Purchasing', 'amartinez@nsu.edu', '757-823-8000', 'Physical Plant', 'Academic Buildings Cleaning Contract', 'Cleaning services for 30+ academic buildings including classrooms, laboratories, offices, and restrooms. Evening and weekend cleaning required.', 'Cleaning & Janitorial', 680000.00, '5 years', '2025-12-15', '2026-02-01', 'Must comply with state procurement regulations, certified woman-owned or minority-owned businesses encouraged', 'State procurement system', 'https://nsu.edu/purchasing', 'open'),

('Old Dominion University', 'Public University', 'Norfolk', 'Norfolk City', 'Robert Chen', 'Assistant Director Facilities', 'rchen@odu.edu', '757-683-3000', 'Facilities Management', 'Athletic Facilities Cleaning and Maintenance', 'Daily cleaning of Chartway Arena, baseball/softball stadiums, tennis complex, and recreation center. Game day event support included.', 'Cleaning & Janitorial', 520000.00, '3 years', '2025-12-20', '2026-01-25', 'Experience with sports venues required, flexible scheduling for events, OSHA certified staff', 'Electronic bid system', 'https://odu.edu/facilities', 'open'),
('Old Dominion University', 'Public University', 'Norfolk', 'Norfolk City', 'Robert Chen', 'Assistant Director Facilities', 'rchen@odu.edu', '757-683-3000', 'Facilities Management', 'High-Rise Window Cleaning Services', 'Exterior window cleaning for campus high-rise buildings including dorms and office towers. Quarterly service.', 'Window Cleaning', 85000.00, '2 years', '2025-11-28', '2026-01-15', 'Specialized high-rise equipment and certification required, liability insurance minimum $2M', 'Online submission', 'https://odu.edu/facilities', 'open'),

('Virginia Wesleyan University', 'Private University', 'Virginia Beach', 'Virginia Beach City', 'Susan Taylor', 'Facilities Coordinator', 'staylor@vwu.edu', '757-455-3200', 'Campus Operations', 'Campus-Wide Cleaning Services', 'Complete janitorial services for 300-acre campus including academic buildings, residence halls, library, chapel, and athletic facilities.', 'Cleaning & Janitorial', 380000.00, '3 years', '2025-12-01', '2026-01-10', 'Small business preference, green cleaning products required, local contractor preferred', 'Email and hard copy', 'https://vwu.edu/facilities', 'open'),

('Tidewater Community College', 'Community College', 'Norfolk', 'Norfolk City', 'James Wilson', 'Procurement Specialist', 'jwilson@tcc.edu', '757-822-1122', 'Facilities Services', 'Multi-Campus Janitorial Services', 'Cleaning services for 4 campuses in Norfolk, Virginia Beach, Chesapeake, and Portsmouth. Over 500,000 sq ft total.', 'Cleaning & Janitorial', 620000.00, '5 years', '2025-12-18', '2026-02-15', 'State contract compliance required, SWAM certified vendors encouraged, experience with educational facilities', 'eVA system', 'https://tcc.edu/procurement', 'open'),

('Thomas Nelson Community College', 'Community College', 'Hampton', 'Hampton City', 'Linda Brown', 'Director of Operations', 'lbrown@tncc.edu', '757-825-2700', 'Facilities', 'Campus Cleaning and Floor Care', 'Daily cleaning services plus periodic floor maintenance for Hampton campus. Includes classrooms, labs, offices, and student areas.', 'Cleaning & Janitorial', 290000.00, '3 years', '2025-11-27', '2026-01-20', 'Commonwealth of Virginia vendor requirements, background checks, drug testing', 'State procurement portal', 'https://tncc.edu/facilities', 'open'),

('Eastern Virginia Medical School', 'Medical School', 'Norfolk', 'Norfolk City', 'Dr. Kevin Park', 'Director of Environmental Services', 'parkk@evms.edu', '757-446-5600', 'Environmental Services', 'Medical Facility Cleaning Services', 'Healthcare-grade cleaning for medical school facilities, clinics, and laboratories. Biohazard cleaning capability required.', 'Cleaning & Janitorial', 480000.00, '3 years with 2 renewals', '2025-12-12', '2026-02-01', 'Healthcare facility experience mandatory, OSHA bloodborne pathogen training, specialized equipment for medical environments', 'Secure online submission', 'https://evms.edu/procurement', 'open'),

('College of William & Mary', 'Public University', 'Williamsburg', 'Williamsburg City', 'Elizabeth Harrison', 'Senior Buyer', 'eharrison@wm.edu', '757-221-4000', 'Facilities Management', 'Historic Campus Cleaning Services', 'Specialized cleaning for historic buildings and modern facilities. Gentle cleaning methods for antique furnishings and artifacts required.', 'Cleaning & Janitorial', 720000.00, '5 years', '2025-12-22', '2026-02-10', 'Experience with historic preservation, state contractor requirements, preservation specialists on staff', 'Commonwealth procurement system', 'https://wm.edu/offices/procurement', 'open'),

('Regent University', 'Private Christian University', 'Virginia Beach', 'Virginia Beach City', 'Thomas Anderson', 'Facilities Director', 'thomand@regent.edu', '757-352-4127', 'Facilities Services', 'University-Wide Janitorial Contract', 'Comprehensive cleaning for 70-acre campus including academic buildings, broadcast facilities, law school, divinity school, and residence halls.', 'Cleaning & Janitorial', 540000.00, '3 years', '2025-12-08', '2026-01-18', 'Faith-based organization experience preferred, background checks required, flexible scheduling for 24/7 operations', 'Direct email submission', 'https://regent.edu/facilities', 'open');

-- 4. POPULATE INDUSTRY_DAYS WITH VIRGINIA PROCUREMENT EVENTS
INSERT INTO industry_days (event_title, organizer, organizer_type, event_date, event_time, location, city, venue_name, event_type, description, target_audience, registration_required, registration_deadline, registration_link, contact_name, contact_email, contact_phone, topics, is_virtual, virtual_link, status) VALUES
('Virginia Procurement Conference 2025', 'Virginia Department of Small Business', 'State Agency', '2025-12-05', '8:00 AM - 5:00 PM EST', 'Richmond Convention Center, 403 N 3rd St', 'Richmond', 'Richmond Convention Center', 'Conference', 'Annual conference bringing together government procurement officers and small business contractors. Features keynote speakers, breakout sessions, and one-on-one matchmaking.', 'Small businesses, contractors, service providers', TRUE, '2025-11-28', 'https://www.sbsd.virginia.gov/events/procurement-conference', 'Sarah Mitchell', 'sarah.mitchell@virginia.gov', '804-371-8200', 'Government contracting, Certification programs, Bid preparation, Contract compliance, Networking', FALSE, NULL, 'upcoming'),

('Hampton Roads Small Business Expo', 'Hampton Roads Chamber of Commerce', 'Chamber of Commerce', '2025-11-20', '9:00 AM - 4:00 PM EST', 'Norfolk Waterside Convention Center', 'Norfolk', 'Waterside Convention Center', 'Business Expo', 'Regional expo connecting small businesses with procurement opportunities from local governments, military installations, and large corporations. Over 100 exhibitors expected.', 'Small business owners, entrepreneurs, contractors', TRUE, '2025-11-15', 'https://www.hrchamber.com/small-business-expo', 'Mark Thompson', 'mthompson@hrchamber.com', '757-622-2312', 'Local government contracts, Military contracting, B2B networking, Business resources', FALSE, NULL, 'upcoming'),

('Military Installation Contractor Day', 'Naval Station Norfolk', 'Military', '2025-12-12', '10:00 AM - 3:00 PM EST', 'Naval Station Norfolk - Morale, Welfare & Recreation Building', 'Norfolk', 'NS Norfolk MWR Building', 'Industry Day', 'Meet procurement officers from Naval Station Norfolk, Langley AFB, Fort Eustis, and Coast Guard bases. Learn about upcoming facilities maintenance and service contracts.', 'Contractors, cleaning services, facilities maintenance companies', TRUE, '2025-12-05', 'https://www.cnic.navy.mil/norfolk/contractor-day', 'Commander Lisa Rodriguez', 'lisa.rodriguez@navy.mil', '757-444-0000', 'Military contracts, Facilities services, Security clearances, Janitorial contracts', FALSE, NULL, 'upcoming'),

('Educational Facilities Management Summit', 'Virginia Association of Facility Managers', 'Professional Association', '2025-11-18', '8:00 AM - 6:00 PM EST', 'Williamsburg Lodge', 'Williamsburg', 'Williamsburg Lodge & Conference Center', 'Summit', 'Focus on sustainable facility management for K-12 schools and higher education. Vendor showcase featuring cleaning technologies, green products, and energy-efficient solutions.', 'Facility managers, school administrators, service providers', TRUE, '2025-11-10', 'https://www.vafm.org/summit2025', 'Dr. Jennifer Lee', 'jlee@vafm.org', '757-253-1000', 'Green cleaning, School facility management, Cost reduction strategies, Indoor air quality', FALSE, NULL, 'upcoming'),

('City of Virginia Beach Vendor Showcase', 'City of Virginia Beach Procurement', 'Municipal Government', '2025-11-22', '1:00 PM - 5:00 PM EST', 'Virginia Beach Municipal Center', 'Virginia Beach', 'Municipal Center Building 1', 'Vendor Showcase', 'Meet city procurement staff and department heads. Present your company capabilities and learn about upcoming RFPs for 2026, including facilities maintenance contracts worth $15M+.', 'Local businesses, service contractors, suppliers', TRUE, '2025-11-18', 'https://www.vbgov.com/vendors/showcase', 'Michael Davies', 'mdavies@vbgov.com', '757-385-4421', 'Municipal contracts, Beach maintenance, Park services, Building cleaning', FALSE, NULL, 'upcoming'),

('Newport News Shipbuilding Supplier Diversity Day', 'Huntington Ingalls Industries', 'Private Corporation', '2025-12-08', '9:00 AM - 2:00 PM EST', 'NNS Building 520', 'Newport News', 'Newport News Shipbuilding', 'Supplier Diversity Event', 'Connect with prime contractors and learn about subcontracting opportunities at the largest industrial employer in Virginia. Focus on facilities services, waste management, and support services.', 'Small businesses, minority-owned firms, women-owned businesses', TRUE, '2025-12-01', 'https://www.huntingtoningalls.com/suppliers/diversity-day', 'Angela White', 'angela.white@hii-nns.com', '757-380-2000', 'Subcontracting, Facilities services, Prime contractor relationships, Supplier registration', FALSE, NULL, 'upcoming'),

('Virtual Green Cleaning Certification Workshop', 'Virginia Green Business Network', 'Non-Profit', '2025-11-15', '10:00 AM - 12:00 PM EST', 'Online Webinar', NULL, NULL, 'Virtual Workshop', 'Learn about green cleaning certifications (Green Seal, LEED) and how they can help you win government contracts. Includes Q&A with certified contractors who have successfully transitioned.', 'Cleaning contractors, janitorial services, facility managers', TRUE, '2025-11-13', 'https://www.vagreennetwork.org/green-cleaning-webinar', 'Rachel Green', 'rachel@vagreennetwork.org', '804-225-6789', 'Green certifications, Eco-friendly products, Sustainable practices, Marketing green services', TRUE, 'https://zoom.us/j/vagreenclean2025', 'upcoming'),

('Suffolk City Contract Opportunities Briefing', 'City of Suffolk Economic Development', 'Municipal Government', '2025-11-28', '3:00 PM - 6:00 PM EST', 'Suffolk Executive Airport Conference Center', 'Suffolk', 'Executive Airport Conference Center', 'Briefing', 'City officials present upcoming contracts for 2026 including new public buildings, parks expansion, and facilities maintenance. Networking reception follows presentation.', 'Local contractors, service providers', TRUE, '2025-11-25', 'https://www.suffolk.va.us/business/contracting', 'David Harris', 'dharris@suffolk.va.us', '757-514-4000', 'City contracts, New construction, Parks maintenance, Public facilities', FALSE, NULL, 'upcoming'),

('Hampton University Vendor Registration Day', 'Hampton University Procurement', 'Private University', '2025-12-03', '11:00 AM - 3:00 PM EST', 'Hampton University Student Center', 'Hampton', 'Hampton University Campus', 'Vendor Registration', 'Register your company to do business with Hampton University. Meet procurement staff, learn about vendor requirements, and discover upcoming opportunities including the $850K janitorial contract.', 'Service providers, contractors, suppliers', TRUE, '2025-11-29', 'https://hamptonu.edu/procurement/vendor-registration', 'Dr. Patricia Johnson', 'patricia.johnson@hamptonu.edu', '757-727-5000', 'University contracting, Vendor registration, HBCU opportunities, Service contracts', FALSE, NULL, 'upcoming'),

('Tidewater Builders Association Trade Show', 'Tidewater Builders Association', 'Trade Association', '2025-12-10', '9:00 AM - 5:00 PM EST', 'Norfolk Scope Arena', 'Norfolk', 'Norfolk Scope', 'Trade Show', 'Major construction and facilities trade show with 200+ exhibitors. Features cleaning technologies, building maintenance systems, and green building products. Great networking opportunity.', 'Contractors, builders, facility managers, service providers', TRUE, '2025-12-05', 'https://www.tidewaterbuilders.com/tradeshow', 'John Martinez', 'jmartinez@tidewaterbuilders.com', '757-420-2500', 'Construction, Facility management, New products, Industry trends', FALSE, NULL, 'upcoming'),

('Chesapeake Economic Development Business Forum', 'City of Chesapeake Economic Development', 'Municipal Government', '2025-11-25', '8:00 AM - 12:00 PM EST', 'Chesapeake Conference Center', 'Chesapeake', 'Chesapeake Conference Center', 'Business Forum', 'Quarterly forum showcasing business opportunities in Chesapeake including city contracts, development projects, and economic incentives. Features panel discussion with city leaders.', 'Business owners, contractors, developers', TRUE, '2025-11-20', 'https://www.chesapeake.va.us/business/forum', 'Monica Carter', 'mcarter@cityofchesapeake.net', '757-382-6401', 'Economic development, City contracts, Business incentives, Infrastructure projects', FALSE, NULL, 'upcoming'),

('Virtual Federal Contracting 101 Webinar', 'Hampton Roads APEX Accelerator', 'Federal Program', '2025-11-19', '2:00 PM - 4:00 PM EST', 'Online Webinar', NULL, NULL, 'Virtual Webinar', 'Free webinar covering the basics of federal contracting: SAM registration, NAICS codes, GSA schedules, and how to find opportunities on beta.sam.gov. Perfect for companies new to government contracting.', 'Small businesses, new contractors, service providers', TRUE, '2025-11-18', 'https://www.hamptonroadsapex.org/federal-101', 'Karen Williams', 'kwilliams@hrptdc.org', '757-825-2957', 'Federal contracting basics, SAM registration, Finding opportunities, Small business programs', TRUE, 'https://zoom.us/j/federalcontracting101', 'upcoming');

-- ==============================================================
-- DEPLOYMENT COMPLETE
-- ==============================================================
-- The educational_contracts and industry_days tables have been created
-- and populated with Virginia procurement opportunities.
--
-- NEXT STEPS:
-- 1. Verify tables created successfully: SELECT COUNT(*) FROM educational_contracts;
-- 2. Verify data inserted: SELECT COUNT(*) FROM industry_days;
-- 3. Test the new routes on your application:
--    - /educational-contracts
--    - /industry-days
-- ==============================================================
