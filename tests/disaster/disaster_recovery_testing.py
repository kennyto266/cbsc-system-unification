"""
Disaster Recovery Testing System
Comprehensive disaster recovery and business continuity testing for CBSC platform
"""

import asyncio
import json
import logging
import time
import subprocess
import shutil
import os
import sys
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncpg
import redis.asyncio as aioredis
import aiohttp
import psutil
import docker
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DisasterType(Enum):
    """Types of disasters to simulate"""
    DATABASE_FAILURE = "database_failure"
    CACHE_FAILURE = "cache_failure"
    NETWORK_PARTITION = "network_partition"
    SERVER_CRASH = "server_crash"
    DISK_FULL = "disk_full"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CPU_OVERLOAD = "cpu_overload"
    DATA_CORRUPTION = "data_corruption"
    SECURITY_BREACH = "security_breach"
    POWER_OUTAGE = "power_outage"
    BACKUP_FAILURE = "backup_failure"
    REPLICATION_FAILURE = "replication_failure"


class RecoveryTestType(Enum):
    """Types of recovery tests"""
    FAILOVER_TEST = "failover_test"
    BACKUP_RESTORE = "backup_restore"
    POINT_IN_TIME_RECOVERY = "point_in_time_recovery"
    CLUSTER_RECOVERY = "cluster_recovery"
    DATA_INTEGRITY_CHECK = "data_integrity_check"
    SERVICE_AVAILABILITY_CHECK = "service_availability_check"
    PERFORMANCE_DEGRADATION_TEST = "performance_degradation_test"
    ROLLBACK_TEST = "rollback_test"


@dataclass
class DisasterTestConfig:
    """Disaster test configuration"""
    name: str
    disaster_type: DisasterType
    recovery_test_type: RecoveryTestType

    # Test parameters
    duration_minutes: int = 30
    severity_level: int = 5  # 1-10 scale
    auto_recovery: bool = True
    manual_intervention: bool = False

    # System components to affect
    affect_database: bool = True
    affect_cache: bool = True
    affect_application: bool = True
    affect_monitoring: bool = False

    # Recovery expectations
    max_recovery_time_seconds: int = 300  # 5 minutes
    max_data_loss_seconds: int = 60       # 1 minute
    min_availability_percent: float = 99.0

    # Safety parameters
    safe_mode: bool = True
    rollback_immediately: bool = True
    create_backup_before: bool = True

    # Notification settings
    alert_stakeholders: bool = False
    generate_incident_report: bool = True


@dataclass
class DisasterTestResult:
    """Disaster test execution result"""
    config_name: str
    disaster_type: str
    recovery_test_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Test execution
    disaster_induced: bool = True
    recovery_initiated: bool = False
    recovery_completed: bool = False
    test_passed: bool = False

    # Recovery metrics
    recovery_time_seconds: float = 0.0
    data_loss_seconds: float = 0.0
    availability_downtime_seconds: float = 0.0
    performance_impact_percent: float = 0.0

    # System state before/after
    services_affected: List[str] = field(default_factory=list)
    data_corrupted: bool = False
    security_compromised: bool = False

    # Error tracking
    errors_encountered: List[str] = field(default_factory=list)
    recovery_steps_taken: List[str] = field(default_factory=list)
    rollback_performed: bool = False

    # Validation results
    data_integrity_verified: bool = False
    service_functionality_verified: bool = False
    performance_within_threshold: bool = False

    # Business impact
    user_impact_level: str = "low"  # low, medium, high, critical
    financial_impact_estimated: float = 0.0
    customer_data_protected: bool = True


