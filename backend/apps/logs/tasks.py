# apps/logs/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task
def parse_logs_async(log_ids, agent_id):
    """
    Asynchronously parse logs and generate events.
    This task is called after logs are ingested.
    """
    from .models import RawLog
    from apps.agents.models import Agent
    from apps.events.parsers import get_parser
    from apps.events.models import Event
    
    try:
        agent = Agent.objects.get(agent_id=agent_id)
    except Agent.DoesNotExist:
        logger.error(f"Agent not found: {agent_id}")
        return
    
    logs = RawLog.objects.filter(id__in=log_ids, is_parsed=False)
    events_created = 0
    
    for raw_log in logs:
        try:
            # Get appropriate parser for this log source
            parser = get_parser(raw_log.source)
            
            if parser:
                # Parse the log and generate events
                parsed_events = parser.parse(raw_log)
                
                # Create events
                for event_data in parsed_events:
                    Event.objects.create(
                        raw_log=raw_log,
                        agent=agent,
                        timestamp=raw_log.timestamp,
                        **event_data
                    )
                    events_created += 1
                
                # Mark log as parsed
                raw_log.is_parsed = True
                raw_log.parsed_at = timezone.now()
                raw_log.save(update_fields=['is_parsed', 'parsed_at'])
            else:
                # No parser available, mark as parsed anyway
                raw_log.is_parsed = True
                raw_log.parsed_at = timezone.now()
                raw_log.save(update_fields=['is_parsed', 'parsed_at'])
        
        except Exception as e:
            logger.error(f"Error parsing log {raw_log.id}: {str(e)}")
            raw_log.parse_error = str(e)
            raw_log.save(update_fields=['parse_error'])
    
    # Update agent statistics
    agent.total_events_generated += events_created
    agent.save(update_fields=['total_events_generated'])
    
    return f"Parsed {len(logs)} logs, generated {events_created} events"

@shared_task
def cleanup_old_logs():
    """
    Clean up raw logs older than retention period.
    Default: 30 days for raw logs, 90 days for parsed logs.
    """
    from .models import RawLog
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Delete old unparsed logs
    deleted_unparsed = RawLog.objects.filter(
        is_parsed=False,
        created_at__lt=thirty_days_ago
    ).delete()[0]
    
    # Keep parsed logs for 90 days
    ninety_days_ago = timezone.now() - timedelta(days=90)
    deleted_parsed = RawLog.objects.filter(
        is_parsed=True,
        created_at__lt=ninety_days_ago
    ).delete()[0]
    
    return f"Cleaned up {deleted_unparsed} unparsed and {deleted_parsed} parsed logs"

@shared_task
def retry_failed_parsing():
    """
    Retry parsing for logs that failed to parse.
    """
    from .models import RawLog
    
    failed_logs = RawLog.objects.filter(
        is_parsed=False,
        parse_error__isnull=False,
        created_at__gte=timezone.now() - timedelta(hours=24)
    )[:1000]
    
    if failed_logs:
        log_ids = [str(log.id) for log in failed_logs]
        # Reset parse error and retry
        failed_logs.update(parse_error=None)
        parse_logs_async.delay(log_ids, str(failed_logs[0].agent.agent_id))
        
        return f"Retrying parsing for {len(log_ids)} failed logs"
    
    return "No failed logs to retry"