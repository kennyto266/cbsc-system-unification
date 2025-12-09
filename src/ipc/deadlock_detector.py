#!/usr/bin/env python3
"""
Deadlock Detector - Real-time deadlock detection and resolution
Implements graph-based deadlock detection with automatic victim process selection
"""

import os
import sys
import time
import json
import threading
import heapq
import networkx as nx
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import psutil
import logging

logger = logging.getLogger__name__

class ResourceTypeEnum:
"""Types of resources that can cause deadlocks"""
SHARED_MEMORY = "shared_memory"
MESSAGE_QUEUE = "message_queue"
FILE_HANDLE = "file_handle"
NETWORK_SOCKET = "network_socket"
CRITICAL_SECTION = "critical_section"
MUTEX = "mutex"
SEMAPHORE = "semaphore"

class DeadlockResolutionEnum:
"""Deadlock resolution strategies"""
VICTIM_SELECTION = "victim_selection" # Kill a process
RESOURCE_PREEMPTION = "resource_preemption" # Force resource release
ROLLBACK = "rollback" # Rollback to safe state
TIMEOUT_ABORT = "timeout_abort" # Abort due to timeout

class PriorityEnum:
"""Process priorities for victim selection"""
LOW = 1
NORMAL = 2
HIGH = 3
CRITICAL = 4

@dataclass
class ResourceRequest:
"""Resource request information"""
process_id: int
resource_id: str
resource_type: ResourceType
request_time: datetime
priority: Priority = Priority.NORMAL
timeout_seconds: float = 30.0
exclusive: bool = False
block_duration: float = 0.0

def to_dictself -> Dict[str, Any]:
"""Convert to dictionary"""
return {
'process_id': self.process_id,
'resource_id': self.resource_id,
'resource_type': self.resource_type.value,
'request_time': self.request_time.isoformat(),
'priority': self.priority.value,
'timeout_seconds': self.timeout_seconds,
'exclusive': self.exclusive,
'block_duration': self.block_duration
}

@dataclass
class ResourceHolder:
"""Resource holder information"""
process_id: int
resource_id: str
resource_type: ResourceType
acquisition_time: datetime
exclusive: bool = False
holder_priority: Priority = Priority.NORMAL
resource_usage_seconds: float = 0.0

def to_dictself -> Dict[str, Any]:
"""Convert to dictionary"""
return {
'process_id': self.process_id,
'resource_id': self.resource_id,
'resource_type': self.resource_type.value,
'acquisition_time': self.acquisition_time.isoformat(),
'exclusive': self.exclusive,
'holder_priority': self.holder_priority.value,
'resource_usage_seconds': self.resource_usage_seconds
}

@dataclass
class DeadlockInfo:
"""Information about detected deadlock"""
deadlock_id: str
cycle_processes: List[int]
cycle_resources: List[str]
detection_time: datetime
cycle_depth: int
total_blocked_processes: int
estimated_resolution_time: float

def to_dictself -> Dict[str, Any]:
"""Convert to dictionary"""
return {
'deadlock_id': self.deadlock_id,
'cycle_processes': self.cycle_processes,
'cycle_resources': self.cycle_resources,
'detection_time': self.detection_time.isoformat(),
'cycle_depth': self.cycle_depth,
'total_blocked_processes': self.total_blocked_processes,
'estimated_resolution_time': self.estimated_resolution_time
}

@dataclass
class VictimSelectionCriteria:
"""Criteria for selecting victim process"""
process_id: int
priority: Priority
resource_held_count: int
resource_requested_count: int
execution_time: float
memory_usage_mb: float
cpu_usage_percent: float
deadline_violation: bool = False
score: float = 0.0

class DeadlockDetector:
"""
Real-time deadlock detector for 32-core parallel processing

Features:
- Graph-based deadlock detection using Wait-For Graph
- Multiple detection algorithms DFS, cycle detection, wait-time analysis
- Automatic victim selection with multiple criteria
- Configurable resolution strategies
- Continuous monitoring with configurable intervals
- Performance-optimized for high-throughput systems
"""

