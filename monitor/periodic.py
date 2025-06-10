from django_q.models import Schedule
from django_q.tasks import schedule


def start_ssh_monitoring_task():
    if not Schedule.objects.filter(name="ssh_metric_collector").exists():
        schedule(
    'monitor.ssh_metrics.collect_and_store_metrics',
    name='ssh_metric_collector',
    schedule_type='I',
    minutes=0.5,
    repeats=-1,
)