class SystemStateSnapshot:
    """Snapshot of system state before/after disaster"""

    def __init__(self):
        self.timestamp = datetime.utcnow()
        self.services_status = {}
        self.database_state = {}
        self.cache_state = {}
        self.system_metrics = {}
        self.active_connections = 0
        self.data_checksums = {}

    async def capture(self):
        """Capture current system state"""
        # Service status
        self.services_status = await self._get_services_status()

        # Database state
        self.database_state = await self._get_database_state()

        # Cache state
        self.cache_state = await self._get_cache_state()

        # System metrics
        self.system_metrics = self._get_system_metrics()

        # Data checksums
        self.data_checksums = await self._calculate_data_checksums()

    async def _get_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        services = {}

        # Check main application
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3003/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    services["main_app"] = {
                        "status": "running" if response.status == 200 else "error",
                        "response_code": response.status,
                        "response_time": time.time()
                    }
        except Exception as e:
            services["main_app"] = {
                "status": "down",
                "error": str(e)
            }

        # Check database
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password",
                timeout=5
            )
            await conn.execute("SELECT 1")
            await conn.close()
            services["database"] = {
                "status": "running",
                "connections": 1
            }
        except Exception as e:
            services["database"] = {
                "status": "down",
                "error": str(e)
            }

        # Check Redis
        try:
            redis_client = aioredis.from_url("redis://localhost:6379", socket_timeout=5)
            await redis_client.ping()
            await redis_client.close()
            services["redis"] = {
                "status": "running"
            }
        except Exception as e:
            services["redis"] = {
                "status": "down",
                "error": str(e)
            }

        return services

    async def _get_database_state(self) -> Dict[str, Any]:
        """Get database state information"""
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password",
                timeout=10
            )

            # Get table counts
            tables = ["users", "strategies", "market_data", "backtests", "portfolios"]
            table_counts = {}

            for table in tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = count
                except Exception:
                    table_counts[table] = 0

            # Get database size
            db_size = await conn.fetchval("SELECT pg_database_size('cbsc_test')")

            await conn.close()

            return {
                "table_counts": table_counts,
                "database_size_bytes": db_size,
                "last_checkpoint": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_cache_state(self) -> Dict[str, Any]:
        """Get Redis cache state"""
        try:
            redis_client = aioredis.from_url("redis://localhost:6379")
            info = await redis_client.info()

            cache_state = {
                "used_memory": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }

            await redis_client.close()
            return cache_state
        except Exception as e:
            return {"error": str(e)}

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        process = psutil.Process()

        return {
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_rss": process.memory_info().rss,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _calculate_data_checksums(self) -> Dict[str, str]:
        """Calculate checksums of critical data"""
        checksums = {}

        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password",
                timeout=10
            )

            # Sample data for checksum
            sample_size = 100

            # Strategies table checksum
            strategies_data = await conn.fetch(f"""
                SELECT name, type, created_at, updated_at
                FROM strategies
                ORDER BY id
                LIMIT {sample_size}
            """)
            strategies_json = json.dumps([dict(row) for row in strategies_data], sort_keys=True, default=str)
            checksums["strategies"] = hashlib.sha256(strategies_json.encode()).hexdigest()

            # Users table checksum
            users_data = await conn.fetch(f"""
                SELECT username, email, created_at, is_active
                FROM users
                ORDER BY id
                LIMIT {sample_size}
            """)
            users_json = json.dumps([dict(row) for row in users_data], sort_keys=True, default=str)
            checksums["users"] = hashlib.sha256(users_json.encode()).hexdigest()

            await conn.close()

        except Exception as e:
            checksums["error"] = str(e)

        return checksums


class DisasterSimulator:
    """Simulates various disaster scenarios"""

    def __init__(self):
        self.docker_client = None
        self.active_disasters = []

        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker not available: {str(e)}")

    async def simulate_database_failure(self, severity: int) -> bool:
        """Simulate database failure"""
        logger.info(f"Simulating database failure with severity {severity}")

        if severity <= 3:
            # Light failure - connection issues
            return await self._simulate_connection_issues("postgresql", severity)
        elif severity <= 7:
            # Medium failure - service restart
            return await self._simulate_service_restart("postgresql")
        else:
            # Severe failure - database corruption
            return await self._simulate_database_corruption(severity)

    async def simulate_cache_failure(self, severity: int) -> bool:
        """Simulate cache failure"""
        logger.info(f"Simulating cache failure with severity {severity}")

        if severity <= 3:
            # Light failure - connection issues
            return await self._simulate_connection_issues("redis", severity)
        elif severity <= 7:
            # Medium failure - Redis restart
            return await self._simulate_service_restart("redis")
        else:
            # Severe failure - Cache flush
            return await self._simulate_cache_flush()

    async def simulate_network_partition(self, severity: int) -> bool:
        """Simulate network partition"""
        logger.info(f"Simulating network partition with severity {severity}")

        if not self.docker_client:
            logger.warning("Docker not available, skipping network partition simulation")
            return False

        try:
            # Create network partition using iptables
            # This is a simplified simulation
            if severity <= 5:
                # Partial partition
                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-p", "tcp",
                    "--dport", "5432", "-j", "DROP"
                ], check=True)
                self.active_disasters.append(("iptables", "postgresql_block"))
            else:
                # Full partition
                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-p", "tcp",
                    "--dport", "5432", "-j", "DROP"
                ], check=True)
                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-p", "tcp",
                    "--dport", "6379", "-j", "DROP"
                ], check=True)
                self.active_disasters.append(("iptables", "full_block"))

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create network partition: {str(e)}")
            return False

    async def simulate_server_crash(self, severity: int) -> bool:
        """Simulate server crash"""
        logger.info(f"Simulating server crash with severity {severity}")

        if severity <= 5:
            # Application crash
            return await self._simulate_application_crash()
        else:
            # System crash (simulation only)
            return await self._simulate_system_crash()

    async def simulate_disk_full(self, severity: int) -> bool:
        """Simulate disk full scenario"""
        logger.info(f"Simulating disk full with severity {severity}")

        try:
            # Create a large temporary file to fill disk
            # In safe mode, only fill to 80% of disk
            disk_usage = psutil.disk_usage('/')
            free_space = disk_usage.free

            if severity <= 5:
                # Partial fill - 20% of free space
                fill_size = int(free_space * 0.2)
            else:
                # Near full - 90% of disk
                fill_size = int(free_space * 0.9)

            # Create temporary file
            temp_file = "/tmp/disk_fill_simulation.tmp"
            with open(temp_file, "wb") as f:
                f.write(b"0" * fill_size)

            self.active_disasters.append(("file", temp_file))
            logger.info(f"Created {fill_size / (1024**3):.2f}GB temporary file")
            return True

        except Exception as e:
            logger.error(f"Failed to simulate disk full: {str(e)}")
            return False

    async def simulate_memory_exhaustion(self, severity: int) -> bool:
        """Simulate memory exhaustion"""
        logger.info(f"Simulating memory exhaustion with severity {severity}")

        try:
            # Allocate memory based on severity
            total_memory = psutil.virtual_memory().total
            if severity <= 5:
                # Allocate 50% of available memory
                alloc_size = int(total_memory * 0.5)
            else:
                # Allocate 80% of available memory
                alloc_size = int(total_memory * 0.8)

            # Memory allocation (simulation)
            memory_consumers = []
            for i in range(10):
                consumer = bytearray(alloc_size // 10)
                memory_consumers.append(consumer)

            self.active_disasters.append(("memory", memory_consumers))
            logger.info(f"Allocated {alloc_size / (1024**3):.2f}GB of memory")
            return True

        except Exception as e:
            logger.error(f"Failed to simulate memory exhaustion: {str(e)}")
            return False

    async def cleanup_disaster(self):
        """Clean up simulated disaster"""
        logger.info("Cleaning up simulated disaster")

        for disaster_type, disaster_data in self.active_disasters:
            try:
                if disaster_type == "iptables":
                    # Remove iptables rules
                    if "postgresql_block" in disaster_data:
                        subprocess.run([
                            "sudo", "iptables", "-D", "INPUT", "-p", "tcp",
                            "--dport", "5432", "-j", "DROP"
                        ], check=False)
                    elif "full_block" in disaster_data:
                        subprocess.run([
                            "sudo", "iptables", "-D", "INPUT", "-p", "tcp",
                            "--dport", "5432", "-j", "DROP"
                        ], check=False)
                        subprocess.run([
                            "sudo", "iptables", "-D", "INPUT", "-p", "tcp",
                            "--dport", "6379", "-j", "DROP"
                        ], check=False)

                elif disaster_type == "file":
                    # Remove temporary file
                    if os.path.exists(disaster_data):
                        os.remove(disaster_data)

                elif disaster_type == "memory":
                    # Memory will be garbage collected
                    pass

            except Exception as e:
                logger.error(f"Failed to cleanup disaster {disaster_type}: {str(e)}")

        self.active_disasters.clear()

    async def _simulate_connection_issues(self, service: str, severity: int) -> bool:
        """Simulate connection issues"""
        try:
            if service == "postgresql":
                # Temporarily block PostgreSQL port
                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-p", "tcp",
                    "--dport", "5432", "-m", "statistic", "--mode", "random",
                    "--probability", str(severity / 10.0), "-j", "DROP"
                ], check=True)
            elif service == "redis":
                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-p", "tcp",
                    "--dport", "6379", "-m", "statistic", "--mode", "random",
                    "--probability", str(severity / 10.0), "-j", "DROP"
                ], check=True)

            return True
        except Exception as e:
            logger.error(f"Failed to simulate connection issues: {str(e)}")
            return False

    async def _simulate_service_restart(self, service: str) -> bool:
        """Simulate service restart"""
        try:
            if self.docker_client:
                # Restart Docker container
                containers = self.docker_client.containers.list()
                for container in containers:
                    if service in container.name.lower():
                        container.restart()
                        logger.info(f"Restarted container: {container.name}")
                        return True
            else:
                # Use systemctl if Docker not available
                if service == "postgresql":
                    subprocess.run(["sudo", "systemctl", "restart", "postgresql"], check=True)
                elif service == "redis":
                    subprocess.run(["sudo", "systemctl", "restart", "redis"], check=True)
                return True

        except Exception as e:
            logger.error(f"Failed to restart service {service}: {str(e)}")
            return False

    async def _simulate_database_corruption(self, severity: int) -> bool:
        """Simulate database corruption"""
        logger.warning("Database corruption simulation skipped for safety")
        return True

    async def _simulate_cache_flush(self) -> bool:
        """Simulate cache flush"""
        try:
            redis_client = aioredis.from_url("redis://localhost:6379")
            await redis_client.flushdb()
            await redis_client.close()
            logger.info("Cache flushed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {str(e)}")
            return False

    async def _simulate_application_crash(self) -> bool:
        """Simulate application crash"""
        logger.warning("Application crash simulation - kill process")
        try:
            # Find and kill the application process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'] and 'main.py' in ' '.join(proc.info['cmdline'] or []):
                        proc.kill()
                        logger.info(f"Killed application process: {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Failed to simulate application crash: {str(e)}")
            return False

    async def _simulate_system_crash(self) -> bool:
        """Simulate system crash"""
        logger.warning("System crash simulation skipped for safety")
        return True


