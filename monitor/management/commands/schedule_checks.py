from django.core.management.base import BaseCommand
from django_q.models import Schedule

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Schedule.objects.update_or_create(
            name='Scheduled Website Check',
            func='monitor.tasks.check_all_websites',
            schedule_type=Schedule.MINUTES,
            minutes=5
        )
