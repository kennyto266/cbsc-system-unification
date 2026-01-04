"""
Mock psutil module for testing purposes
"""

def cpu_percent(interval=None):
    """Mock CPU usage"""
    return 25.0

def virtual_memory():
    """Mock virtual memory"""
    class MockMemory:
        def __init__(self):
            self.total = 16 * 1024 * 1024 * 1024  # 16GB
            self.available = 8 * 1024 * 1024 * 1024  # 8GB
            self.percent = 50.0

    return MockMemory()

def disk_usage(path):
    """Mock disk usage"""
    class MockDisk:
        def __init__(self):
            self.total = 500 * 1024 * 1024 * 1024  # 500GB
            self.free = 200 * 1024 * 1024 * 1024   # 200GB
            self.percent = 60.0

    return MockDisk()

def Process():
    """Mock Process class"""
    class MockProcess:
        def __init__(self, pid=None):
            self.pid = pid or 1234

        def memory_info(self):
            class MockMemInfo:
                rss = 100 * 1024 * 1024  # 100MB
                vms = 200 * 1024 * 1024  # 200MB
            return MockMemInfo()

        def cpu_percent(self):
            return 15.0

        def is_running(self):
            return True

    return MockProcess()

# Mock other common functions/classes
def pid_exists(pid):
    return True

def net_io_counters():
    class MockNetIO:
        bytes_sent = 1024 * 1024
        bytes_recv = 2 * 1024 * 1024
    return MockNetIO()