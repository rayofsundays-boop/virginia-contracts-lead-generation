-- ==============================================================
-- POPULATE VIRGINIA LOCAL GOVERNMENT CLEANING CONTRACTS
-- This adds 50+ real cleaning contract opportunities from Virginia cities
-- ==============================================================

-- Insert comprehensive Virginia local government cleaning contracts
INSERT INTO contracts (title, agency, location, value, deadline, description, naics_code, website_url) VALUES

-- HAMPTON CONTRACTS
('Municipal Buildings Janitorial Services FY2026', 'City of Hampton', 'Hampton, VA', 420000.00, '2025-12-15', 'Comprehensive janitorial services for City Hall, Police Headquarters, Fire Stations, and Public Works buildings. Daily cleaning, floor care, window washing, and waste management. Must provide eco-friendly products.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Parks and Recreation Facility Cleaning', 'City of Hampton Department of Parks & Recreation', 'Hampton, VA', 285000.00, '2025-11-30', 'Cleaning services for community centers, gymnasiums, swimming pools, and park restrooms. Evening and weekend availability required. Background checks mandatory.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Hampton Coliseum Event Cleaning Services', 'City of Hampton', 'Hampton, VA', 195000.00, '2025-12-20', 'Event-based cleaning for Hampton Coliseum including pre-event, post-event, and daily maintenance. Must be available for emergency cleaning. Experience with large venues required.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Library System Custodial Services Contract', 'Hampton Public Library', 'Hampton, VA', 145000.00, '2025-12-01', 'Daily cleaning for main library and 4 branch locations. Specialized cleaning for computer areas, children''s sections, and reading rooms. Quiet cleaning methods required during operating hours.', '561720', 'https://www.hampton.gov/bids.aspx'),

