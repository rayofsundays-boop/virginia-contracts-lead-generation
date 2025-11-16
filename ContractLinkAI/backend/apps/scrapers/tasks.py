"""
Celery tasks for scraping state and city portals.
"""
from celery import shared_task
from django.utils import timezone
import asyncio
import logging
from apps.states.models import StatePortal, CityPortal
from apps.rfps.models import RFP
from apps.scrapers.models import ScrapeJob, ScrapeError
from apps.scrapers.scraper_base import get_scraper_for_state
from apps.ai_engine.classifier import CityPortalDiscovery

logger = logging.getLogger('scrapers')


@shared_task(name='scrapers.tasks.hourly_state_scrape')
def hourly_state_scrape():
    """
    Scrape all active state portals hourly.
    """
    logger.info("Starting hourly state scrape")
    
    active_portals = StatePortal.objects.filter(is_active=True)
    total_new_rfps = 0
    
    for portal in active_portals:
        try:
            # Create scrape job
            job = ScrapeJob.objects.create(
                job_type='state',
                target_state_code=portal.state_code,
                target_url=portal.portal_url,
                status='running',
                started_at=timezone.now()
            )
            
            # Get scraper
            scraper = get_scraper_for_state(portal.state_code)
            if not scraper:
                job.status = 'failed'
                job.error_message = f"No scraper available for {portal.state_code}"
                job.completed_at = timezone.now()
                job.save()
                continue
            
            # Run scraper
            rfps = asyncio.run(scraper.scrape())
            
            # Save RFPs
            new_count, updated_count = save_rfps(rfps)
            
            # Update job
            job.status = 'completed'
            job.rfps_found = len(rfps)
            job.rfps_new = new_count
            job.rfps_updated = updated_count
            job.completed_at = timezone.now()
            job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            job.save()
            
            # Update portal statistics
            portal.total_rfps_found += new_count
            portal.successful_scrapes += 1
            portal.last_scraped = timezone.now()
            portal.save()
            
            total_new_rfps += new_count
            
            logger.info(f"Scraped {portal.state_code}: {new_count} new, {updated_count} updated")
            
        except Exception as e:
            logger.error(f"Error scraping {portal.state_code}: {str(e)}")
            
            # Log error
            ScrapeError.objects.create(
                scrape_job=job if 'job' in locals() else None,
                error_type=type(e).__name__,
                error_message=str(e),
                target_url=portal.portal_url
            )
            
            # Update portal
            portal.failed_scrapes += 1
            portal.save()
            
            if 'job' in locals():
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = timezone.now()
                job.save()
    
    logger.info(f"Hourly scrape complete: {total_new_rfps} new RFPs across all states")
    return {'total_new_rfps': total_new_rfps}


@shared_task(name='scrapers.tasks.nightly_city_discovery')
def nightly_city_discovery():
    """
    Discover new city procurement portals using AI.
    Runs nightly for a subset of cities.
    """
    logger.info("Starting nightly city discovery")
    
    # Major cities to check (top 100 US cities)
    major_cities = [
        ('New York', 'NY'), ('Los Angeles', 'CA'), ('Chicago', 'IL'),
        ('Houston', 'TX'), ('Phoenix', 'AZ'), ('Philadelphia', 'PA'),
        ('San Antonio', 'TX'), ('San Diego', 'CA'), ('Dallas', 'TX'),
        ('San Jose', 'CA'), ('Austin', 'TX'), ('Jacksonville', 'FL'),
        ('Fort Worth', 'TX'), ('Columbus', 'OH'), ('Charlotte', 'NC'),
        ('San Francisco', 'CA'), ('Indianapolis', 'IN'), ('Seattle', 'WA'),
        ('Denver', 'CO'), ('Washington', 'DC'), ('Boston', 'MA'),
        ('El Paso', 'TX'), ('Nashville', 'TN'), ('Detroit', 'MI'),
        ('Oklahoma City', 'OK'), ('Portland', 'OR'), ('Las Vegas', 'NV'),
        ('Memphis', 'TN'), ('Louisville', 'KY'), ('Baltimore', 'MD'),
        # Add more cities...
    ]
    
    ai_discovery = CityPortalDiscovery()
    discovered_count = 0
    
    for city_name, state_code in major_cities[:10]:  # Process 10 cities per night
        try:
            # Check if already discovered
            state_portal = StatePortal.objects.filter(state_code=state_code).first()
            if not state_portal:
                continue
            
            existing = CityPortal.objects.filter(
                state_portal=state_portal,
                city_name=city_name
            ).exists()
            
            if existing:
                continue
            
            # Use AI to find portal
            result = ai_discovery.find_city_portal(city_name, state_code)
            
            # Only save if confidence is high enough
            if result.get('confidence_score', 0) >= 0.6 and result.get('portal_url'):
                CityPortal.objects.create(
                    state_portal=state_portal,
                    city_name=city_name,
                    portal_name=result.get('portal_name', f'{city_name} Procurement'),
                    portal_url=result['portal_url'],
                    discovered_by_ai=True,
                    discovery_confidence=result['confidence_score'],
                    is_active=False,  # Needs manual verification
                    is_verified=False
                )
                
                discovered_count += 1
                logger.info(f"Discovered portal for {city_name}, {state_code}")
            
        except Exception as e:
            logger.error(f"Error discovering portal for {city_name}, {state_code}: {str(e)}")
    
    logger.info(f"City discovery complete: {discovered_count} new portals found")
    return {'discovered_count': discovered_count}


def save_rfps(rfps_data):
    """
    Save scraped RFPs to database.
    
    Returns:
        Tuple of (new_count, updated_count)
    """
    new_count = 0
    updated_count = 0
    
    for rfp_data in rfps_data:
        try:
            rfp_number = rfp_data.get('rfp_number')
            if not rfp_number:
                continue
            
            # Check if RFP already exists
            existing = RFP.objects.filter(rfp_number=rfp_number).first()
            
            if existing:
                # Update existing RFP
                for key, value in rfp_data.items():
                    setattr(existing, key, value)
                existing.save()
                updated_count += 1
            else:
                # Create new RFP
                RFP.objects.create(**rfp_data)
                new_count += 1
                
        except Exception as e:
            logger.error(f"Error saving RFP {rfp_data.get('rfp_number')}: {str(e)}")
    
    return new_count, updated_count
