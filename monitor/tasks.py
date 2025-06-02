from celery import shared_task
from .utils import check_website
from .models import MonitoredWebsite

@shared_task
def check_website_task(website_id):
    website = MonitoredWebsite.objects.get(id=website_id)
    check_website(website)