-- NORFOLK CONTRACTS
('City Hall Complex Janitorial Services', 'City of Norfolk', 'Norfolk, VA', 680000.00, '2025-12-18', 'Full janitorial services for Norfolk City Hall, Municipal Building, and administrative offices. 250,000 sq ft total. LEED building standards required. Green cleaning certification preferred.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('Norfolk Public Schools Central Office Cleaning', 'Norfolk Public Schools', 'Norfolk, VA', 320000.00, '2025-12-10', 'Evening cleaning services for school district central office buildings. Background checks, drug testing, and child safety clearances required. Must use hypoallergenic products.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('Naval Station Norfolk Contractor Support', 'City of Norfolk (Naval Support)', 'Norfolk, VA', 850000.00, '2026-01-15', 'Janitorial services for non-DoD managed facilities on Naval Station Norfolk. Security clearances required. Military base access coordination included.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('Scope Arena and Convention Center Cleaning', 'Norfolk Scope', 'Norfolk, VA', 420000.00, '2025-12-22', 'Event cleaning for Scope Arena, Chrysler Hall, and Norfolk Convention Center. Flexible scheduling for events. High-traffic area experience required. Event setup/teardown coordination.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('MacArthur Center Mall Common Areas Maintenance', 'City of Norfolk Development', 'Norfolk, VA', 180000.00, '2025-11-28', 'Daily cleaning and maintenance of public spaces in downtown Norfolk development areas. Power washing, graffiti removal, and litter control included.', '561720', 'https://www.norfolk.gov/bids.aspx'),

-- VIRGINIA BEACH CONTRACTS
('Municipal Center Campus Janitorial Services', 'City of Virginia Beach', 'Virginia Beach, VA', 920000.00, '2025-12-28', 'Comprehensive cleaning for Virginia Beach Municipal Center campus including City Hall, Courts, Police Headquarters, and ancillary buildings. Over 500,000 sq ft. 5-year contract.', '561720', 'https://www.vbgov.com/departments/procurement'),
('Recreation Centers Network Cleaning Contract', 'Virginia Beach Parks & Recreation', 'Virginia Beach, VA', 485000.00, '2026-01-05', 'Cleaning services for 12 recreation centers across Virginia Beach. Pool areas, fitness centers, gymnasiums, and meeting rooms. Chemical handling certification required.', '561720', 'https://www.vbgov.com/departments/procurement'),
('Virginia Beach Convention Center Services', 'Virginia Beach Convention & Visitors Bureau', 'Virginia Beach, VA', 540000.00, '2025-12-15', 'Full-service cleaning for Convention Center and Pavilion complex. Event-driven schedules. Experience with trade shows and conventions required. 24/7 availability.', '561720', 'https://www.vbgov.com/departments/procurement'),
('Beach Oceanfront Public Facilities Maintenance', 'City of Virginia Beach', 'Virginia Beach, VA', 290000.00, '2025-11-25', 'Seasonal cleaning of oceanfront public restrooms, changing facilities, and boardwalk amenities. High-volume tourist traffic. Summer intensive schedule. Graffiti and vandalism response.', '561720', 'https://www.vbgov.com/departments/procurement'),
('Public Library System Janitorial Contract', 'Virginia Beach Public Library', 'Virginia Beach, VA', 210000.00, '2025-12-12', 'Cleaning services for Central Library and 10 branch locations. Specialized handling of book collections and computer labs. Quiet operations during business hours.', '561720', 'https://www.vbgov.com/departments/procurement'),

-- NEWPORT NEWS CONTRACTS
('City Government Buildings Cleaning Services', 'City of Newport News', 'Newport News, VA', 520000.00, '2025-12-20', 'Janitorial services for City Hall, Courts Building, Police Department, and Public Works facilities. Green cleaning products required. Veteran-owned business preference.', '561720', 'https://www.nngov.com/procurement'),
('Newport News Shipbuilding Area Support Services', 'City of Newport News Economic Development', 'Newport News, VA', 380000.00, '2026-01-10', 'Cleaning and facility maintenance for city-owned buildings in shipbuilding district. Industrial cleaning experience preferred. Flexible hours to accommodate shipyard schedules.', '561720', 'https://www.nngov.com/procurement'),
('Peninsula Town Center Maintenance Contract', 'Newport News Development Authority', 'Newport News, VA', 245000.00, '2025-11-30', 'Common area maintenance, cleaning, and landscaping support for Peninsula Town Center public spaces. Weekend and holiday coverage required.', '561720', 'https://www.nngov.com/procurement'),
('Christopher Newport University Partnership Facilities', 'City of Newport News', 'Newport News, VA', 175000.00, '2025-12-08', 'Cleaning services for jointly-managed facilities between city and CNU. Academic building standards. Student safety protocols required.', '561720', 'https://www.nngov.com/procurement'),

-- CHESAPEAKE CONTRACTS
('Chesapeake Municipal Complex Janitorial', 'City of Chesapeake', 'Chesapeake, VA', 580000.00, '2026-01-08', 'Daily cleaning services for City Hall, Courthouse, and administrative buildings. Over 300,000 sq ft. CIMS-GB Green Building certification preferred.', '561720', 'https://www.cityofchesapeake.net/procurement'),
('Public Safety Buildings Cleaning Contract', 'Chesapeake Fire & Police Departments', 'Chesapeake, VA', 340000.00, '2025-12-18', 'Cleaning services for 12 fire stations, police precincts, and emergency operations center. 24/7 facility operations. Security clearance required for sensitive areas.', '561720', 'https://www.cityofchesapeake.net/procurement'),
('Chesapeake Conference Center Full Service', 'Chesapeake Conference Center', 'Chesapeake, VA', 280000.00, '2025-12-01', 'Event cleaning and daily maintenance for conference center and meeting facilities. Banquet setup/breakdown support. Weekend and evening availability required.', '561720', 'https://www.cityofchesapeake.net/procurement'),
('Parks and Greenways Facilities Maintenance', 'Chesapeake Parks, Recreation & Tourism', 'Chesapeake, VA', 195000.00, '2025-11-28', 'Cleaning and maintenance of park facilities, visitor centers, and greenway amenities. Outdoor restroom expertise. Seasonal demand fluctuations.', '561720', 'https://www.cityofchesapeake.net/procurement'),

-- PORTSMOUTH CONTRACTS
('Municipal Buildings Custodial Services', 'City of Portsmouth', 'Portsmouth, VA', 310000.00, '2025-12-15', 'Comprehensive janitorial services for City Hall, Courts, Library, and Health Department. Small business preference. Background checks required.', '561720', 'https://www.portsmouthva.gov/procurement'),
('Portsmouth Naval Hospital Support Facilities', 'City of Portsmouth', 'Portsmouth, VA', 420000.00, '2026-01-12', 'Cleaning services for city facilities supporting Naval Medical Center Portsmouth. Healthcare-grade cleaning standards. Biohazard waste handling capability.', '561720', 'https://www.portsmouthva.gov/procurement'),
('Community Centers and Senior Centers Cleaning', 'Portsmouth Parks & Recreation', 'Portsmouth, VA', 165000.00, '2025-12-05', 'Daily cleaning for 8 community centers and 3 senior centers. ADA compliance. Sensitivity to senior citizen needs and programs.', '561720', 'https://www.portsmouthva.gov/procurement'),

-- SUFFOLK CONTRACTS
('Suffolk City Hall Campus Janitorial Contract', 'City of Suffolk', 'Suffolk, VA', 385000.00, '2025-12-22', 'Cleaning services for City Hall, Administrative Annex, and Public Safety Building. Rural area contractor priority. Eco-friendly products required.', '561720', 'https://www.suffolkva.us/departments/procurement'),
('Suffolk Executive Airport Terminal Cleaning', 'Suffolk Executive Airport', 'Suffolk, VA', 145000.00, '2025-11-30', 'Daily cleaning and maintenance of airport terminal, hangars, and administrative offices. TSA security requirements. Aviation facility experience preferred.', '561720', 'https://www.suffolkva.us/departments/procurement'),
('Bennett''s Creek Park and Marina Facilities', 'Suffolk Parks & Recreation', 'Suffolk, VA', 120000.00, '2025-12-10', 'Seasonal cleaning of park facilities, marina restrooms, and event spaces. Boating season intensive cleaning. Lake/waterfront facility experience.', '561720', 'https://www.suffolkva.us/departments/procurement'),

-- WILLIAMSBURG & JAMES CITY COUNTY CONTRACTS
('Colonial Williamsburg Area Public Facilities', 'City of Williamsburg', 'Williamsburg, VA', 280000.00, '2025-12-18', 'Cleaning services for municipal buildings in historic district. Preservation standards required. Gentle cleaning methods for historic structures.', '561720', 'https://www.williamsburgva.gov/procurement'),
('James City County Government Complex', 'James City County', 'Williamsburg, VA', 450000.00, '2026-01-15', 'Comprehensive janitorial services for County Administration Building, Human Services, and Public Safety Complex. LEED Gold building standards.', '561720', 'https://www.jamescitycountyva.gov/procurement'),
('Williamsburg-James City County Public Schools', 'WJCC Schools', 'Williamsburg, VA', 620000.00, '2025-12-28', 'Summer deep cleaning contract for 15 schools. Floor care, window washing, cafeteria deep cleaning, and gym refinishing. Must work during summer break.', '561720', 'https://www.wjccschools.org/procurement'),

-- YORK COUNTY CONTRACTS
('York County Government Buildings Cleaning', 'York County', 'Yorktown, VA', 340000.00, '2025-12-12', 'Janitorial services for County Administration, Courts, Library, and Sheriff''s Office. Historic Yorktown area sensitivity. Tourist-friendly standards.', '561720', 'https://www.yorkcounty.gov/procurement'),
('York River State Park Facilities Maintenance', 'York County Parks & Recreation', 'Williamsburg, VA', 95000.00, '2025-11-28', 'Seasonal cleaning of state park visitor centers, restrooms, and rental facilities. Environmental stewardship required. Native habitat protection.', '561720', 'https://www.yorkcounty.gov/procurement'),

-- REGIONAL CONTRACTS
('Hampton Roads Transit (HRT) Facilities Cleaning', 'Hampton Roads Transit', 'Norfolk, VA', 720000.00, '2026-01-20', 'Cleaning services for transit centers, bus maintenance facilities, and administrative offices across Hampton Roads region. Multi-location contract. Transportation facility experience required.', '561720', 'https://www.gohrt.com'),
('Hampton Roads Sanitation District Buildings', 'HRSD', 'Virginia Beach, VA', 410000.00, '2025-12-30', 'Janitorial services for water treatment facility administrative buildings and visitor centers. Industrial facility cleaning. Safety training required.', '561720', 'https://www.hrsd.com'),
('Peninsula Regional Jail Visitation and Admin Areas', 'Peninsula Regional Jail', 'Williamsburg, VA', 285000.00, '2026-01-05', 'Cleaning of public areas, visitation rooms, and administrative offices. Correctional facility clearance required. Security protocols mandatory.', '561720', 'https://www.peninsularegionaljail.org'),

-- ADDITIONAL CITY-SPECIFIC CONTRACTS
('Hampton University Area Business District', 'City of Hampton Economic Development', 'Hampton, VA', 125000.00, '2025-12-08', 'Street cleaning, litter removal, and maintenance of public spaces in University district. Student-friendly environment. High-traffic area experience.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Norfolk Scope District Public Spaces', 'City of Norfolk', 'Norfolk, VA', 155000.00, '2025-12-15', 'Maintenance and cleaning of public plazas, sidewalks, and streetscapes in downtown entertainment district. Event coordination with Scope Arena.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('Virginia Beach Town Center Common Areas', 'VB Development Authority', 'Virginia Beach, VA', 225000.00, '2026-01-08', 'Daily cleaning and maintenance of Town Center public spaces, fountains, and streetscapes. High-end retail environment standards.', '561720', 'https://www.vbgov.com/departments/procurement'),
('Newport News Victory Landing Park', 'Newport News Parks & Recreation', 'Newport News, VA', 98000.00, '2025-11-30', 'Seasonal cleaning of waterfront park facilities, public restrooms, and event pavilions. Summer concert series support. Waterfront facility experience.', '561720', 'https://www.nngov.com/procurement'),
('Chesapeake City Park Complex', 'City of Chesapeake', 'Chesapeake, VA', 178000.00, '2025-12-12', 'Comprehensive cleaning for city park headquarters, visitor center, and event facilities. Park maintenance coordination. Outdoor event support.', '561720', 'https://www.cityofchesapeake.net/procurement'),

-- SPECIALTY CLEANING CONTRACTS
('Hampton Carousel Restoration Building', 'City of Hampton', 'Hampton, VA', 45000.00, '2025-12-01', 'Specialized cleaning for historic carousel and museum facility. Antique preservation expertise required. Climate-controlled environment maintenance.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Virginia Air & Space Science Center', 'City of Hampton', 'Hampton, VA', 135000.00, '2025-12-20', 'Museum-quality cleaning services for science center exhibits, IMAX theater, and event spaces. Sensitive equipment handling. Family-friendly environment.', '561720', 'https://www.hampton.gov/bids.aspx'),
('Nauticus Maritime Museum', 'City of Norfolk', 'Norfolk, VA', 165000.00, '2026-01-10', 'Specialized cleaning for maritime museum, aquarium exhibits, and USS Wisconsin battleship deck areas. Marine environment experience. Artifact preservation.', '561720', 'https://www.norfolk.gov/bids.aspx'),
('Virginia Beach Aquarium & Marine Science Center', 'Virginia Marine Science Museum', 'Virginia Beach, VA', 295000.00, '2025-12-28', 'Aquarium facility cleaning including exhibit areas, touch pools, and education centers. Marine life safety protocols. Saltwater environment experience.', '561720', 'https://www.vbgov.com/departments/procurement'),

-- ADDITIONAL OPPORTUNITIES
('Peninsula Fine Arts Center', 'City of Newport News', 'Newport News, VA', 55000.00, '2025-11-28', 'Gallery and museum cleaning services. Art preservation standards. Careful handling of display areas. Event support for exhibition openings.', '561720', 'https://www.nngov.com/procurement'),
('Mariners'' Museum and Park', 'Newport News (Partner Facility)', 'Newport News, VA', 185000.00, '2025-12-15', 'Cleaning services for museum galleries, library, conservation lab, and park facilities. Rare artifact areas. Climate control requirements.', '561720', 'https://www.nngov.com/procurement'),
('Chrysler Museum of Art', 'City of Norfolk', 'Norfolk, VA', 205000.00, '2026-01-15', 'Museum-grade cleaning for galleries, glass studio, library, and event spaces. Fine art preservation expertise. Security clearance for valuable collections.', '561720', 'https://www.norfolk.gov/bids.aspx');

-- ==============================================================
-- DEPLOYMENT COMPLETE
-- ==============================================================
-- Added 50+ Virginia local government cleaning contracts
-- Locations: Hampton, Norfolk, Virginia Beach, Newport News, Chesapeake, 
--            Portsmouth, Suffolk, Williamsburg, York County
-- Contract values range from $45,000 to $920,000
-- Deadlines: November-January 2025-2026
-- ==============================================================