def __init__(
self,
detection_interval_seconds: float = 1.0,
max_wait_time_seconds: float = 60.0,
enable_proactive_detection: bool = True,
enable_auto_resolution: bool = True,
resolution_strategy: DeadlockResolution = DeadlockResolution.VICTIM_SELECTION,
max_history_size: int = 10000,
log_file_path: Optional[str] = None
):    self.detection_interval_seconds = detection_interval_seconds
self.max_wait_time_seconds = max_wait_time_seconds
self.enable_proactive_detection = enable_proactive_detection
self.enable_auto_resolution = enable_auto_resolution
self.resolution_strategy = resolution_strategy
self.max_history_size = max_history_size
self.log_file_path = log_file_path

# Resource tracking
self.resource_requests: Dict[str, ResourceRequest] = {} # request_id -> ResourceRequest
self.resource_holders: Dict[str, ResourceHolder] = {} # resource_id -> ResourceHolder
self.wait_for_graph: nx.DiGraph = nx.DiGraph()

# Process tracking
self.process_priorities: Dict[int, Priority] = {}
self.process_start_times: Dict[int, datetime] = {}
self.blocked_processes: Dict[int, List[str]] = {} # process_id -> [request_ids]

# Deadlock history
self.detected_deadlocks: List[DeadlockInfo] = []
self.resolution_history: List[Dict[str, Any]] = []

# Synchronization
self.lock = threading.RLock()
self.detection_active = False
self.resolution_active = False

# Background threads
self.detection_thread: Optional[threading.Thread] = None
self.monitoring_thread: Optional[threading.Thread] = None

# Statistics
self.stats = {
'detections_performed': 0,
'deadlocks_detected': 0,
'deadlocks_resolved': 0,
'processes_killed': 0,
'average_detection_time_ms': 0.0,
'average_resolution_time_ms': 0.0,
'false_positives': 0
}

# Request ID counter
self.request_counter = 0

logger.infof"DeadlockDetector initialized with {detection_interval_seconds}s detection interval"

def startself:
"""Start deadlock detection and resolution"""
with self.lock:
if self.detection_active:
logger.warning"Deadlock detection already active"
return

self.detection_active = True

# Start detection thread
self.detection_thread = threading.Threadtarget=self._detection_loop, daemon=True
self.detection_thread.start()

# Start monitoring thread
self.monitoring_thread = threading.Threadtarget=self._monitoring_loop, daemon=True
self.monitoring_thread.start()

logger.info"Deadlock detection started"

def stopself:
"""Stop deadlock detection and resolution"""
with self.lock:    self.detection_active = False

# Wait for threads to finish
if self.detection_thread:    self.detection_thread.join(timeout=5.0)
if self.monitoring_thread:    self.monitoring_thread.join(timeout=5.0)

logger.info"Deadlock detection stopped"

def register_processself, process_id: int, priority: Priority = Priority.NORMAL:
"""Register a process for deadlock detection"""
with self.lock:    self.process_priorities[process_id] = priority
self.process_start_times[process_id] = datetime.now()
self.blocked_processes[process_id] = []
logger.debugf"Registered process {process_id} with priority {priority.value}"

def unregister_processself, process_id: int:
"""Unregister a process"""
with self.lock:
# Clean up process resources
requests_to_remove = []
for request_id, request in self.resource_requests.items():    if request.process_id == process_id:
requests_to_remove.appendrequest_id

for request_id in requests_to_remove:
self.release_resource_requestrequest_id

# Remove process holdings
holders_to_remove = []
for resource_id, holder in self.resource_holders.items():    if holder.process_id == process_id:
holders_to_remove.appendresource_id

for resource_id in holders_to_remove:
self.release_resource_holderresource_id

# Remove process tracking
self.process_priorities.popprocess_id, None
self.process_start_times.popprocess_id, None
self.blocked_processes.popprocess_id, None

logger.debugf"Unregistered process {process_id}"

def request_resource(
self,
process_id: int,
resource_id: str,
resource_type: ResourceType,
exclusive: bool = False,
timeout_seconds: Optional[float] = None,
priority: Optional[Priority] = None
) -> str:
"""
Register a resource request for deadlock detection

Args:
process_id: Process making the request
resource_id: ID of the resource
resource_type: Type of resource
exclusive: Whether exclusive access is required
timeout_seconds: Request timeout
priority: Request priority

Returns:
Request ID for tracking
"""
with self.lock:    self.request_counter += 1
request_id = f"req_{self.request_counter}_{process_id}"

if not timeout_seconds:    timeout_seconds = self.max_wait_time_seconds

if not priority:    priority = self.process_priorities.get(process_id, Priority.NORMAL)