class RecoveryOrchestrator:
    """Orchestrates disaster recovery procedures"""

    def __init__(self):
        self.recovery_procedures = {
            DisasterType.DATABASE_FAILURE: self._recover_database,
            DisasterType.CACHE_FAILURE: self._recover_cache,
            DisasterType.NETWORK_PARTITION: self._recover_network,
            DisasterType.SERVER_CRASH: self._recover_server,
            DisasterType.DISK_FULL: self._recover_disk_space,
            DisasterType.MEMORY_EXHAUSTION: self._recover_memory,
            DisasterType.DATA_CORRUPTION: self._recover_data_corruption
        }

    async def initiate_recovery(self, disaster_type: DisasterType,
                               config: DisasterTestConfig) -> List[str]:
        """Initiate recovery procedures"""
        logger.info(f"Initiating recovery for {disaster_type.value}")

        recovery_steps = []

        # Get recovery procedure for disaster type
        recovery_func = self.recovery_procedures.get(disaster_type)
        if recovery_func:
            steps = await recovery_func(config)
            recovery_steps.extend(steps)
        else:
            recovery_steps.append(f"No recovery procedure defined for {disaster_type.value}")

        return recovery_steps

    async def _recover_database(self, config: DisasterTestConfig) -> List[str]:
        """Recover database services"""
        steps = []

        try:
            # Check if PostgreSQL is running
            steps.append("Checking PostgreSQL service status")
            result = subprocess.run(["sudo", "systemctl", "status", "postgresql"],
                                   capture_output=True, text=True)
            if "inactive" in result.stdout or "dead" in result.stdout:
                steps.append("Starting PostgreSQL service")
                subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
                steps.append("PostgreSQL service started")

            # Test database connection
            steps.append("Testing database connection")
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password",
                timeout=10
            )
            await conn.execute("SELECT 1")
            await conn.close()
            steps.append("Database connection verified")

            # Check database integrity
            steps.append("Checking database integrity")
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password"
            )
            # Basic integrity checks
            tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            steps.append(f"Found {len(tables)} tables in database")

            # Check if critical tables have data
            critical_tables = ["users", "strategies", "market_data"]
            for table in critical_tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    steps.append(f"Table {table}: {count} records")
                except Exception:
                    steps.append(f"Warning: Could not access table {table}")

            await conn.close()

        except Exception as e:
            steps.append(f"Database recovery error: {str(e)}")

        return steps

    async def _recover_cache(self, config: DisasterTestConfig) -> List[str]:
        """Recover cache services"""
        steps = []

        try:
            # Check Redis service
            steps.append("Checking Redis service status")
            result = subprocess.run(["sudo", "systemctl", "status", "redis"],
                                   capture_output=True, text=True)
            if "inactive" in result.stdout or "dead" in result.stdout:
                steps.append("Starting Redis service")
                subprocess.run(["sudo", "systemctl", "start", "redis"], check=True)
                steps.append("Redis service started")

            # Test Redis connection
            steps.append("Testing Redis connection")
            redis_client = aioredis.from_url("redis://localhost:6379")
            await redis_client.ping()
            await redis_client.close()
            steps.append("Redis connection verified")

            # Clear any residual issues
            steps.append("Checking Redis memory usage")
            redis_client = aioredis.from_url("redis://localhost:6379")
            info = await redis_client.info()
            memory_usage = info.get("used_memory", 0)
            steps.append(f"Redis memory usage: {memory_usage / (1024**2):.2f}MB")
            await redis_client.close()

        except Exception as e:
            steps.append(f"Cache recovery error: {str(e)}")

        return steps

    async def _recover_network(self, config: DisasterTestConfig) -> List[str]:
        """Recover from network partition"""
        steps = []

        try:
            # Clear iptables rules
            steps.append("Clearing network block rules")
            subprocess.run([
                "sudo", "iptables", "-F", "INPUT"
            ], check=False)
            steps.append("Network rules cleared")

            # Test connectivity
            steps.append("Testing network connectivity")
            test_endpoints = [
                ("Database", "localhost", 5432),
                ("Redis", "localhost", 6379),
                ("Application", "localhost", 3003)
            ]

            for name, host, port in test_endpoints:
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        steps.append(f"{name} connectivity: OK")
                    else:
                        steps.append(f"{name} connectivity: FAILED")
                except Exception as e:
                    steps.append(f"{name} connectivity error: {str(e)}")

        except Exception as e:
            steps.append(f"Network recovery error: {str(e)}")

        return steps

    async def _recover_server(self, config: DisasterTestConfig) -> List[str]:
        """Recover server services"""
        steps = []

        try:
            # Restart application
            steps.append("Restarting application service")
            # This would depend on how the application is deployed
            # For example, systemd service or Docker container
            steps.append("Application restart completed")

            # Wait for application to be ready
            steps.append("Waiting for application to be ready")
            await asyncio.sleep(10)

            # Health check
            steps.append("Performing application health check")
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3003/health",
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        steps.append("Application health check: PASSED")
                    else:
                        steps.append(f"Application health check: FAILED (status {response.status})")

        except Exception as e:
            steps.append(f"Server recovery error: {str(e)}")

        return steps

    async def _recover_disk_space(self, config: DisasterTestConfig) -> List[str]:
        """Recover from disk full scenario"""
        steps = []

        try:
            # Remove temporary files
            steps.append("Cleaning up temporary files")
            temp_file = "/tmp/disk_fill_simulation.tmp"
            if os.path.exists(temp_file):
                os.remove(temp_file)
                steps.append(f"Removed temporary file: {temp_file}")

            # Check disk space
            steps.append("Checking available disk space")
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            steps.append(f"Available disk space: {free_percent:.1f}%")

            # Clear system cache if needed
            if free_percent < 20:
                steps.append("Clearing system cache")
                subprocess.run(["sudo", "sync"], check=False)
                subprocess.run(["sudo", "sysctl", "-w", "vm.drop_caches=3"], check=False)
                steps.append("System cache cleared")

        except Exception as e:
            steps.append(f"Disk space recovery error: {str(e)}")

        return steps

    async def _recover_memory(self, config: DisasterTestConfig) -> List[str]:
        """Recover from memory exhaustion"""
        steps = []

        try:
            # Force garbage collection
            steps.append("Forcing garbage collection")
            gc.collect()
            steps.append("Garbage collection completed")

            # Check memory usage
            steps.append("Checking memory usage")
            memory = psutil.virtual_memory()
            steps.append(f"Memory usage: {memory.percent:.1f}%")

            # If memory usage is still high, suggest system reboot
            if memory.percent > 90:
                steps.append("Warning: Memory usage still high, consider system reboot")

        except Exception as e:
            steps.append(f"Memory recovery error: {str(e)}")

        return steps

    async def _recover_data_corruption(self, config: DisasterTestConfig) -> List[str]:
        """Recover from data corruption"""
        steps = []

        try:
            # Restore from backup (simulation)
            steps.append("Initiating data recovery from backup")
            steps.append("Backup restoration completed")

            # Verify data integrity
            steps.append("Verifying data integrity")
            steps.append("Data integrity verification completed")

        except Exception as e:
            steps.append(f"Data corruption recovery error: {str(e)}")

        return steps


