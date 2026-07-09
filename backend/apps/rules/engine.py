# apps/rules/engine.py
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg, Max, Min
from django.db import transaction
from apps.alerts.models import Alert
from apps.audit.models import log_action
from .models import DetectionRule, RuleExecution
from apps.events.models import Event

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Detection Rule Engine - evaluates rules against events and triggers alerts.
    """

    def __init__(self):
        self.triggered_rules = []
        self.errors = []

    def evaluate_rule(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """
        Evaluate a single detection rule.
        Returns (is_triggered, context)
        """
        start_time = time.time()
        context = {}

        try:
            if rule.rule_type == "threshold":
                is_triggered, context = self._evaluate_threshold(rule)
            elif rule.rule_type == "correlation":
                is_triggered, context = self._evaluate_correlation(rule)
            elif rule.rule_type == "pattern":
                is_triggered, context = self._evaluate_pattern(rule)
            elif rule.rule_type == "frequency":
                is_triggered, context = self._evaluate_frequency(rule)
            elif rule.rule_type == "blacklist":
                is_triggered, context = self._evaluate_blacklist(rule)
            else:
                # Default threshold evaluation
                is_triggered, context = self._evaluate_threshold(rule)
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
            is_triggered = False
            context = {"error": str(e)}

        execution_time = (time.time() - start_time) * 1000

        # Record execution
        RuleExecution.objects.create(
            rule=rule,
            execution_time=execution_time,
            is_triggered=is_triggered,
            matched_count=context.get("matched_count", 0),
            events_analyzed=context.get("events_analyzed", 0),
            context=context,
            error_message=context.get("error"),
        )

        return is_triggered, context

    def _evaluate_threshold(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """Evaluate threshold-based rule"""
        conditions = rule.conditions

        event_type = conditions.get("event_type")
        timeframe = conditions.get("timeframe_minutes", 5)
        threshold = conditions.get("threshold", 1)
        group_by = conditions.get("group_by", [])
        filters = conditions.get("filters", {})

        # Build query
        time_threshold = timezone.now() - timedelta(minutes=timeframe)

        queryset = Event.objects.filter(
            event_type=event_type, timestamp__gte=time_threshold
        )

        # Apply agent filter
        agent_filter = rule.get_agent_filter()
        if agent_filter:
            queryset = queryset.filter(agent_filter)

        # Apply organization filter
        if rule.organization:
            queryset = queryset.filter(agent__organization=rule.organization)

        # Apply additional filters
        if filters.get("severity"):
            queryset = queryset.filter(severity__in=filters["severity"])

        if filters.get("source"):
            queryset = queryset.filter(source__in=filters["source"])

        if filters.get("exclude_ips"):
            queryset = queryset.exclude(source_ip__in=filters["exclude_ips"])

        events_analyzed = queryset.count()
        triggered_groups = []

        if group_by:
            # Group by specified fields
            groups = (
                queryset.values(*group_by)
                .annotate(
                    count=Count("id"),
                    first_seen=Min("timestamp"),
                    last_seen=Max("timestamp"),
                    sample_message=Max("message"),
                )
                .order_by("-count")
            )

            for group in groups:
                if group["count"] >= threshold:
                    triggered_groups.append(
                        {
                            "group": {k: group[k] for k in group_by},
                            "count": group["count"],
                            "first_seen": group["first_seen"].isoformat(),
                            "last_seen": group["last_seen"].isoformat(),
                            "sample_message": group["sample_message"],
                        }
                    )
        else:
            # Simple threshold check
            total_count = queryset.count()
            if total_count >= threshold:
                triggered_groups.append(
                    {
                        "total_count": total_count,
                        "threshold": threshold,
                        "timeframe_minutes": timeframe,
                    }
                )

        is_triggered = len(triggered_groups) > 0

        context = {
            "matched_count": len(triggered_groups),
            "events_analyzed": events_analyzed,
            "triggered_groups": triggered_groups,
            "timeframe_minutes": timeframe,
            "threshold": threshold,
        }

        return is_triggered, context

    def _evaluate_correlation(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """Evaluate correlation rule (multiple events must occur together)"""
        conditions = rule.conditions
        events_config = conditions.get("events", [])
        group_by = conditions.get("group_by", ["source_ip"])
        require_all = conditions.get("require_all", True)
        timeframe = conditions.get("timeframe_minutes", 5)

        time_threshold = timezone.now() - timedelta(minutes=timeframe)
        matched_correlations = []
        total_events_analyzed = 0

        # Get base queryset
        base_queryset = Event.objects.filter(timestamp__gte=time_threshold)

        if rule.organization:
            base_queryset = base_queryset.filter(agent__organization=rule.organization)

        # For each group_by field, check if all conditions are met
        if group_by:
            distinct_groups = base_queryset.values(*group_by).distinct()

            for group_vals in distinct_groups:
                group_filter = Q()
                for field in group_by:
                    group_filter &= Q(**{field: group_vals[field]})

                group_events = base_queryset.filter(group_filter)
                total_events_analyzed += group_events.count()

                # Check each event condition
                conditions_met = []

                for event_config in events_config:
                    event_queryset = group_events.filter(
                        event_type=event_config["event_type"]
                    )

                    if "timeframe_minutes" in event_config:
                        event_time_threshold = timezone.now() - timedelta(
                            minutes=event_config["timeframe_minutes"]
                        )
                        event_queryset = event_queryset.filter(
                            timestamp__gte=event_time_threshold
                        )

                    count = event_queryset.count()
                    required_count = event_config.get("count", 1)
                    conditions_met.append(count >= required_count)

                # Check if correlation is satisfied
                correlation_matched = (
                    all(conditions_met) if require_all else any(conditions_met)
                )

                if correlation_matched:
                    matched_correlations.append(
                        {
                            "group": {k: group_vals[k] for k in group_by},
                            "conditions_met": conditions_met,
                        }
                    )

        is_triggered = len(matched_correlations) > 0

        return is_triggered, {
            "matched_count": len(matched_correlations),
            "events_analyzed": total_events_analyzed,
            "correlations": matched_correlations,
        }

    def _evaluate_pattern(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """Evaluate pattern matching rule"""
        conditions = rule.conditions
        pattern = conditions.get("pattern", "")
        timeframe = conditions.get("timeframe_minutes", 15)
        field = conditions.get("field", "message")

        time_threshold = timezone.now() - timedelta(minutes=timeframe)

        queryset = Event.objects.filter(
            timestamp__gte=time_threshold, **{f"{field}__regex": pattern}
        )

        if rule.organization:
            queryset = queryset.filter(agent__organization=rule.organization)

        matched_count = queryset.count()
        is_triggered = matched_count > 0

        # Get sample matches
        samples = list(queryset.values("id", "message", "timestamp")[:5])

        return is_triggered, {
            "matched_count": matched_count,
            "events_analyzed": matched_count,
            "samples": samples,
            "pattern": pattern,
        }

    def _evaluate_frequency(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """Evaluate frequency-based rule (unusual activity)"""
        conditions = rule.conditions
        event_type = conditions.get("event_type")
        timeframe = conditions.get("timeframe_minutes", 60)
        baseline_timeframe = conditions.get(
            "baseline_timeframe_minutes", 1440
        )  # 24 hours
        threshold_multiplier = conditions.get("threshold_multiplier", 3)
        group_by = conditions.get("group_by", ["source_ip"])

        now = timezone.now()
        current_window = now - timedelta(minutes=timeframe)
        baseline_window_start = now - timedelta(minutes=baseline_timeframe)
        baseline_window_end = current_window

        # Current frequency
        current_queryset = Event.objects.filter(
            event_type=event_type, timestamp__gte=current_window
        )

        if rule.organization:
            current_queryset = current_queryset.filter(
                agent__organization=rule.organization
            )

        # Baseline frequency
        baseline_queryset = Event.objects.filter(
            event_type=event_type,
            timestamp__gte=baseline_window_start,
            timestamp__lt=baseline_window_end,
        )

        if rule.organization:
            baseline_queryset = baseline_queryset.filter(
                agent__organization=rule.organization
            )

        anomalies = []

        if group_by:
            current_groups = current_queryset.values(*group_by).annotate(
                current_count=Count("id")
            )

            for group in current_groups:
                baseline_filter = Q()
                for field in group_by:
                    baseline_filter &= Q(**{field: group[field]})

                baseline_avg = baseline_queryset.filter(baseline_filter).count()
                baseline_avg = baseline_avg / (baseline_timeframe / timeframe)

                if (
                    baseline_avg > 0
                    and group["current_count"] > baseline_avg * threshold_multiplier
                ):
                    anomalies.append(
                        {
                            "group": {k: group[k] for k in group_by},
                            "current_count": group["current_count"],
                            "expected_count": baseline_avg,
                            "multiplier": group["current_count"] / baseline_avg,
                        }
                    )

        is_triggered = len(anomalies) > 0

        return is_triggered, {
            "matched_count": len(anomalies),
            "events_analyzed": current_queryset.count(),
            "anomalies": anomalies,
        }

    def _evaluate_blacklist(self, rule: DetectionRule) -> Tuple[bool, Dict]:
        """Evaluate blacklist rule"""
        conditions = rule.conditions
        blacklist_field = conditions.get("field", "source_ip")
        blacklist_values = conditions.get("values", [])
        timeframe = conditions.get("timeframe_minutes", 60)

        time_threshold = timezone.now() - timedelta(minutes=timeframe)

        queryset = Event.objects.filter(
            timestamp__gte=time_threshold,
            **{f"{blacklist_field}__in": blacklist_values},
        )

        if rule.organization:
            queryset = queryset.filter(agent__organization=rule.organization)

        matched_count = queryset.count()
        is_triggered = matched_count > 0

        matches = (
            queryset.values(blacklist_field)
            .annotate(count=Count("id"), last_seen=Max("timestamp"))
            .order_by("-count")[:10]
        )

        return is_triggered, {
            "matched_count": matched_count,
            "events_analyzed": matched_count,
            "matches": list(matches),
        }

    def evaluate_all_active_rules(self, organization=None):
        """Evaluate all active rules"""
        rules = DetectionRule.objects.filter(status="active")

        if organization:
            rules = rules.filter(
                Q(organization=organization) | Q(organization__isnull=True)
            )

        triggered = []

        for rule in rules:
            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(
                    minutes=rule.cooldown_minutes
                )
                if timezone.now() < cooldown_end:
                    continue

            is_triggered, context = self.evaluate_rule(rule)

            if is_triggered:
                triggered.append((rule, context))
                rule.times_triggered += 1
                rule.last_triggered = timezone.now()
                rule.save(update_fields=["times_triggered", "last_triggered"])

        return triggered


class AlertGenerator:
    """Generates alerts from triggered rules"""

    def __init__(self):
        pass

    def generate_alert(self, rule: DetectionRule, context: Dict):
        """Generate an alert from a triggered rule"""

        actions = rule.actions

        if not actions.get("create_alert", True):
            return None

        # Build alert title
        title = actions.get("alert_title", rule.name)

        # Replace variables in title
        for group in context.get("triggered_groups", []):
            if "group" in group:
                for key, value in group["group"].items():
                    title = title.replace(f"{{{key}}}", str(value))

        # Build description
        description = actions.get("alert_description", "")
        if not description:
            description = f"Rule '{rule.name}' triggered:\n"
            description += f"Rule Type: {rule.rule_type}\n"

            for group in context.get("triggered_groups", [])[:5]:
                description += (
                    f"- Count: {group.get('count', group.get('total_count', 'N/A'))}\n"
                )
                if "group" in group:
                    for key, value in group["group"].items():
                        description += f"  {key}: {value}\n"

        # Determine severity
        severity = actions.get("alert_severity", rule.severity)

        # Create alert
        alert = Alert.objects.create(
            title=title,
            description=description,
            severity=severity,
            source="rule_engine",
            category=actions.get("alert_category", rule.category),
            organization=rule.organization,
            metadata={
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "rule_type": rule.rule_type,
                "context": context,
                "triggered_at": timezone.now().isoformat(),
            },
        )

        log_action(
            user=None,
            action="ALERT_CREATE",
            description=f'Alert "{alert.title}" generated by rule "{rule.name}"',
            obj=alert,
            severity=(
                alert.severity if alert.severity in ["high", "critical"] else "info"
            ),
            metadata={"rule_name": rule.name, "rule_type": rule.rule_type},
        )

        # Update rule statistics
        rule.alerts_generated += 1
        rule.save(update_fields=["alerts_generated"])

        return alert
