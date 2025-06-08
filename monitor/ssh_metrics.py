import paramiko

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
            self.client.connect(hostname=self.host, port=self.port, username=self.username, pkey=pkey)
        else:
            self.client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password)

    def run_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode().strip()

    def collect_metrics(self):
        if not self.client:
            self.connect()

        # Zmienione: bardziej odporne komendy
        cpu_cmd = "top -bn1 | grep '%Cpu' | awk '{print 100 - $8}'"
        ram_total_cmd = "grep MemTotal /proc/meminfo | awk '{print int($2/1024)}'"
        ram_used_cmd = "free -m | awk '/Mem:/ {print $3}'"

        try:
            cpu = self.run_command(cpu_cmd)
            ram_total = self.run_command(ram_total_cmd)
            ram_used = self.run_command(ram_used_cmd)

            return {
                'cpu_percent': float(cpu),
                'ram_total': int(ram_total),
                'ram_used': int(ram_used)
            }
        except Exception as e:
            print("❌ Błąd podczas zbierania danych:", e)
            return {
                'cpu_percent': 0.0,
                'ram_total': 0,
                'ram_used': 0
            }

    def close(self):
        if self.client:
            self.client.close()
