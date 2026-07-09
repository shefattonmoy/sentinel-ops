# apps/agents/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Agent, AgentHeartbeat, AgentConfiguration, AgentGroup

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'hostname', 'agent_type', 'status_indicator',
        'version', 'last_heartbeat', 'cpu_usage_bar',
        'memory_usage_bar', 'is_active'
    ]
    list_filter = ['status', 'agent_type', 'is_active', 'organization']
    search_fields = ['name', 'hostname', 'agent_id', 'token']
    readonly_fields = [
        'agent_id', 'token', 'last_heartbeat',
        'cpu_usage', 'memory_usage', 'disk_usage',
        'total_logs_collected', 'total_events_generated'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('agent_id', 'name', 'hostname', 'version', 'agent_type')
        }),
        ('Authentication', {
            'fields': ('token',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'last_heartbeat', 'is_active')
        }),
        ('System Metrics', {
            'fields': ('cpu_usage', 'memory_usage', 'disk_usage', 'network_status')
        }),
        ('Statistics', {
            'fields': ('total_logs_collected', 'total_events_generated', 'total_alerts_triggered')
        }),
        ('Configuration', {
            'fields': ('monitored_logs', 'tags', 'heartbeat_interval')
        }),
        ('Organization', {
            'fields': ('organization',)
        }),
    )
    
    def status_indicator(self, obj):
        colors = {
            'online': 'green',
            'offline': 'red',
            'degraded': 'orange',
            'error': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.status.upper()
        )
    status_indicator.short_description = 'Status'
    
    def cpu_usage_bar(self, obj):
        if obj.cpu_usage is None:
            return '-'
        color = 'red' if obj.cpu_usage > 90 else 'orange' if obj.cpu_usage > 70 else 'green'
        return format_html(
            '<div style="background: #eee; width: 100px;">'
            '<div style="background: {}; width: {}px; height: 20px;"></div>'
            '</div> {}%',
            color,
            obj.cpu_usage,
            round(obj.cpu_usage, 1)
        )
    cpu_usage_bar.short_description = 'CPU Usage'
    
    def memory_usage_bar(self, obj):
        if obj.memory_usage is None:
            return '-'
        color = 'red' if obj.memory_usage > 90 else 'orange' if obj.memory_usage > 70 else 'green'
        return format_html(
            '<div style="background: #eee; width: 100px;">'
            '<div style="background: {}; width: {}px; height: 20px;"></div>'
            '</div> {}%',
            color,
            obj.memory_usage,
            round(obj.memory_usage, 1)
        )
    memory_usage_bar.short_description = 'Memory Usage'

@admin.register(AgentHeartbeat)
class AgentHeartbeatAdmin(admin.ModelAdmin):
    list_display = ['agent', 'timestamp', 'cpu_usage', 'memory_usage', 'disk_usage', 'is_healthy']
    list_filter = ['is_healthy', 'timestamp']
    search_fields = ['agent__name', 'agent__hostname']
    readonly_fields = ['timestamp']

@admin.register(AgentConfiguration)
class AgentConfigurationAdmin(admin.ModelAdmin):
    list_display = ['agent', 'heartbeat_interval', 'log_level_filter', 'enable_docker_monitoring']
    list_filter = ['log_level_filter', 'enable_docker_monitoring']
    search_fields = ['agent__name']

@admin.register(AgentGroup)
class AgentGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent_count', 'online_count', 'offline_count']
    filter_horizontal = ['agents']
    
    def agent_count(self, obj):
        return obj.agents.count()
    
    def online_count(self, obj):
        return obj.online_count()
    
    def offline_count(self, obj):
        return obj.offline_count()