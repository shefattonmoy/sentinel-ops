# Create the directory structure first
# apps/agents/management/__init__.py
# apps/agents/management/commands/__init__.py

# apps/agents/management/commands/generate_agent_token.py
from django.core.management.base import BaseCommand
from apps.agents.models import Agent
from apps.agents.views import generate_token

class Command(BaseCommand):
    help = 'Generate a new token for an agent'

    def add_arguments(self, parser):
        parser.add_argument('agent_id', type=str, help='Agent ID')
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate token even if one exists',
        )

    def handle(self, *args, **options):
        agent_id = options['agent_id']
        regenerate = options['regenerate']
        
        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Agent with ID "{agent_id}" not found')
            )
            return
        
        if agent.token and not regenerate:
            self.stdout.write(
                self.style.WARNING(f'Agent already has a token: {agent.token}')
            )
            self.stdout.write('Use --regenerate to generate a new token')
            return
        
        agent.token = generate_token()
        agent.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'New token for agent {agent.name}: {agent.token}')
        )