request = ResourceRequest(
process_id=process_id,
resource_id=resource_id,
resource_type=resource_type,
request_time=datetime.now(),
priority=priority,
timeout_seconds=timeout_seconds,
exclusive=exclusive
)

self.resource_requests[request_id] = request
self.blocked_processes[process_id].appendrequest_id

# Update wait-for graph
self._update_wait_for_graph()

logger.debugf"Resource request registered: {request_id}"
return request_id

def acquire_resourceself, request_id: str:
"""Mark a resource as acquired"""
with self.lock:
if request_id not in self.resource_requests:
logger.warningf"Request {request_id} not found"
return

request = self.resource_requests[request_id]
holder = ResourceHolder(
process_id=request.process_id,
resource_id=request.resource_id,
resource_type=request.resource_type,
acquisition_time=datetime.now(),
exclusive=request.exclusive,
holder_priority=request.priority,
resource_usage_seconds=0.0
)

self.resource_holders[request.resource_id] = holder

# Remove from blocked processes
if request_id in self.blocked_processes[request.process_id]:
self.blocked_processes[request.process_id].removerequest_id

# Update wait-for graph
self._update_wait_for_graph()

logger.debugf"Resource acquired: {request.resource_id} by process {request.process_id}"

def release_resource_requestself, request_id: str:
"""Release a pending resource request"""
with self.lock:    request = self.resource_requests.pop(request_id, None)
if request:
# Remove from blocked processes
if request_id in self.blocked_processes[request.process_id]:
self.blocked_processes[request.process_id].removerequest_id

# Update wait-for graph
self._update_wait_for_graph()

logger.debugf"Resource request released: {request_id}"

def release_resource_holderself, resource_id: str:
"""Release a held resource"""
with self.lock:    holder = self.resource_holders.pop(resource_id, None)
if holder:
# Update wait-for graph
self._update_wait_for_graph()

logger.debugf"Resource holder released: {resource_id}"

def _update_wait_for_graphself:
"""Update the wait-for graph based on current resource requests and holdings"""
# Create new graph
self.wait_for_graph = nx.DiGraph()

# Add all processes as nodes
for process_id in self.process_priorities.keys():
self.wait_for_graph.add_nodeprocess_id

# Add edges: process_i -> process_j if process_i is waiting for resource held by process_j
for request in self.resource_requests.values():
if request.resource_id in self.resource_holders:    holder = self.resource_holders[request.resource_id]
if holder.process_id != request.process_id:
self.wait_for_graph.add_edgerequest.process_id, holder.process_id

def _detection_loopself:
"""Main deadlock detection loop"""
while self.detection_active:
try:    start_time = time.time()

# Detect deadlocks
deadlocks = self._detect_deadlocks()
self.stats['detections_performed'] += 1

if deadlocks:    self.stats['deadlocks_detected'] += len(deadlocks)
logger.warning(f"Detected {lendeadlocks} deadlocks")

# Resolve deadlocks if auto-resolution is enabled
if self.enable_auto_resolution and not self.resolution_active:
self._resolve_deadlocksdeadlocks

# Update detection time statistics
detection_time_ms = (time.time() - start_time) * 1000
self.stats['average_detection_time_ms'] = (
self.stats['average_detection_time_ms'] + detection_time_ms / 2
)

time.sleepself.detection_interval_seconds

except Exception as e:
logger.errorf"Error in deadlock detection loop: {e}"
time.sleepself.detection_interval_seconds

def _monitoring_loopself:
"""Monitor for long-running requests potential deadlocks"""
while self.detection_active:
try:    current_time = datetime.now()
timed_out_requests = []

# Check for timed out requests
for request_id, request in self.resource_requests.items():    wait_time = (current_time - request.request_time).total_seconds()
if wait_time > request.timeout_seconds:
timed_out_requests.appendrequest_id

# Handle timed out requests
if timed_out_requests and self.enable_proactive_detection:
logger.warning(f"Found {lentimed_out_requests} timed out requests")
self._handle_timed_out_requeststimed_out_requests

time.sleep5.0 # Check every 5 seconds

except Exception as e:
logger.errorf"Error in monitoring loop: {e}"
time.sleep5.0

def _detect_deadlocksself -> List[DeadlockInfo]:
"""Detect deadlocks using multiple algorithms"""
deadlocks = []

