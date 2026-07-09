# apps/mitre/importer.py
import requests
import logging

logger = logging.getLogger(__name__)

# MITRE ATT&CK Enterprise data (free JSON)
MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

# Event to MITRE technique mappings
EVENT_TECHNIQUE_MAP = {
    'FAILED_LOGIN': ('T1110', 'Brute Force', 0.9),
    'BRUTE_FORCE_ATTEMPT': ('T1110', 'Brute Force', 1.0),
    'SUCCESSFUL_LOGIN': ('T1078', 'Valid Accounts', 0.7),
    'SUDO_COMMAND': ('T1548', 'Abuse Elevation Control Mechanism', 0.9),
    'USER_CREATED': ('T1136', 'Create Account', 0.9),
    'USER_DELETED': ('T1531', 'Account Access Removal', 0.8),
    'ACCESS_DENIED': ('T1087', 'Account Discovery', 0.6),
    'SERVER_ERROR': ('T1499', 'Endpoint Denial of Service', 0.5),
    'CONTAINER_CRASH': ('T1499', 'Endpoint Denial of Service', 0.6),
    'CONTAINER_OOM': ('T1498', 'Network Denial of Service', 0.5),
    'OOM_KILLER': ('T1498', 'Network Denial of Service', 0.7),
    'NGINX_ERROR': ('T1499', 'Endpoint Denial of Service', 0.5),
    'DJANGO_ERROR': ('T1499', 'Endpoint Denial of Service', 0.4),
    'INVALID_USER': ('T1087', 'Account Discovery', 0.7),
    'CONTAINER_RESTART': ('T1498', 'Network Denial of Service', 0.5),
    'KERNEL_PANIC': ('T1498', 'Network Denial of Service', 0.8),
    'SERVICE_FAILURE': ('T1489', 'Service Stop', 0.7),
    'DISK_ERROR': ('T1485', 'Data Destruction', 0.6),
    'NETWORK_EVENT': ('T1040', 'Network Sniffing', 0.4),
    'DATABASE_QUERY': ('T1213', 'Data from Information Repositories', 0.5),
    'DJANGO_WARNING': ('T1499', 'Endpoint Denial of Service', 0.3),
}

def import_mitre_data():
    """Import MITRE ATT&CK data"""
    from .models import MitreTechnique
    
    try:
        response = requests.get(MITRE_URL, timeout=30)
        data = response.json()
        
        count = 0
        for obj in data.get('objects', []):
            if obj.get('type') == 'attack-pattern' and not obj.get('revoked', False):
                for ref in obj.get('external_references', []):
                    if ref.get('source_name') == 'mitre-attack':
                        technique_id = ref.get('external_id', '')
                        if technique_id.startswith('T'):
                            # Get tactic from kill chain phases
                            tactics = [p.get('phase_name', '') for p in obj.get('kill_chain_phases', [])]
                            tactic = tactics[0] if tactics else 'Unknown'
                            
                            MitreTechnique.objects.update_or_create(
                                technique_id=technique_id,
                                defaults={
                                    'name': obj.get('name', ''),
                                    'description': obj.get('description', '')[:500],
                                    'tactic': tactic,
                                    'platform': ', '.join(obj.get('x_mitre_platforms', [])),
                                    'data_sources': obj.get('x_mitre_data_sources', []),
                                }
                            )
                            count += 1
        
        logger.info(f"Imported {count} MITRE techniques")
        return count
    except Exception as e:
        logger.error(f"Failed to import MITRE data: {e}")
        return 0

def import_event_mappings():
    """Import event-to-technique mappings"""
    from .models import EventTechniqueMapping, MitreTechnique
    
    count = 0
    for event_type, (technique_id, name, confidence) in EVENT_TECHNIQUE_MAP.items():
        try:
            technique = MitreTechnique.objects.get(technique_id=technique_id)
            EventTechniqueMapping.objects.update_or_create(
                event_type=event_type,
                defaults={
                    'technique': technique,
                    'confidence': confidence,
                }
            )
            count += 1
        except MitreTechnique.DoesNotExist:
            pass
    
    return count