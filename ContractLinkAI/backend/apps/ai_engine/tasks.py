"""
Celery tasks for AI classification of RFPs.
"""
from celery import shared_task
from django.utils import timezone
import logging
from apps.rfps.models import RFP
from apps.ai_engine.models import AIClassification
from apps.ai_engine.classifier import AIClassifier

logger = logging.getLogger('ai_engine')


@shared_task(name='ai_engine.tasks.classify_new_rfps')
def classify_new_rfps():
    """
    Classify newly discovered RFPs that haven't been classified yet.
    Runs every 30 minutes.
    """
    logger.info("Starting AI classification of new RFPs")
    
    # Get RFPs without AI classification
    unclassified_rfps = RFP.objects.filter(
        ai_classification_confidence__isnull=True,
        status='active'
    )[:50]  # Process 50 at a time
    
    classifier = AIClassifier()
    classified_count = 0
    
    for rfp in unclassified_rfps:
        try:
            # Classify the RFP
            result = classifier.classify_rfp_with_label_explanation(
                rfp.title,
                rfp.description
            )
            
            # Update RFP with classification
            rfp.category = result.get('predicted_category', 'other')
            rfp.ai_classification_confidence = result.get('confidence_score', 0.0)
            rfp.ai_classification_date = timezone.now()
            
            # Extract keywords if available
            if result.get('extracted_keywords'):
                rfp.keywords = result['extracted_keywords']
            
            rfp.save()
            
            # Save detailed classification result
            AIClassification.objects.create(
                rfp=rfp,
                predicted_category=result.get('predicted_category', 'other'),
                confidence_score=result.get('confidence_score', 0.0),
                top_predictions=result.get('top_predictions', []),
                reasoning=result.get('reasoning', ''),
                extracted_keywords=result.get('extracted_keywords', []),
                model_name=result.get('model_name', ''),
                processing_time_ms=result.get('processing_time_ms'),
                tokens_used=result.get('tokens_used')
            )
            
            classified_count += 1
            logger.info(f"Classified RFP {rfp.rfp_number}: {rfp.category} ({rfp.ai_classification_confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error classifying RFP {rfp.rfp_number}: {str(e)}")
    
    logger.info(f"AI classification complete: {classified_count} RFPs classified")
    return {'classified_count': classified_count}


@shared_task(name='ai_engine.tasks.reclassify_low_confidence_rfps')
def reclassify_low_confidence_rfps():
    """
    Re-classify RFPs with low confidence scores using enhanced method.
    Runs weekly.
    """
    logger.info("Re-classifying low confidence RFPs")
    
    # Get RFPs with low confidence
    low_confidence_rfps = RFP.objects.filter(
        ai_classification_confidence__lt=0.7,
        status='active'
    ).order_by('ai_classification_confidence')[:20]
    
    classifier = AIClassifier()
    improved_count = 0
    
    for rfp in low_confidence_rfps:
        try:
            # Use enhanced classification method
            result = classifier.classify_rfp_with_label_explanation(
                rfp.title,
                rfp.description
            )
            
            new_confidence = result.get('confidence_score', 0.0)
            
            # Only update if confidence improved
            if new_confidence > rfp.ai_classification_confidence:
                rfp.category = result.get('predicted_category', rfp.category)
                rfp.ai_classification_confidence = new_confidence
                rfp.ai_classification_date = timezone.now()
                rfp.save()
                
                improved_count += 1
                logger.info(f"Improved classification for {rfp.rfp_number}: {new_confidence:.2f}")
                
        except Exception as e:
            logger.error(f"Error re-classifying RFP {rfp.rfp_number}: {str(e)}")
    
    logger.info(f"Re-classification complete: {improved_count} improved")
    return {'improved_count': improved_count}