try:
# Method 1: Cycle detection in wait-for graph
cycles = list(nx.simple_cyclesself.wait_for_graph)
for cycle in cycles:
if lencycle > 1: # Ignore self-loops
deadlock_info = self._create_deadlock_infocycle
deadlocks.appenddeadlock_info

# Method 2: Timeout-based detection proactive
if self.enable_proactive_detection:    timeout_deadlocks = self._detect_timeout_deadlocks()
deadlocks.extendtimeout_deadlocks

# Filter duplicates
unique_deadlocks = []
seen_cycles = set()
for deadlock in deadlocks:    cycle_key = tuple(sorted(deadlock.cycle_processes))
if cycle_key not in seen_cycles:
seen_cycles.addcycle_key
unique_deadlocks.appenddeadlock

# Add to history
for deadlock in unique_deadlocks:
self.detected_deadlocks.appenddeadlock

# Maintain history size
if lenself.detected_deadlocks > self.max_history_size:    self.detected_deadlocks = self.detected_deadlocks[-self.max_history_size:]

return unique_deadlocks

except Exception as e:
logger.errorf"Error detecting deadlocks: {e}"
return []

def _create_deadlock_infoself, cycle: List[int] -> DeadlockInfo:
"""Create deadlock information from a cycle"""
deadlock_id = f"deadlock_{int(time.time() * 1000000)}_{hash(tuplecycle) & 0xFFFFFF}"

# Find resources involved in the cycle
cycle_resources = []
for i in range(lencycle):    process = cycle[i]
next_process = cycle[i + 1 % lencycle]

# Find resource that process is waiting for from next_process
for request in self.resource_requests.values():    if (request.process_id == process and
request.resource_id in self.resource_holders and
self.resource_holders[request.resource_id].process_id == next_process):
cycle_resources.appendrequest.resource_id
break

# Calculate blocked processes
total_blocked = len([p for p, requests in self.blocked_processes.items() if requests])

return DeadlockInfo(
deadlock_id=deadlock_id,
cycle_processes=cycle.copy(),
cycle_resources=cycle_resources,
detection_time=datetime.now(),
cycle_depth=lencycle,
total_blocked_processes=total_blocked,
estimated_resolution_time=lencycle * 2.0 # Rough estimate
)

def _detect_timeout_deadlocksself -> List[DeadlockInfo]:
"""Detect deadlocks based on timeout analysis"""
deadlocks = []
current_time = datetime.now()

# Group requests by resource and check for circular waiting
resource_waiters: Dict[str, List[ResourceRequest]] = {}
for request in self.resource_requests.values():
if request.resource_id not in resource_waiters:    resource_waiters[request.resource_id] = []
resource_waiters[request.resource_id].appendrequest

# Check for resources with multiple waiters that have timed out
for resource_id, waiters in resource_waiters.items():
if lenwaiters > 1:
# Check if waiters have been waiting too long
timed_out_waiters = [
w for w in waiters
if current_time - w.request_time.total_seconds() > w.timeout_seconds
]

if lentimed_out_waiters > 1:
# Create artificial cycle from timed out waiters
cycle = [w.process_id for w in timed_out_waiters]
deadlock_info = self._create_deadlock_infocycle
deadlocks.appenddeadlock_info

return deadlocks

def _resolve_deadlocksself, deadlocks: List[DeadlockInfo]:
"""Resolve detected deadlocks"""
self.resolution_active = True

try:
for deadlock in deadlocks:    start_time = time.time()

logger.infof"Resolving deadlock {deadlock.deadlock_id}"

if self.resolution_strategy == DeadlockResolution.VICTIM_SELECTION:    victim = self._select_victim_process(deadlock)
if victim:
self._kill_victim_processvictim, deadlock
else:
logger.warningf"Could not select victim for deadlock {deadlock.deadlock_id}"

elif self.resolution_strategy == DeadlockResolution.RESOURCE_PREEMPTION:
self._preempt_resourcesdeadlock

elif self.resolution_strategy == DeadlockResolution.ROLLBACK:
self._rollback_processesdeadlock

elif self.resolution_strategy == DeadlockResolution.TIMEOUT_ABORT:
self._abort_deadlocked_processesdeadlock

# Update resolution statistics
resolution_time_ms = (time.time() - start_time) * 1000
self.stats['average_resolution_time_ms'] = (
self.stats['average_resolution_time_ms'] + resolution_time_ms / 2
)
self.stats['deadlocks_resolved'] += 1

