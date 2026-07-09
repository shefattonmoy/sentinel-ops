# apps/alerts/tasks.py
from celery import shared_task
from alerts.engine import RuleEngine, AlertGenerator

@shared_task
def evaluate_all_rules():
    """
    Periodic task to evaluate all active rules.
    Should run every 1-5 minutes.
    """
    engine = RuleEngine()
    triggered = engine.evaluate_all_active_rules()
    
    generator = AlertGenerator()
    alerts_created = 0
    
    for rule, context in triggered:
        alert = generator.generate_alert(rule, context)
        if alert:
            alerts_created += 1
    
    return f"Evaluated rules, triggered {len(triggered)}, created {alerts_created} alerts"

@shared_task
def evaluate_rule(rule_id):
    """
    Evaluate a specific rule.
    """
    from .models import DetectionRule
    
    try:
        rule = DetectionRule.objects.get(id=rule_id)
    except DetectionRule.DoesNotExist:
        return f"Rule {rule_id} not found"
    
    engine = RuleEngine()
    is_triggered, context = engine.evaluate_rule(rule)
    
    if is_triggered:
        generator = AlertGenerator()
        alert = generator.generate_alert(rule, context)
        return f"Rule triggered, alert created: {alert.id if alert else 'No alert'}"
    
    return f"Rule not triggered"