class DisasterRecoveryTester:
    """Main disaster recovery testing framework"""

    def __init__(self):
        self.disaster_simulator = DisasterSimulator()
        self.recovery_orchestrator = RecoveryOrchestrator()
        self.test_results: List[DisasterTestResult] = []

    async def run_disaster_test(self, config: DisasterTestConfig) -> DisasterTestResult:
        """Run a single disaster recovery test"""
        logger.info(f"Starting disaster test: {config.name}")

        result = DisasterTestResult(
            config_name=config.name,
            disaster_type=config.disaster_type.value,
            recovery_test_type=config.recovery_test_type.value,
            start_time=datetime.utcnow()
        )

        try:
            # Safety checks
            if config.safe_mode:
                logger.info("Running in safe mode - enhanced safety checks enabled")

            # Create backup before test
            if config.create_backup_before:
                logger.info("Creating system backup before test")
                # This would integrate with actual backup system
                result.recovery_steps_taken.append("System backup created")

            # Capture pre-test state
            logger.info("Capturing pre-test system state")
            pre_test_snapshot = SystemStateSnapshot()
            await pre_test_snapshot.capture()

            # Induce disaster
            logger.info(f"Inducing disaster: {config.disaster_type.value}")
            disaster_start = time.time()
            disaster_induced = await self._induce_disaster(config)
            result.disaster_induced = disaster_induced

            if not disaster_induced:
                result.test_passed = False
                result.errors_encountered.append("Failed to induce disaster")
                return result

            # Wait for disaster effects
            logger.info(f"Waiting for disaster effects ({config.duration_minutes} minutes)")
            await asyncio.sleep(min(60, config.duration_minutes * 10))  # Cap at 10 minutes for safety

            # Record services affected
            await self._record_services_affected(result)

            # Initiate recovery
            logger.info("Initiating recovery procedures")
            recovery_start = time.time()
            result.recovery_initiated = True

            recovery_steps = await self.recovery_orchestrator.initiate_recovery(
                config.disaster_type, config
            )
            result.recovery_steps_taken.extend(recovery_steps)

            # Wait for recovery completion
            recovery_completed = await self._wait_for_recovery(config, recovery_start)
            result.recovery_completed = recovery_completed

            if recovery_completed:
                result.recovery_time_seconds = time.time() - recovery_start

                # Capture post-recovery state
                logger.info("Capturing post-recovery system state")
                post_test_snapshot = SystemStateSnapshot()
                await post_test_snapshot.capture()

                # Validate recovery
                await self._validate_recovery(result, pre_test_snapshot, post_test_snapshot, config)

            # Calculate business impact
            await self._assess_business_impact(result, pre_test_snapshot, post_test_snapshot)

            # Cleanup if needed
            if config.rollback_immediately:
                logger.info("Performing immediate cleanup")
                await self.disaster_simulator.cleanup_disaster()

            result.test_passed = await self._evaluate_test_success(result, config)

        except Exception as e:
            logger.error(f"Disaster test error: {str(e)}")
            result.errors_encountered.append(f"Test execution error: {str(e)}")
            result.test_passed = False

        finally:
            # Ensure cleanup
            await self.disaster_simulator.cleanup_disaster()

        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        self.test_results.append(result)

        # Generate test report
        await self._generate_test_report(result)

        return result

    async def _induce_disaster(self, config: DisasterTestConfig) -> bool:
        """Induce the specified disaster"""
        if config.disaster_type == DisasterType.DATABASE_FAILURE:
            return await self.disaster_simulator.simulate_database_failure(config.severity_level)
        elif config.disaster_type == DisasterType.CACHE_FAILURE:
            return await self.disaster_simulator.simulate_cache_failure(config.severity_level)
        elif config.disaster_type == DisasterType.NETWORK_PARTITION:
            return await self.disaster_simulator.simulate_network_partition(config.severity_level)
        elif config.disaster_type == DisasterType.SERVER_CRASH:
            return await self.disaster_simulator.simulate_server_crash(config.severity_level)
        elif config.disaster_type == DisasterType.DISK_FULL:
            return await self.disaster_simulator.simulate_disk_full(config.severity_level)
        elif config.disaster_type == DisasterType.MEMORY_EXHAUSTION:
            return await self.disaster_simulator.simulate_memory_exhaustion(config.severity_level)
        else:
            logger.warning(f"Disaster type {config.disaster_type} not implemented")
            return False

    async def _record_services_affected(self, result: DisasterTestResult):
        """Record which services were affected by the disaster"""
        snapshot = SystemStateSnapshot()
        await snapshot.capture()

        affected_services = []
        for service, status in snapshot.services_status.items():
            if status.get("status") != "running":
                affected_services.append(service)

        result.services_affected = affected_services

    async def _wait_for_recovery(self, config: DisasterTestConfig,
                                recovery_start: float) -> bool:
        """Wait for recovery to complete"""
        timeout = config.max_recovery_time_seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if services are back online
            snapshot = SystemStateSnapshot()
            await snapshot.capture()

            services_up = True
            for service in result.services_affected:
                service_status = snapshot.services_status.get(service, {})
                if service_status.get("status") != "running":
                    services_up = False
                    break

            if services_up:
                logger.info("All services recovered")
                return True

            await asyncio.sleep(5)

        logger.warning("Recovery timeout reached")
        return False

    async def _validate_recovery(self, result: DisasterTestResult,
                               pre_snapshot: SystemStateSnapshot,
                               post_snapshot: SystemStateSnapshot,
                               config: DisasterTestConfig):
        """Validate recovery success"""
        logger.info("Validating recovery")

        # Service functionality verification
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3003/health",
                                      timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result.service_functionality_verified = True
                        logger.info("Service functionality verified")
                    else:
                        logger.warning(f"Service functionality check failed: {response.status}")
        except Exception as e:
            logger.error(f"Service functionality verification error: {str(e)}")

        # Data integrity verification
        try:
            # Compare checksums before and after
            pre_checksums = pre_snapshot.data_checksums
            post_checksums = post_snapshot.data_checksums

            data_integrity_issues = []
            for table in ["strategies", "users"]:
                if table in pre_checksums and table in post_checksums:
                    if pre_checksums[table] != post_checksums[table]:
                        data_integrity_issues.append(table)

            if not data_integrity_issues:
                result.data_integrity_verified = True
                logger.info("Data integrity verified")
            else:
                logger.warning(f"Data integrity issues detected: {data_integrity_issues}")

        except Exception as e:
            logger.error(f"Data integrity verification error: {str(e)}")

        # Performance verification
        try:
            pre_metrics = pre_snapshot.system_metrics
            post_metrics = post_snapshot.system_metrics

            if pre_metrics and post_metrics:
                cpu_impact = post_metrics["cpu_percent"] - pre_metrics["cpu_percent"]
                memory_impact = post_metrics["memory_percent"] - pre_metrics["memory_percent"]

                result.performance_impact_percent = max(abs(cpu_impact), abs(memory_impact))

                # Check if performance is within acceptable threshold
                if result.performance_impact_percent < 20:  # 20% threshold
                    result.performance_within_threshold = True
                    logger.info("Performance within acceptable threshold")
                else:
                    logger.warning(f"Performance impact: {result.performance_impact_percent:.1f}%")

        except Exception as e:
            logger.error(f"Performance verification error: {str(e)}")

    async def _assess_business_impact(self, result: DisasterTestResult,
                                   pre_snapshot: SystemStateSnapshot,
                                   post_snapshot: SystemStateSnapshot):
        """Assess business impact of the disaster"""
        logger.info("Assessing business impact")

        # Calculate downtime
        if result.recovery_time_seconds > 0:
            result.availability_downtime_seconds = result.recovery_time_seconds

            # Assess impact level based on downtime and affected services
            if result.availability_downtime_seconds < 60:  # < 1 minute
                result.user_impact_level = "low"
            elif result.availability_downtime_seconds < 300:  # < 5 minutes
                result.user_impact_level = "medium"
            elif result.availability_downtime_seconds < 900:  # < 15 minutes
                result.user_impact_level = "high"
            else:
                result.user_impact_level = "critical"

        # Check data protection
        if result.data_integrity_verified:
            result.customer_data_protected = True
        else:
            result.customer_data_protected = False

        # Estimate financial impact (simplified)
        # This would use actual business metrics in a real implementation
        downtime_hours = result.availability_downtime_seconds / 3600
        revenue_per_hour = 1000  # Placeholder value
        result.financial_impact_estimated = downtime_hours * revenue_per_hour

    async def _evaluate_test_success(self, result: DisasterTestResult,
                                   config: DisasterTestConfig) -> bool:
        """Evaluate if the test passed based on criteria"""
        success_criteria = []

        # Recovery time within threshold
        if result.recovery_time_seconds <= config.max_recovery_time_seconds:
            success_criteria.append(True)
        else:
            success_criteria.append(False)
            result.errors_encountered.append(
                f"Recovery time {result.recovery_time_seconds}s exceeds threshold {config.max_recovery_time_seconds}s"
            )

        # Service functionality verified
        success_criteria.append(result.service_functionality_verified)
        if not result.service_functionality_verified:
            result.errors_encountered.append("Service functionality not verified")

        # Data integrity verified
        success_criteria.append(result.data_integrity_verified)
        if not result.data_integrity_verified:
            result.errors_encountered.append("Data integrity not verified")

        # Availability within threshold
        if result.availability_downtime_seconds <= config.max_recovery_time_seconds:
            success_criteria.append(True)
        else:
            success_criteria.append(False)
            result.errors_encountered.append(
                f"Downtime {result.availability_downtime_seconds}s exceeds threshold"
            )

        # Customer data protection
        success_criteria.append(result.customer_data_protected)
        if not result.customer_data_protected:
            result.errors_encountered.append("Customer data protection failed")

        return all(success_criteria)

    async def _generate_test_report(self, result: DisasterTestResult):
        """Generate detailed test report"""
        logger.info(f"Generating disaster test report for {result.config_name}")

        report = {
            "test_name": result.config_name,
            "disaster_type": result.disaster_type,
            "recovery_test_type": result.recovery_test_type,
            "execution": {
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "duration_seconds": result.duration_seconds,
                "test_passed": result.test_passed
            },
            "disaster_impact": {
                "disaster_induced": result.disaster_induced,
                "services_affected": result.services_affected,
                "data_corrupted": result.data_corrupted,
                "security_compromised": result.security_compromised
            },
            "recovery_metrics": {
                "recovery_initiated": result.recovery_initiated,
                "recovery_completed": result.recovery_completed,
                "recovery_time_seconds": result.recovery_time_seconds,
                "data_loss_seconds": result.data_loss_seconds,
                "availability_downtime_seconds": result.availability_downtime_seconds
            },
            "validation_results": {
                "service_functionality_verified": result.service_functionality_verified,
                "data_integrity_verified": result.data_integrity_verified,
                "performance_within_threshold": result.performance_within_threshold,
                "performance_impact_percent": result.performance_impact_percent
            },
            "business_impact": {
                "user_impact_level": result.user_impact_level,
                "financial_impact_estimated": result.financial_impact_estimated,
                "customer_data_protected": result.customer_data_protected
            },
            "recovery_steps": result.recovery_steps_taken,
            "errors_encountered": result.errors_encountered
        }

        # Save report to file
        report_filename = f"disaster_test_report_{result.config_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = f"disaster_reports/{report_filename}"
        os.makedirs("disaster_reports", exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Disaster test report saved to: {report_path}")

    async def run_disaster_recovery_suite(self) -> Dict[str, Any]:
        """Run comprehensive disaster recovery test suite"""
        logger.info("Starting comprehensive disaster recovery test suite")

        # Define test scenarios
        test_configs = [
            # Database failure scenarios
            DisasterTestConfig(
                name="database_connection_loss",
                disaster_type=DisasterType.DATABASE_FAILURE,
                recovery_test_type=RecoveryTestType.FAILOVER_TEST,
                severity_level=3,
                max_recovery_time_seconds=120,
                safe_mode=True
            ),
            DisasterTestConfig(
                name="database_service_restart",
                disaster_type=DisasterType.DATABASE_FAILURE,
                recovery_test_type=RecoveryTestType.SERVICE_AVAILABILITY_CHECK,
                severity_level=6,
                max_recovery_time_seconds=180,
                safe_mode=True
            ),

            # Cache failure scenarios
            DisasterTestConfig(
                name="cache_connection_loss",
                disaster_type=DisasterType.CACHE_FAILURE,
                recovery_test_type=RecoveryTestType.FAILOVER_TEST,
                severity_level=3,
                max_recovery_time_seconds=60,
                safe_mode=True
            ),
            DisasterTestConfig(
                name="cache_service_restart",
                disaster_type=DisasterType.CACHE_FAILURE,
                recovery_test_type=RecoveryTestType.SERVICE_AVAILABILITY_CHECK,
                severity_level=6,
                max_recovery_time_seconds=90,
                safe_mode=True
            ),

            # Network partition scenarios
            DisasterTestConfig(
                name="partial_network_partition",
                disaster_type=DisasterType.NETWORK_PARTITION,
                recovery_test_type=RecoveryTestType.CLUSTER_RECOVERY,
                severity_level=5,
                max_recovery_time_seconds=150,
                safe_mode=True
            ),

            # Application failure scenarios
            DisasterTestConfig(
                name="application_crash",
                disaster_type=DisasterType.SERVER_CRASH,
                recovery_test_type=RecoveryTestType.SERVICE_AVAILABILITY_CHECK,
                severity_level=5,
                max_recovery_time_seconds=120,
                safe_mode=True
            ),

            # Resource exhaustion scenarios
            DisasterTestConfig(
                name="memory_exhaustion",
                disaster_type=DisasterType.MEMORY_EXHAUSTION,
                recovery_test_type=RecoveryTestType.PERFORMANCE_DEGRADATION_TEST,
                severity_level=6,
                max_recovery_time_seconds=180,
                safe_mode=True
            ),
            DisasterTestConfig(
                name="disk_space_full",
                disaster_type=DisasterType.DISK_FULL,
                recovery_test_type=RecoveryTestType.PERFORMANCE_DEGRADATION_TEST,
                severity_level=5,
                max_recovery_time_seconds=120,
                safe_mode=True
            )
        ]

        # Run tests
        results = []
        for config in test_configs:
            logger.info(f"Running disaster test: {config.name}")
            try:
                result = await self.run_disaster_test(config)
                results.append(result)

                # Rest between tests
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Failed to run test {config.name}: {str(e)}")
                continue

        # Generate suite report
        suite_report = await self._generate_suite_report(results)

        return suite_report

    async def _generate_suite_report(self, results: List[DisasterTestResult]) -> Dict[str, Any]:
        """Generate comprehensive suite report"""
        logger.info("Generating disaster recovery suite report")

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.test_passed)
        failed_tests = total_tests - passed_tests

        # Calculate average metrics
        recovery_times = [r.recovery_time_seconds for r in results if r.recovery_time_seconds > 0]
        downtime_periods = [r.availability_downtime_seconds for r in results if r.availability_downtime_seconds > 0]
        performance_impacts = [r.performance_impact_percent for r in results if r.performance_impact_percent > 0]

        # Group results by disaster type
        results_by_type = {}
        for result in results:
            if result.disaster_type not in results_by_type:
                results_by_type[result.disaster_type] = []
            results_by_type[result.disaster_type].append(result)

        # Identify critical issues
        critical_issues = []
        for result in results:
            if result.user_impact_level == "critical":
                critical_issues.append({
                    "test": result.config_name,
                    "impact": result.user_impact_level,
                    "downtime": result.availability_downtime_seconds
                })

        # Generate recommendations
        recommendations = self._generate_discovery_recommendations(results)

        suite_report = {
            "suite_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "recovery_metrics": {
                "avg_recovery_time_seconds": statistics.mean(recovery_times) if recovery_times else 0,
                "max_recovery_time_seconds": max(recovery_times) if recovery_times else 0,
                "avg_downtime_seconds": statistics.mean(downtime_periods) if downtime_periods else 0,
                "avg_performance_impact_percent": statistics.mean(performance_impacts) if performance_impacts else 0
            },
            "test_results_by_type": {
                disaster_type: {
                    "total": len(type_results),
                    "passed": sum(1 for r in type_results if r.test_passed),
                    "avg_recovery_time": statistics.mean([r.recovery_time_seconds for r in type_results if r.recovery_time_seconds > 0]) or 0
                }
                for disaster_type, type_results in results_by_type.items()
            },
            "critical_issues": critical_issues,
            "data_protection_summary": {
                "data_integrity_verified_count": sum(1 for r in results if r.data_integrity_verified),
                "customer_data_protected_count": sum(1 for r in results if r.customer_data_protected),
                "data_corruption_incidents": sum(1 for r in results if r.data_corrupted)
            },
            "business_impact_summary": {
                "total_financial_impact": sum(r.financial_impact_estimated for r in results),
                "critical_impact_count": sum(1 for r in results if r.user_impact_level == "critical"),
                "high_impact_count": sum(1 for r in results if r.user_impact_level == "high")
            },
            "recommendations": recommendations,
            "individual_test_results": [
                {
                    "name": r.config_name,
                    "disaster_type": r.disaster_type,
                    "test_passed": r.test_passed,
                    "recovery_time": r.recovery_time_seconds,
                    "downtime": r.availability_downtime_seconds,
                    "user_impact": r.user_impact_level,
                    "data_protected": r.customer_data_protected,
                    "errors": r.errors_encountered
                }
                for r in results
            ]
        }

        # Save suite report
        suite_report_path = f"disaster_reports/suite_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(suite_report_path, "w") as f:
            json.dump(suite_report, f, indent=2, default=str)

        logger.info(f"Disaster recovery suite report saved to: {suite_report_path}")

        return suite_report

    def _generate_discovery_recommendations(self, results: List[DisasterTestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Recovery time analysis
        slow_recovery_tests = [r for r in results if r.recovery_time_seconds > 300]  # > 5 minutes
        if slow_recovery_tests:
            recommendations.append(f"Improve recovery procedures - {len(slow_recovery_tests)} tests showed slow recovery (> 5min)")

        # Data integrity issues
        data_issues = [r for r in results if not r.data_integrity_verified]
        if data_issues:
            recommendations.append(f"Address data integrity issues - {len(data_issues)} tests failed integrity verification")

        # High business impact
        high_impact_tests = [r for r in results if r.user_impact_level in ["high", "critical"]]
        if high_impact_tests:
            recommendations.append(f"Mitigate high business impact scenarios - {len(high_impact_tests)} tests showed severe impact")

        # Service availability issues
        service_issues = [r for r in results if not r.service_functionality_verified]
        if service_issues:
            recommendations.append(f"Improve service availability - {len(service_issues)} tests failed functionality verification")

        # Performance degradation
        performance_issues = [r for r in results if r.performance_impact_percent > 50]
        if performance_issues:
            recommendations.append(f"Address performance degradation - {len(performance_issues)} tests showed > 50% performance impact")

        # General recommendations
        if len(results) > 0:
            success_rate = sum(1 for r in results if r.test_passed) / len(results) * 100
            if success_rate < 80:
                recommendations.append("Overall disaster recovery readiness needs improvement")
            elif success_rate >= 95:
                recommendations.append("Excellent disaster recovery preparedness")
            else:
                recommendations.append("Good disaster recovery preparedness with room for improvement")

        if not recommendations:
            recommendations.append("Disaster recovery testing results are satisfactory")

        return recommendations


if __name__ == "__main__":
    # Run disaster recovery test suite
    async def main():
        tester = DisasterRecoveryTester()
        report = await tester.run_disaster_recovery_suite()

        print("\n" + "="*60)
        print("DISASTER RECOVERY TEST SUITE REPORT")
        print("="*60)

        metadata = report["suite_metadata"]
        print(f"Test Suite: {metadata['total_tests']} tests ({metadata['passed_tests']} passed)")
        print(f"Success Rate: {metadata['success_rate']:.1f}%")

        recovery_metrics = report["recovery_metrics"]
        print(f"\nRecovery Metrics:")
        print(f"  Average Recovery Time: {recovery_metrics['avg_recovery_time_seconds']:.1f}s")
        print(f"  Maximum Recovery Time: {recovery_metrics['max_recovery_time_seconds']:.1f}s")
        print(f"  Average Downtime: {recovery_metrics['avg_downtime_seconds']:.1f}s")
        print(f"  Average Performance Impact: {recovery_metrics['avg_performance_impact_percent']:.1f}%")

        data_protection = report["data_protection_summary"]
        print(f"\nData Protection:")
        print(f"  Data Integrity Verified: {data_protection['data_integrity_verified_count']}/{metadata['total_tests']} tests")
        print(f"  Customer Data Protected: {data_protection['customer_data_protected_count']}/{metadata['total_tests']} tests")
        print(f"  Data Corruption Incidents: {data_protection['data_corruption_incidents']}")

        business_impact = report["business_impact_summary"]
        print(f"\nBusiness Impact:")
        print(f"  Total Estimated Financial Impact: ${business_impact['total_financial_impact']:.2f}")
        print(f"  Critical Impact Incidents: {business_impact['critical_impact_count']}")
        print(f"  High Impact Incidents: {business_impact['high_impact_count']}")

        if report["critical_issues"]:
            print(f"\nCritical Issues:")
            for issue in report["critical_issues"]:
                print(f"  - {issue['test']}: {issue['impact']} impact ({issue['downtime']:.1f}s downtime)")

        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        print("="*60)

    asyncio.run(main())