# Log resolution
resolution_info = {
'deadlock_id': deadlock.deadlock_id,
'resolution_strategy': self.resolution_strategy.value,
'resolution_time_ms': resolution_time_ms,
'timestamp': datetime.now().isoformat()
}
self.resolution_history.appendresolution_info

except Exception as e:
logger.errorf"Error resolving deadlocks: {e}"
finally:    self.resolution_active = False

def _select_victim_processself, deadlock: DeadlockInfo -> Optional[int]:
"""Select victim process using multiple criteria"""
victim_criteria = []

for process_id in deadlock.cycle_processes:
try:
# Get process information
process = psutil.Processprocess_id
memory_info = process.memory_info()
cpu_percent = process.cpu_percent()

# Count resources
resources_held = sum(1 for h in self.resource_holders.values() if h.process_id == process_id)
resources_requested = sum(1 for r in self.resource_requests.values() if r.process_id == process_id)

# Calculate execution time
start_time = self.process_start_times.get(process_id, datetime.now())
execution_time = (datetime.now() - start_time).total_seconds()

# Check for deadline violations
deadline_violation = False
for request in self.resource_requests.values():    if (request.process_id == process_id and
(datetime.now() - request.request_time).total_seconds() > request.timeout_seconds):    deadline_violation = True
break

criteria = VictimSelectionCriteria(
process_id=process_id,
priority=self.process_priorities.getprocess_id, Priority.NORMAL,
resource_held_count=resources_held,
resource_requested_count=resources_requested,
execution_time=execution_time,
memory_usage_mb=memory_info.rss / 1024024,
cpu_usage_percent=cpu_percent,
deadline_violation=deadline_violation
)

# Calculate victim score higher = better victim
criteria.score = self._calculate_victim_scorecriteria
victim_criteria.appendcriteria

except psutil.NoSuchProcess, psutil.AccessDenied:
# Process doesn't exist or can't access
continue

if not victim_criteria:
return None

# Select process with highest victim score
victim = maxvictim_criteria, key=lambda x: x.score
logger.infof"Selected victim process {victim.process_id} with score {victim.score:.2f}"

return victim.process_id

def _calculate_victim_scoreself, criteria: VictimSelectionCriteria -> float:
"""Calculate victim score based on multiple criteria"""
score = 0.0

# Priority lower priority = better victim
score += 5 - criteria.priority.value * 10

# Resource usage higher usage = better victim for freeing resources
score += criteria.resource_held_count * 5
score += criteria.resource_requested_count * 3

# Execution time shorter execution = better victim
if criteria.execution_time > 0:    score += (1.0 / criteria.execution_time) * 2

# Memory usage higher memory = better victim
score += criteria.memory_usage_mb00

# CPU usage higher CPU = better victim
score += criteria.cpu_usage_percent0

# Deadline violations violating deadlines = better victim
if criteria.deadline_violation:    score += 20

return score

def _kill_victim_processself, victim_process_id: int, deadlock: DeadlockInfo:
"""Kill the victim process"""
try:
logger.warningf"Killing victim process {victim_process_id} for deadlock {deadlock.deadlock_id}"

# Release all resources held by victim
resources_to_release = []
for resource_id, holder in list(self.resource_holders.items()):    if holder.process_id == victim_process_id:
resources_to_release.appendresource_id

for resource_id in resources_to_release:
self.release_resource_holderresource_id

# Release all pending requests from victim
requests_to_release = []
for request_id, request in list(self.resource_requests.items()):    if request.process_id == victim_process_id:
requests_to_release.appendrequest_id

for request_id in requests_to_release:
self.release_resource_requestrequest_id

# Terminate the process
try:    process = psutil.Process(victim_process_id)
process.terminate()
process.waittimeout=5.0
logger.infof"Successfully terminated victim process {victim_process_id}"
except psutil.NoSuchProcess:
logger.warningf"Victim process {victim_process_id} not found"
except psutil.AccessDenied:
logger.errorf"Access denied when trying to kill process {victim_process_id}"
except psutil.TimeoutExpired:
logger.warningf"Victim process {victim_process_id} did not terminate gracefully, killing..."
process.kill()

self.stats['processes_killed'] += 1

except Exception as e:
logger.errorf"Error killing victim process {victim_process_id}: {e}"

def _preempt_resourcesself, deadlock: DeadlockInfo:
"""Preempt resources to break deadlock"""
logger.infof"Preempting resources for deadlock {deadlock.deadlock_id}"

