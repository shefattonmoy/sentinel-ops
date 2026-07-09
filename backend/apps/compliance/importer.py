# apps/compliance/importer.py

SOC2_CONTROLS = [
    {'control_id': 'CC1.1', 'title': 'COSO Principle 1', 'category': 'Control Environment',
     'events': ['USER_CREATED', 'USER_DELETED', 'SUDO_COMMAND']},
    {'control_id': 'CC6.1', 'title': 'Logical Access Security', 'category': 'Logical and Physical Access',
     'events': ['FAILED_LOGIN', 'SUCCESSFUL_LOGIN', 'ACCESS_DENIED']},
    {'control_id': 'CC6.3', 'title': 'Access Provisioning', 'category': 'Logical and Physical Access',
     'events': ['USER_CREATED']},
    {'control_id': 'CC7.1', 'title': 'Vulnerability Detection', 'category': 'System Operations',
     'events': ['CONTAINER_CRASH', 'SERVER_ERROR', 'DJANGO_ERROR']},
    {'control_id': 'CC7.2', 'title': 'Intrusion Detection', 'category': 'System Operations',
     'events': ['BRUTE_FORCE_ATTEMPT', 'ACCESS_DENIED']},
    {'control_id': 'CC8.1', 'title': 'Change Management', 'category': 'Change Management',
     'events': ['CONTAINER_RESTART', 'SERVICE_FAILURE']},
]

ISO27001_CONTROLS = [
    {'control_id': 'A.9.2.1', 'title': 'User Registration', 'category': 'Access Control',
     'events': ['USER_CREATED']},
    {'control_id': 'A.9.4.2', 'title': 'Secure Login', 'category': 'Access Control',
     'events': ['FAILED_LOGIN', 'SUCCESSFUL_LOGIN']},
    {'control_id': 'A.12.4.1', 'title': 'Event Logging', 'category': 'Operations Security',
     'events': ['SYSTEM_EVENT', 'NETWORK_EVENT']},
    {'control_id': 'A.12.6.1', 'title': 'Vulnerability Management', 'category': 'Operations Security',
     'events': ['CONTAINER_CRASH', 'SERVER_ERROR']},
    {'control_id': 'A.16.1.6', 'title': 'Incident Response', 'category': 'Information Security Incident Management',
     'events': ['BRUTE_FORCE_ATTEMPT', 'INCIDENT_CREATED']},
]

def import_compliance_data():
    from .models import ComplianceFramework, ComplianceControl
    
    frameworks = {
        'SOC2': SOC2_CONTROLS,
        'ISO27001': ISO27001_CONTROLS,
    }
    
    for fw_name, controls in frameworks.items():
        framework, _ = ComplianceFramework.objects.get_or_create(
            name=fw_name,
            defaults={'description': f'{fw_name} Compliance Framework'}
        )
        
        for ctrl in controls:
            ComplianceControl.objects.update_or_create(
                framework=framework,
                control_id=ctrl['control_id'],
                defaults={
                    'title': ctrl['title'],
                    'category': ctrl['category'],
                    'mapped_events': ctrl['events'],
                }
            )