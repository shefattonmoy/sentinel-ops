# apps/gamification/engine.py
from django.utils import timezone
from datetime import timedelta

POINTS = {
    "resolve_alert": {"low": 5, "medium": 10, "high": 20, "critical": 50},
    "close_incident": {"low": 20, "medium": 40, "high": 60, "critical": 100},
    "detect_threat": 30,
    "execute_playbook": 15,
    "quick_response": 25,
    "streak_bonus": 10,
}

TITLES = {
    1: "Junior Analyst",
    5: "Security Analyst",
    10: "Senior Analyst",
    20: "Threat Hunter",
    35: "Security Architect",
    50: "Cyber Defender",
    75: "Sentinel Master",
    100: "Security Legend",
}

BADGES = [
    {
        "name": "First Blood",
        "description": "Resolve your first alert",
        "icon": "🔰",
        "criteria": {"alerts_resolved": 1},
    },
    {
        "name": "Alert Machine",
        "description": "Resolve 100 alerts",
        "icon": "⚡",
        "criteria": {"alerts_resolved": 100},
    },
    {
        "name": "Incident Commander",
        "description": "Close 10 incidents",
        "icon": "🎖️",
        "criteria": {"incidents_closed": 10},
    },
    {
        "name": "Threat Hunter",
        "description": "Detect 50 threats",
        "icon": "🔍",
        "criteria": {"threats_detected": 50},
    },
    {
        "name": "Speed Demon",
        "description": "Average response time under 2 min",
        "icon": "⚡",
        "criteria": {"response_time_avg": 2},
    },
    {
        "name": "Automator",
        "description": "Execute 25 playbooks",
        "icon": "🤖",
        "criteria": {"playbooks_executed": 25},
    },
    {
        "name": "Weekly Champion",
        "description": "Top of weekly leaderboard",
        "icon": "👑",
        "criteria": {"weekly_rank": 1},
    },
    {
        "name": "Perfect Week",
        "description": "7-day activity streak",
        "icon": "🔥",
        "criteria": {"streak": 7},
    },
]


class GamificationEngine:
    """Gamification points and achievements engine"""

    def award_points(self, user, action, severity=None):
        """Award points for an action"""
        from .models import AnalystProfile, Badge

        profile, _ = AnalystProfile.objects.get_or_create(user=user)

        points = 0
        if action == "resolve_alert" and severity:
            points = POINTS["resolve_alert"].get(severity, 10)
        elif action == "close_incident" and severity:
            points = POINTS["close_incident"].get(severity, 40)
        elif action == "detect_threat":
            points = POINTS["detect_threat"]
        elif action == "execute_playbook":
            points = POINTS["execute_playbook"]
        elif action == "quick_response":
            points = POINTS["quick_response"]

        profile.total_points += points
        profile.weekly_points += points
        profile.monthly_points += points

        if action == "resolve_alert":
            profile.alerts_resolved += 1
        elif action == "close_incident":
            profile.incidents_closed += 1
        elif action == "detect_threat":
            profile.threats_detected += 1
        elif action == "execute_playbook":
            profile.playbooks_executed += 1

        # Check level up
        new_level = profile.total_points // 100 + 1
        if new_level > profile.level:
            profile.level = new_level
            for level_threshold, title in sorted(TITLES.items(), reverse=True):
                if new_level >= level_threshold:
                    profile.title = title
                    break

        # Check achievements
        self._check_achievements(profile)

        profile.save()
        return points

    def _check_achievements(self, profile):
        """Check and award new achievements"""
        from .models import Badge

        current_achievements = profile.achievements or []

        for badge_data in BADGES:
            if badge_data["name"] in current_achievements:
                continue

            criteria = badge_data["criteria"]
            earned = True

            for key, value in criteria.items():
                if key == "alerts_resolved" and profile.alerts_resolved < value:
                    earned = False
                elif key == "incidents_closed" and profile.incidents_closed < value:
                    earned = False
                elif key == "threats_detected" and profile.threats_detected < value:
                    earned = False
                elif key == "playbooks_executed" and profile.playbooks_executed < value:
                    earned = False

            if earned:
                badge, _ = Badge.objects.get_or_create(
                    name=badge_data["name"],
                    defaults={
                        "description": badge_data["description"],
                        "icon": badge_data["icon"],
                        "criteria": criteria,
                    },
                )
                current_achievements.append(badge_data["name"])
                profile.total_points += badge.points

        profile.achievements = current_achievements

    def generate_leaderboard(self, period="weekly"):
        """Generate leaderboard"""
        from .models import AnalystProfile, Leaderboard

        # Get ALL profiles for update (not sliced)
        all_profiles = AnalystProfile.objects.all()

        # Get top 20 for display
        order_field = "-weekly_points" if period == "weekly" else "-monthly_points"
        top_profiles = all_profiles.order_by(order_field)[:20]

        rankings = []
        for i, profile in enumerate(top_profiles, 1):
            rankings.append(
                {
                    "rank": i,
                    "user": profile.user.username,
                    "points": (
                        profile.weekly_points
                        if period == "weekly"
                        else profile.monthly_points
                    ),
                    "level": profile.level,
                    "title": profile.title,
                    "achievements": len(profile.achievements or []),
                }
            )

        # Save snapshot
        now = timezone.now().date()
        if period == "weekly":
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=6)
        else:
            start = now.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        Leaderboard.objects.create(
            period=period,
            period_start=start,
            period_end=end,
            rankings=rankings,
        )

        # Reset points on FULL queryset (not sliced)
        if period == "weekly":
            all_profiles.update(weekly_points=0)
        else:
            all_profiles.update(monthly_points=0)

        return rankings