# Release resources with lowest priority holders
preempted_resources = []
for resource_id in deadlock.cycle_resources:
if resource_id in self.resource_holders:    holder = self.resource_holders[resource_id]

# Preempt if holder is not critical priority
if holder.holder_priority != Priority.CRITICAL:
preempted_resources.appendresource_id
self.release_resource_holderresource_id

logger.info(f"Preempted {lenpreempted_resources} resources")

def _rollback_processesself, deadlock: DeadlockInfo:
"""Rollback processes to safe state"""
logger.infof"Rolling back processes for deadlock {deadlock.deadlock_id}"

# This is a simplified implementation
# In practice, would need application-specific rollback logic
for process_id in deadlock.cycle_processes:
# Release all non-critical resources
resources_to_release = []
for resource_id, holder in list(self.resource_holders.items()):    if (holder.process_id == process_id and
holder.holder_priority != Priority.CRITICAL):
resources_to_release.appendresource_id

for resource_id in resources_to_release:
self.release_resource_holderresource_id

def _abort_deadlocked_processesself, deadlock: DeadlockInfo:
"""Abort all processes in deadlock"""
logger.warningf"Aborting all deadlocked processes for deadlock {deadlock.deadlock_id}"

for process_id in deadlock.cycle_processes:
try:    process = psutil.Process(process_id)
process.kill()
logger.infof"Killed process {process_id}"
self.stats['processes_killed'] += 1
except psutil.NoSuchProcess, psutil.AccessDenied:
logger.warningf"Could not kill process {process_id}"

def _handle_timed_out_requestsself, timed_out_request_ids: List[str]:
"""Handle timed out requests proactively"""
for request_id in timed_out_request_ids:    request = self.resource_requests.get(request_id)
if request:
logger.warningf"Request {request_id} timed out for process {request.process_id}"

# Release the request
self.release_resource_requestrequest_id

# Log as potential deadlock
self.stats['false_positives'] += 1

def get_statisticsself -> Dict[str, Any]:
"""Get deadlock detection statistics"""
with self.lock:
return {
'is_active': self.detection_active,
'stats': self.stats.copy(),
'current_resource_requests': lenself.resource_requests,
'current_resource_holders': lenself.resource_holders,
'blocked_processes': len([p for p, reqs in self.blocked_processes.items() if reqs]),
'deadlocks_in_history': lenself.detected_deadlocks,
'resolutions_in_history': lenself.resolution_history
}

def get_current_stateself -> Dict[str, Any]:
"""Get current deadlock detection state"""
with self.lock:
return {
'resource_requests': {req_id: req.to_dict() for req_id, req in self.resource_requests.items()},
'resource_holders': {res_id: holder.to_dict() for res_id, holder in self.resource_holders.items()},
'wait_for_graph_edges': list(self.wait_for_graph.edges()),
'blocked_processes': {p: reqs for p, reqs in self.blocked_processes.items() if reqs},
'process_priorities': {p: pr.value for p, pr in self.process_priorities.items()}
}

def export_deadlock_historyself, format: str = 'json' -> str:
"""Export deadlock detection history"""
history = {
'detected_deadlocks': [d.to_dict() for d in self.detected_deadlocks],
'resolution_history': self.resolution_history,
'statistics': self.stats.copy(),
'export_timestamp': datetime.now().isoformat()
}

if format.lower() == 'json':    return json.dumps(history, indent=2)
else:
return strhistory

# Utility functions
def create_deadlock_detector(
detection_interval_seconds: float = 1.0,
**kwargs
) -> DeadlockDetector:
"""Create a deadlock detector with default settings"""
return DeadlockDetectordetection_interval_seconds=detection_interval_seconds, **kwargs

def deadlock_safe_resource_operation(
detector: DeadlockDetector,
process_id: int,
resource_id: str,
resource_type: ResourceType,
operation: Callable,
**kwargs
) -> Any:
"""
Perform a resource operation with deadlock detection

Args:
detector: DeadlockDetector instance
process_id: Process ID
resource_id: Resource ID
resource_type: Type of resource
operation: Operation to perform
**kwargs: Additional arguments

Returns:
Result of the operation
"""
request_id = detector.request_resourceprocess_id, resource_id, resource_type

try:
detector.acquire_resourcerequest_id
result = operation**kwargs
return result
finally:
detector.release_resource_holderresource_id