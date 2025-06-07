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

        cpu = self.run_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
        ram_total = self.run_command("free -m | awk '/Mem:/ {print $2}'")
        ram_used = self.run_command("free -m | awk '/Mem:/ {print $3}'")

        return {
            'cpu_percent': float(cpu),
            'ram_total': int(ram_total),
            'ram_used': int(ram_used)
        }

    def close(self):
        if self.client:
            self.client.close()
