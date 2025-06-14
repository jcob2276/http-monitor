import paramiko
from .models import SSHHost, SSHMetric
import paramiko
from .models import SSHHost, SSHMetric

# -----------------------------
# Klasa do monitorowania przez SSH
# -----------------------------
class SSHMonitor:
    def __init__(self, host, username, password=None, port=22, key_path=None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.key_path = key_path
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.key_path:
            pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                pkey=pkey
            )
        else:
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )

    def run_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode().strip()
    
    def collect_metrics(self):
        if not self.client:
            self.connect()
        commands = {
            'cpu_percent': "top -bn1 | grep 'Cpu(s)' | sed 's/,/\\n/g' | grep 'id' | awk '{print 100 - $1}'",
            'ram_total': "grep MemTotal /proc/meminfo | awk '{print int($2/1024)}'",
            'ram_used': "free -m | awk '/Mem:/ {print $3}'",
        }
        results = {}
        try:
            for key, cmd in commands.items():
                output = self.run_command(cmd)
                print(f"[DEBUG] {self.host} | {key}: '{output}'")
                if not output:
                    raise ValueError(f"Brak wyniku dla {key}")
                if "cpu" in key:
                    results[key] = float(output)
                else:
                    results[key] = int(output)
            return results
        except Exception as e:
            print(f"❌ Błąd zbierania metryk z {self.host}: {e}")
            return {'cpu_percent': 0.0, 'ram_total': 0, 'ram_used': 0}

    def close(self):
        if self.client:
            self.client.close()

# -----------------------------
# Funkcja cyklicznego zbierania metryk
# -----------------------------
def collect_and_store_metrics():
    """
    Iteruje po wszystkich hostach SSH i zapisuje metryki do bazy.
    """
    for host_obj in SSHHost.objects.all():
        ssh = SSHMonitor(
            host=host_obj.hostname,
            username=host_obj.username,
            password=host_obj.password  
        )

        try:
            metrics = ssh.collect_metrics()
            SSHMetric.objects.create(
                host=host_obj,
                cpu_percent=metrics['cpu_percent'],
                ram_used=metrics['ram_used'],
                ram_total=metrics['ram_total']
            )
            print(f"✅ Metryki zapisane dla {host_obj.hostname}")

        except Exception as e:
            print(f"❌ Błąd – host: {host_obj.hostname} → {e}")

        finally:
            ssh.close()
