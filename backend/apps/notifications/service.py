# apps/notifications/service.py
import requests
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification, NotificationChannel
from apps.events.websocket import WebSocketNotifier

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications through various channels"""

    def send_notification(
        self,
        user=None,
        organization=None,
        title="",
        message="",
        priority="medium",
        trigger_type="",
        trigger_id=None,
        metadata=None,
        action_url=None,
    ):
        """Send notification through configured channels"""

        channels = []
        if organization:
            channels = NotificationChannel.objects.filter(
                organization=organization,
                is_active=True,
            )

        sent_count = 0

        # Always send browser notification
        if user:
            self._send_browser_notification(
                user,
                title,
                message,
                priority,
                trigger_type,
                trigger_id,
                metadata,
                action_url,
            )
            sent_count += 1
        elif organization:
            # Send to all users in organization via WebSocket
            self._send_org_notification(organization, title, message, priority)

        # Send through configured channels
        for channel in channels:
            if self._should_notify(channel, priority, trigger_type):
                try:
                    if channel.channel_type == "email" and user and user.email:
                        self._send_email(channel, user.email, title, message)
                        sent_count += 1
                    elif channel.channel_type == "slack":
                        self._send_slack(channel, title, message, priority)
                        sent_count += 1
                    elif channel.channel_type == "discord":
                        self._send_discord(channel, title, message, priority)
                        sent_count += 1
                    elif channel.channel_type == "webhook":
                        self._send_webhook(channel, title, message, priority, metadata)
                        sent_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send notification via {channel.channel_type}: {e}"
                    )

        # Create notification record
        notification = Notification.objects.create(
            user=user,
            organization=organization,
            title=title,
            message=message,
            priority=priority,
            channel="browser",
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            metadata=metadata or {},
            action_url=action_url,
            is_sent=sent_count > 0,
            sent_at=timezone.now() if sent_count > 0 else None,
        )

        return notification

    def test_channel(self, channel):
        """Test a notification channel"""
        try:
            test_title = "SentinelOps Test Notification"
            test_message = (
                "This is a test notification to verify channel configuration."
            )

            if channel.channel_type == "email":
                self._send_email(
                    channel,
                    channel.config.get("test_email", ""),
                    test_title,
                    test_message,
                )
            elif channel.channel_type == "slack":
                self._send_slack(channel, test_title, test_message, "medium")
            elif channel.channel_type == "discord":
                self._send_discord(channel, test_title, test_message, "medium")
            elif channel.channel_type == "webhook":
                self._send_webhook(channel, test_title, test_message, "medium", {})

            return True
        except Exception as e:
            logger.error(f"Channel test failed: {e}")
            return False

    def _send_browser_notification(
        self,
        user,
        title,
        message,
        priority,
        trigger_type,
        trigger_id,
        metadata,
        action_url,
    ):
        """Send browser notification via WebSocket"""
        WebSocketNotifier.notify_user(
            user.id,
            {
                "title": title,
                "message": message,
                "priority": priority,
                "trigger_type": trigger_type,
                "action_url": action_url,
            },
        )

    def _send_org_notification(self, organization, title, message, priority):
        """Send notification to all users in organization"""
        WebSocketNotifier.notify_dashboard_update(
            {
                "notification": {
                    "title": title,
                    "message": message,
                    "priority": priority,
                    "timestamp": timezone.now().isoformat(),
                }
            },
            str(organization.id),
        )

    def _send_email(self, channel, to_email, title, message):
        """Send email notification"""
        if not to_email:
            return

        send_mail(
            subject=f"[SentinelOps] {title}",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "sentinelops@localhost"),
            recipient_list=[to_email],
            fail_silently=True,
        )

    def _send_slack(self, channel, title, message, priority):
        """Send Slack notification"""
        webhook_url = channel.config.get("webhook_url")
        if not webhook_url:
            return

        color_map = {
            "critical": "#FF0000",
            "high": "#FFA500",
            "medium": "#FFD700",
            "low": "#00FF00",
            "urgent": "#FF0000",
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(priority, "#808080"),
                    "title": title,
                    "text": message,
                    "footer": "SentinelOps Security Platform",
                    "ts": int(timezone.now().timestamp()),
                }
            ]
        }

        requests.post(webhook_url, json=payload, timeout=10)

    def _send_discord(self, channel, title, message, priority):
        """Send Discord notification"""
        webhook_url = channel.config.get("webhook_url")
        if not webhook_url:
            return

        color_map = {
            "critical": 0xFF0000,
            "high": 0xFFA500,
            "medium": 0xFFD700,
            "low": 0x00FF00,
            "urgent": 0xFF0000,
        }

        payload = {
            "username": "SentinelOps",
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color_map.get(priority, 0x808080),
                    "timestamp": timezone.now().isoformat(),
                    "footer": {"text": "SentinelOps Security Platform"},
                }
            ],
        }

        requests.post(webhook_url, json=payload, timeout=10)

    def _send_webhook(self, channel, title, message, priority, metadata):
        """Send custom webhook notification"""
        webhook_url = channel.config.get("webhook_url")
        if not webhook_url:
            return

        payload = {
            "source": "SentinelOps",
            "title": title,
            "message": message,
            "priority": priority,
            "metadata": metadata,
            "timestamp": timezone.now().isoformat(),
        }

        headers = channel.config.get("headers", {})
        headers["Content-Type"] = "application/json"

        requests.post(webhook_url, json=payload, headers=headers, timeout=10)

    def _should_notify(self, channel, priority, trigger_type):
        """Check if channel should receive this notification"""
        if priority in ["critical", "urgent"] and channel.notify_on_critical:
            return True
        if priority == "high" and channel.notify_on_high:
            return True
        if trigger_type == "incident" and channel.notify_on_incident:
            return True
        if trigger_type == "agent_offline" and channel.notify_on_agent_offline:
            return True
        return False


# Global notification triggers - called from signals/tasks
def notify_critical_alert(alert):
    """Send notification for critical alert"""
    service = NotificationService()
    service.send_notification(
        user=alert.assigned_to,
        organization=alert.organization,
        title=f"🚨 Critical Alert: {alert.title}",
        message=f"Severity: {alert.severity}\nSource: {alert.source}\n\n{alert.description[:300]}",
        priority="critical",
        trigger_type="alert",
        trigger_id=str(alert.id),
        action_url=f"/alerts/{alert.id}",
    )


def notify_incident_created(incident):
    """Send notification for new incident"""
    service = NotificationService()
    service.send_notification(
        user=incident.assigned_to,
        organization=incident.organization,
        title=f"🔴 New Incident: {incident.title}",
        message=f"Severity: {incident.severity}\nPriority: {incident.priority}\nType: {incident.incident_type}",
        priority="high",
        trigger_type="incident",
        trigger_id=str(incident.id),
        action_url=f"/incidents/{incident.id}",
    )


def notify_agent_offline(agent):
    """Send notification for offline agent"""
    service = NotificationService()
    service.send_notification(
        organization=agent.organization,
        title=f"⚠️ Agent Offline: {agent.name}",
        message=f"Agent {agent.name} ({agent.hostname}) went offline.\nLast heartbeat: {agent.last_heartbeat}",
        priority="high",
        trigger_type="agent_offline",
        trigger_id=str(agent.agent_id),
        action_url=f"/agents/{agent.agent_id}",
    )


def notify_rule_triggered(rule, alert):
    """Send notification for triggered rule"""
    service = NotificationService()
    service.send_notification(
        organization=rule.organization,
        title=f"📋 Rule Triggered: {rule.name}",
        message=f'Rule "{rule.name}" generated alert: {alert.title}',
        priority=alert.severity if alert.severity in ["critical", "high"] else "medium",
        trigger_type="rule",
        trigger_id=str(rule.id),
        action_url=f"/alerts/{alert.id}",
    )
