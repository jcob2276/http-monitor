from .ssh_metrics import SSHMonitor
from .models import SSHMetric

def collect_and_store_metrics():
    ssh = SSHMonitor(
        host='10.10.12.13',
        username='stud',
        password='stud'
    )
    
    try:
        metrics = ssh.collect_metrics()
        SSHMetric.objects.create(
            host=ssh.host,
            cpu_percent=metrics['cpu_percent'],
            ram_used=metrics['ram_used'],
            ram_total=metrics['ram_total']
        )
        print("✅ Metryki zapisane")
    except Exception as e:
        print(f"❌ Błąd zbierania metryk: {e}")
    finally:
        ssh.close()
